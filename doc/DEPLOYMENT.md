# Deployment Guide

This guide provides a step-by-step process for deploying the Plant Shop application to a production environment. The target environment is a **Linux server (e.g., Ubuntu 22.04)** using Nginx, Gunicorn, Daphne, PostgreSQL, and Redis.

## Prerequisites

*   A Linux server (e.g., a VPS from DigitalOcean, Linode, or an AWS EC2 instance).
*   A domain name configured to point to your server's public IP address.
*   Root or `sudo` access to the server.

---

## Step 1: Server Preparation

1.  **Update System Packages:**
    Ensure your server's package list and installed packages are up to date.
    ```bash
    sudo apt update && sudo apt upgrade -y
    ```

2.  **Install Core Dependencies:**
    Install Python, package management tools, Nginx (our web server), PostgreSQL (our database), and Redis (for caching and WebSockets).
    ```bash
    sudo apt install python3-pip python3-dev python3-venv libpq-dev postgresql postgresql-contrib nginx redis-server -y
    ```

3.  **Create and Configure the Database:**
    Log in to PostgreSQL to create a dedicated database and user for the application.
    ```bash
    sudo -u postgres psql
    ```
    Inside the PostgreSQL prompt, execute the following commands. **Replace `a_very_secure_password` with a strong, unique password.**
    ```sql
    CREATE DATABASE plant_shop_db;
    CREATE USER plant_shop_user WITH PASSWORD 'a_very_secure_password';
    ALTER ROLE plant_shop_user SET client_encoding TO 'utf8';
    ALTER ROLE plant_shop_user SET default_transaction_isolation TO 'read committed';
    ALTER ROLE plant_shop_user SET timezone TO 'UTC';
    GRANT ALL PRIVILEGES ON DATABASE plant_shop_db TO plant_shop_user;
    \q
    ```

---

## Step 2: Application Setup

1.  **Clone the Application Code:**
    Clone the repository into a suitable directory, such as `/var/www/`.
    ```bash
    sudo git clone https://github.com/init050/plant-shop.git /var/www/plant-shop
    cd /var/www/plant-shop
    ```

2.  **Create a Python Virtual Environment:**
    Isolate the project's Python dependencies from the system's Python packages.
    ```bash
    sudo python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install Dependencies:**
    Uncomment `gunicorn` in `requirements.txt` if it is commented out, then install all packages.
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables for Production:**
    Copy the example `.env` file and edit it with your production settings.
    ```bash
    cp .env.example .env
    nano .env
    ```
    **Crucially, update the following:**
    *   Set `DEBUG=False`.
    *   Set `SECRET_KEY` to a new, randomly generated, long string.
    *   Fill in the `DB_` variables with the credentials you created in Step 1.
    *   Fill in the `REDIS_HOST` and `REDIS_PORT` (e.g., `localhost` and `6379`).

5.  **Configure Channel Layers for Production:**
    In `Plant_Shop/settings.py`, you **must** change the `CHANNEL_LAYERS` setting to use Redis. The default `InMemoryChannelLayer` is not suitable for a multi-process production environment.

    ```python
    # In Plant_Shop/settings.py, find and update CHANNEL_LAYERS:
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {
                "hosts": [(config('REDIS_HOST', '127.0.0.1'), config('REDIS_PORT', 6379, cast=int))],
            },
        },
    }
    ```

6.  **Prepare Django for Production:**
    Run these commands to prepare the database and static files.
    ```bash
    python manage.py migrate
    python manage.py collectstatic
    ```

---

## Step 3: Configure Gunicorn & Daphne with `systemd`

We will use `systemd` to manage our application servers, ensuring they run as background services and restart on failure.

1.  **Create a Gunicorn `systemd` Service File:**
    This service will handle standard HTTP requests.
    ```bash
    sudo nano /etc/systemd/system/gunicorn.service
    ```
    Paste the following, replacing `your_user` with the Linux user that will run the process (e.g., `root` or a dedicated user).
    ```ini
    [Unit]
    Description=gunicorn daemon for Plant Shop
    After=network.target

    [Service]
    User=your_user
    Group=www-data
    WorkingDirectory=/var/www/plant-shop
    ExecStart=/var/www/plant-shop/.venv/bin/gunicorn --access-logfile - --workers 3 --bind unix:/var/www/plant-shop/plant_shop.sock Plant_Shop.wsgi:application

    [Install]
    WantedBy=multi-user.target
    ```

2.  **Create a Daphne `systemd` Service File:**
    This service will handle WebSocket connections.
    ```bash
    sudo nano /etc/systemd/system/daphne.service
    ```
    Paste the following, replacing `your_user`:
    ```ini
    [Unit]
    Description=daphne daemon for Plant Shop WebSockets
    After=network.target

    [Service]
    User=your_user
    Group=www-data
    WorkingDirectory=/var/www/plant-shop
    ExecStart=/var/www/plant-shop/.venv/bin/daphne -u /var/www/plant-shop/daphne.sock Plant_Shop.asgi:application

    [Install]
    WantedBy=multi-user.target
    ```

3.  **Start and Enable the Services:**
    ```bash
    sudo systemctl start gunicorn
    sudo systemctl enable gunicorn
    sudo systemctl start daphne
    sudo systemctl enable daphne
    ```

---

## Step 4: Configure Nginx as a Reverse Proxy

Nginx will sit in front of our application servers, routing traffic appropriately.

1.  **Create an Nginx Site Configuration:**
    ```bash
    sudo nano /etc/nginx/sites-available/plant_shop
    ```

2.  **Paste the following configuration**, replacing `your_domain.com` with your actual domain.
    ```nginx
    server {
        listen 80;
        server_name your_domain.com www.your_domain.com;

        location = /favicon.ico { access_log off; log_not_found off; }

        # Serve static and media files directly
        location /static/ {
            root /var/www/plant-shop;
        }
        location /media/ {
            root /var/www/plant-shop;
        }

        # Proxy standard HTTP requests to Gunicorn
        location / {
            include proxy_params;
            proxy_pass http://unix:/var/www/plant-shop/plant_shop.sock;
        }

        # Proxy WebSocket requests to Daphne
        location /ws/ {
            proxy_pass http://unix:/var/www/plant-shop/daphne.sock;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_redirect off;
        }
    }
    ```

3.  **Enable the Site and Restart Nginx:**
    ```bash
    sudo ln -s /etc/nginx/sites-available/plant_shop /etc/nginx/sites-enabled
    sudo nginx -t  # Test configuration for errors
    sudo systemctl restart nginx
    ```

4.  **Set Up HTTPS with Certbot (Recommended):**
    ```bash
    sudo apt install certbot python3-certbot-nginx -y
    sudo certbot --nginx -d your_domain.com -d www.your_domain.com
    ```
    Follow the prompts. Certbot will automatically acquire an SSL certificate and update your Nginx configuration to use it.

Your application should now be live and accessible at your domain.
