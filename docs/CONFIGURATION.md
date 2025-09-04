# Configuration Guide

This document explains all the environment variables used to configure the Plant Shop application. All configuration is managed via a `.env` file in the root of the project directory.

To get started, copy the example file:
```bash
cp .env.example .env
```
Then, edit the new `.env` file with your local settings.

---

## Core Application Variables

These variables are essential for the basic operation of the application.

*   #### `SECRET_KEY`
    *   **Description:** A secret, unique key for your Django installation. It is used for cryptographic signing (e.g., sessions, password reset tokens) and must be kept confidential.
    *   **Example:** `pb_a_random_string_of_at_least_50_characters_go_here`
    *   **Required:** **Yes**

*   #### `DEBUG`
    *   **Description:** A boolean (`True` or `False`) that toggles Django's debug mode. When `True`, detailed error pages are shown, and static files are served differently.
    *   **Default:** `False`
    *   **Production Value:** Must be `False`.
    *   **Development Value:** `True`
    *   **Required:** **Yes**

---

## Database Variables (PostgreSQL)

These variables configure the connection to the PostgreSQL database, which is the primary data store for the application.

*   #### `DB_NAME`
    *   **Description:** The name of the database to use.
    *   **Example:** `plant_shop_db`
    *   **Required:** **Yes**

*   #### `DB_USER`
    *   **Description:** The username for connecting to the database.
    *   **Example:** `plant_shop_user`
    *   **Required:** **Yes**

*   #### `DB_PASSWORD`
    *   **Description:** The password for the specified database user.
    *   **Example:** `a_very_secure_password`
    *   **Required:** **Yes**

*   #### `DB_HOST`
    *   **Description:** The hostname or IP address of the database server.
    *   **Example:** `localhost` (for a local server) or a cloud provider's hostname.
    *   **Required:** **Yes**

*   #### `DB_PORT`
    *   **Description:** The port the database server is listening on.
    *   **Example:** `5432` (the default for PostgreSQL).
    *   **Required:** **Yes**

---

## Redis Variables

These are required for caching and real-time features (Django Channels) in a production environment. For local development, the application can fall back to using an in-memory store for Channels, but Redis is highly recommended.

*   #### `REDIS_HOST`
    *   **Description:** The hostname or IP address of the Redis server.
    *   **Example:** `localhost`
    *   **Required:** For production.

*   #### `REDIS_PORT`
    *   **Description:** The port the Redis server is listening on.
    *   **Example:** `6379` (the default for Redis).
    *   **Required:** For production.

---

## Email Variables (Optional)

These variables configure an external SMTP service for sending emails, which is necessary for features like password resets in a production environment. By default, the development environment is configured to print emails to the console.

*   #### `EMAIL_BACKEND`
    *   **Description:** The backend to use for sending emails.
    *   **Example:** `django.core.mail.backends.smtp.EmailBackend`

*   #### `EMAIL_HOST`
    *   **Description:** The SMTP server hostname.
    *   **Example:** `smtp.sendgrid.net` or `smtp.mailtrap.io`

*   #### `EMAIL_PORT`
    *   **Description:** The port for the SMTP server.
    *   **Example:** `587`

*   #### `EMAIL_HOST_USER`
    *   **Description:** The username for authenticating with the SMTP server.

*   #### `EMAIL_HOST_PASSWORD`
    *   **Description:** The password or API key for the SMTP server.

*   #### `EMAIL_USE_TLS`
    *   **Description:** Whether to use a Transport Layer Security (TLS) secure connection.
    *   **Example:** `True`
