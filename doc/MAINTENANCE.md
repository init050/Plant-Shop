# Maintenance Guide

This document outlines the routine maintenance tasks required to keep the Plant Shop application healthy, performant, and secure in a production environment.

---

## 1. Backups

**Regular backups are the most critical maintenance task.** A catastrophic failure without backups can lead to irreversible data loss.

### Database Backups
The PostgreSQL database contains all critical application data and must be backed up daily.

*   **Command:** Use the `pg_dump` utility to create a compressed SQL dump.
    ```bash
    pg_dump -U your_db_user -h localhost your_db_name | gzip > backup_$(date +%Y-%m-%d).sql.gz
    ```
*   **Automation:** This command should be automated using a `cron` job that runs during off-peak hours (e.g., 2:00 AM).
    ```cron
    # Example cron job entry in /etc/cron.d/plant_shop_backup
    0 2 * * * your_server_user /path/to/your/backup_script.sh
    ```
*   **Storage:** Backups must be stored securely and redundantly. Best practice is to copy them to an off-site location, such as a cloud storage service (e.g., AWS S3, Backblaze B2, or another VPS).

### Media File Backups
User-uploaded files (stored in the `/uploads/` directory) must also be backed up.

*   **Strategy:** Use a tool like `rsync` to efficiently copy the directory to a backup location.
    ```bash
    rsync -a /var/www/plant-shop/uploads/ /path/to/backup/location/
    ```
*   **Automation:** This should also be run as a daily `cron` job.

---

## 2. Log Management

Server and application logs can consume significant disk space over time. Use `logrotate` to manage them automatically.

*   **Nginx & System Logs:** These are typically managed by `logrotate` by default. You can review the configurations in `/etc/logrotate.d/`.
*   **Application Logs:** If you configure Gunicorn, Daphne, or Django to log to files, you must create a `logrotate` configuration for them.

**Example `logrotate` config for application logs:**
```
# /etc/logrotate.d/plant_shop
/var/www/plant-shop/logs/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 your_server_user www-data
    sharedscripts
    postrotate
        # If a service needs to be reloaded after log rotation, add the command here.
        # e.g., systemctl reload gunicorn
    endscript
}
```

---

## 3. Clearing Stale Data

Periodically cleaning up old data can free up space and improve performance.

### Clearing Expired Sessions
Django's session store can accumulate expired session data. Run this command periodically to clean it.

*   **Command:**
    ```bash
    # Activate virtual environment first
    python manage.py clearsessions
    ```
*   **Automation:** This is safe to run as a weekly `cron` job.

### Pruning Orphaned Files
*   **`django-cleanup`:** The project includes this library, which is configured to automatically delete media files from storage when the corresponding model instance is deleted. This prevents orphaned files from accumulating, so no manual cleanup is required for this task.

---

## 4. Software & Security Updates

Keeping all software components up to date is crucial for security.

### Operating System Packages
Regularly apply updates to your server's OS packages.
```bash
sudo apt update && sudo apt full-upgrade -y
```

### Python Dependencies
Periodically review and update the Python packages defined in `requirements.txt`.

1.  Activate the virtual environment.
2.  Run `pip list --outdated` to see which packages have new versions.
3.  Update packages carefully, especially major versions. **Always run the full test suite after updating a dependency** to ensure there are no breaking changes.
    ```bash
    pip install --upgrade django
    pytest
    ```

---

## 5. Application Monitoring

Proactive monitoring helps you detect issues before they affect users.

*   **Service Health:** Regularly check the status of the core application services.
    ```bash
    sudo systemctl status gunicorn
    sudo systemctl status daphne
    sudo systemctl status nginx
    sudo systemctl status postgresql
    sudo systemctl status redis-server
    ```
*   **Resource Usage:** Monitor server resources like CPU, memory, and disk space. Use tools like `htop`, `df -h`, and `free -m`. Set up alerts if usage exceeds certain thresholds.
*   **Error Tracking:** For a production application, it is highly recommended to integrate a dedicated error monitoring service like **Sentry**. Sentry can be added to the project via `sentry-sdk` and will automatically capture and report application errors in real-time, providing valuable debugging information.
