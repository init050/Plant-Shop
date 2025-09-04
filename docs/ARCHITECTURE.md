# Solution Architecture: Plant Shop

## 1. High-Level Architecture

The Plant Shop is a **monolithic web application** built with Django. It is server-rendered, with backend handling business logic, persistence, and HTML templates styled with Tailwind CSS.

Real-time chat uses Django Channels with an ASGI server.

**Core Principles:**

* **Modularity:** Separated into Django "apps" (product\_module, account\_module).
* **Simplicity:** Monolithic design reduces deployment complexity.
* **Scalability:** Stateless design allows horizontal scaling.

---

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
```

**Component Descriptions:**

* **User Browser:** Renders HTML/CSS and manages interactions.
* **Plant Shop Django App:** Core system containing business logic.
* **Account Module:** User registration, login, profiles, auth.
* **Product Module:** Product catalog, cart, orders.
* **Article Module:** Blog posts and articles.
* **Chat Module:** Real-time chat via Django Channels.
* **Home Module:** Landing pages and static content.
* **PostgreSQL:** Stores all persistent data.
* **Redis:** Cache, session storage, message broker for WebSockets.

---

## 3. Deployment Diagram

```mermaid
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
```

**Notes:**

* **Nginx:** Reverse proxy, SSL terminator, serves /static/ and /media/.
* **Gunicorn:** Handles synchronous HTTP requests.
* **Daphne:** Handles WebSocket connections.
* **PostgreSQL & Redis:** Ideally separate services for high availability.

---

## 4. Sequence Diagram: User Registration

```mermaid
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
```

---

## 5. Data Flow Overview

* **User Data:** Entered via forms, validated, persisted to PostgreSQL.
* **Session Data:** Stored in Redis for stateless scaling.
* **Cache Data:** Expensive queries cached in Redis for improved performance.
* **Static Assets:** Served directly by Nginx.
* **Media Files:** User uploads saved in /uploads/ and served by Nginx.
* **Real-time Chat:** Messages sent via WebSocket → Django Channels → Redis channel → other users; also persisted in PostgreSQL.
