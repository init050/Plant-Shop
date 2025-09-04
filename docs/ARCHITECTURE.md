# Solution Architecture: Plant Shop

This document provides a comprehensive overview of the technical architecture for the Plant Shop application. It is intended for developers, architects, and technical managers.

## 1. High-Level Architecture

The Plant Shop is a **monolithic web application** built with the **Django framework**. It follows a traditional server-rendered model, where the backend handles business logic, data persistence, and renders HTML templates, which are then styled on the client-side using Tailwind CSS.

For real-time features like the chat, the application uses **Django Channels** to handle WebSocket connections, running on an **ASGI server**.

**Core Design Principles:**
* **Modularity:** The application is divided into distinct Django "apps," each responsible for a specific domain (e.g., product_module, account_module).
* **Simplicity:** A monolithic architecture was chosen to reduce deployment complexity and simplify development.
* **Scalability:** Stateless design where possible, allowing horizontal scaling by adding more app server instances.

## 2. Component Diagram

```mermaid
graph TD
    subgraph Client
        A[User Browser]
    end

    subgraph Backend
        B[Plant Shop Django App]
        C[PostgreSQL Database]
        D[Redis]
    end

    A -->|HTTP/HTTPS Requests| B
    A -->|WebSocket Connection| B

    B -->|Reads/Writes Data| C
    B -->|Caching & WebSocket Messages| D

    subgraph Modules
        acc[Account Module]
        prod[Product Module]
        art[Article Module]
        chat[Chat Module]
        home[Home Module]
    end

    B --> acc
    B --> prod
    B --> art
    B --> chat
    B --> home
Component Descriptions:

User Browser: Renders HTML/CSS and manages interactions.

Plant Shop Django App: Core system containing business logic.

Account Module: User registration, login, profiles, auth.

Product Module: Product catalog, cart, orders.

Article Module: Blog posts and articles.

Chat Module: Real-time chat via Django Channels.

Home Module: Landing pages and static content.

PostgreSQL: Stores persistent data.

Redis: In-memory cache, session storage, and message broker for WebSockets.

3. Deployment Diagram
mermaid
Copy code
graph TD
    subgraph Internet
        Client[User Browser]
    end

    subgraph CloudServer
        Nginx[Nginx Web Server] --> AppGroup[Application Group - StaticFiles]

        subgraph AppGroup
            Gunicorn[Gunicorn WSGI Server] --> Daphne[Daphne ASGI Workers]
        end

        Postgres[PostgreSQL Database]
        RedisCache[Redis]
    end

    Client -->|Port 80/443| Nginx
    Nginx -->|Serves Static/Media| AppGroup
    Nginx -->|Reverse Proxy HTTP| Gunicorn
    Nginx -->|Reverse Proxy WebSocket| Daphne
    Daphne --> Postgres
    Daphne --> RedisCache
Notes:

Nginx: Reverse proxy, SSL terminator, serves /static/ and /media/.

Gunicorn: Handles synchronous HTTP requests.

Daphne: Handles asynchronous WebSocket connections.

PostgreSQL & Redis: Separate services for high availability.

4. Sequence Diagram: User Registration
mermaid
Copy code
sequenceDiagram
    participant Browser
    participant DjangoApp as Django Application
    participant DB as PostgreSQL Database

    Browser ->> DjangoApp: GET /user/register/
    DjangoApp -->> Browser: Return Registration Form

    Browser ->> DjangoApp: POST /user/register/ (form data)
    DjangoApp ->> DjangoApp: Validate form data

    alt Form Valid
        DjangoApp ->> DB: Create user record
        DB -->> DjangoApp: Return User ID
        DjangoApp -->> Browser: Redirect to login page
    else Form Invalid
        DjangoApp -->> Browser: Re-render form with errors
    end
5. Data Flow Overview
User Data: Entered via forms, validated, persisted to PostgreSQL.

Session Data: Stored in Redis for stateless scaling.

Cache Data: Expensive queries cached in Redis to improve performance.

Static Assets: Served by Nginx.

Media Files: User uploads saved in /uploads/, served by Nginx.

Real-time Chat: Messages via WebSocket → Django Channels → Redis channel → other users, also persisted in PostgreSQL.