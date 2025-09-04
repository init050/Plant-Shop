# Security Guide

This document outlines the security practices, configurations, and considerations for the Plant Shop application. Maintaining a secure application is a critical and ongoing process. All developers are encouraged to follow these guidelines.

## Core Security Principles

*   **Defense in Depth:** The application employs multiple layers of security controls, from the web server configuration down to the application logic.
*   **Principle of Least Privilege:** Users and processes are only granted the permissions necessary to perform their intended functions.
*   **Secure Defaults:** The framework and application are configured to be secure by default. `DEBUG` mode **must never** be enabled in a production environment.

---

## Implemented Security Measures

This project leverages Django's robust built-in security features and several third-party libraries (included in `requirements.txt`) to mitigate common web application vulnerabilities.

### 1. Cross-Site Scripting (XSS) Prevention
*   **Django Templates:** Django's template engine automatically escapes variables by default, which is the primary defense against XSS. This prevents the injection of malicious scripts into the rendered HTML.
*   **Content Sanitization:** For cases where rich text is allowed (e.g., in article content), the application uses the **`bleach`** library to sanitize the HTML, stripping out any dangerous tags or attributes while allowing a safe subset of formatting.

### 2. Cross-Site Request Forgery (CSRF) Protection
*   **CSRF Middleware:** Django's `CsrfViewMiddleware` is enabled globally. It requires a unique CSRF token for all state-changing requests (`POST`, `PUT`, `DELETE`), ensuring that requests can only be initiated from our application's forms.

### 3. SQL Injection Prevention
*   **Django ORM:** The application uses Django's Object-Relational Mapper (ORM) for all database interactions. The ORM uses parameterized queries, which safely separates query logic from user-provided data, making the application inherently safe from SQL injection vulnerabilities. Direct SQL queries are avoided.

### 4. Password Security
*   **Strong Hashing:** User passwords are never stored in plaintext. Django uses a strong, salted, and iterated hashing algorithm (PBKDF2 by default) to securely store password hashes.
*   **Password Validators:** The `AUTH_PASSWORD_VALIDATORS` setting in `settings.py` is configured to enforce minimum password strength requirements (e.g., length, complexity), making weak passwords harder to use.

### 5. Session Security
*   **`django-session-security`:** This library is included to enhance session management. It helps prevent session hijacking by expiring sessions after a period of inactivity and can be configured to log users out if their IP address or user agent changes unexpectedly.
*   **Secure Cookies:** In a production environment where HTTPS is enabled, session cookies must be configured with the `SESSION_COOKIE_SECURE=True` and `CSRF_COOKIE_SECURE=True` flags in `settings.py`. This ensures that cookies are only transmitted over an encrypted connection.

### 6. Brute-Force Attack Prevention
*   **`django-ratelimit`:** This library is used to prevent brute-force attacks against sensitive endpoints, particularly the login and password reset forms. It is configured to limit the number of attempts a user or IP address can make in a given time window.

### 7. Security Headers
*   **`django-cors-headers`:** This library is used to manage Cross-Origin Resource Sharing (CORS) headers, defining which external domains are allowed to make requests to the API.
*   **`django-csp`:** This library helps implement a Content Security Policy (CSP), a critical browser-level security feature that helps prevent XSS and data injection attacks by defining which sources of content (scripts, styles, images) are trusted.

---

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly. **Do not create a public GitHub issue.** Instead, please contact the project maintainer directly via email to ensure the vulnerability is not disclosed publicly before a fix is available.
