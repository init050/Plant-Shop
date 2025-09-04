# Plant Shop: A Modern E-Commerce & Content Platform

**A Django application that blends a curated e-commerce experience with rich content and community features to help plant lovers thrive.**

This project isn't just another online store. It's a platform designed from the ground up to provide a seamless and enjoyable journey for both new and experienced plant owners. It tackles the common frustrations of online plant shopping: cluttered interfaces and a lack of post-purchase support.

> **Note:** The templates (HTML) were created with the help of AI.

---

## 🎯 Key Features

*   **Modern E-Commerce Store:** A clean, intuitive, and fully functional shop with product listings, a shopping cart, and a streamlined checkout process.
*   **Rich Content & Articles:** An integrated blog module allows for the publication of articles on plant care, tips, and tricks, helping users succeed with their purchases.
*   **Real-Time Chat Support:** A live chat feature (built with Django Channels) for users to connect with support or community members.
*   **User Account Management:** A complete user authentication system with profiles, order history, and password management.
*   **Categorization & Tagging:** A flexible system for organizing products and articles, making discovery easy and intuitive.
*   **Responsive Design:** A modern UI built with Tailwind CSS that works beautifully on both desktop and mobile devices.

---

## 🛠️ Tech Stack

This project is built with a modern, robust, and scalable technology stack.

| Category          | Technology                                                                                             |
| ----------------- | ------------------------------------------------------------------------------------------------------ |
| **Backend**       | [Django](https://www.djangoproject.com/) 5.1, [Daphne](https://github.com/django/daphne) (ASGI Server) |
| **Frontend**      | Django Templates, [Tailwind CSS](https://tailwindcss.com/) 3.4                                         |
| **Database**      | [PostgreSQL](https://www.postgresql.org/)                                                              |
| **Real-Time**     | [Django Channels](https://channels.readthedocs.io/en/latest/) 4.2, [Redis](https://redis.io/)          |

---

## 📦 Quick Start

To get the project up and running locally, follow these steps.

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/init050/plant-shop.git
    cd plant-shop
    ```

2.  **Set up the backend:**
    ```bash
    # Create and activate a virtual environment
    python -m venv .venv
    source .venv/bin/activate  # On Windows, use `.venv\Scripts\activate`

    # Install Python dependencies
    pip install -r requirements.txt

    # Set up environment variables
    # The project already contains a .env file, but a .env.example is recommended for new contributors.
    # Ensure your .env file has the necessary database credentials and a SECRET_KEY.
    # cp .env.example .env 

    # Apply database migrations
    python manage.py migrate

    # Run the development server
    python manage.py runserver
    ```

3.  **Set up the frontend:**
    *In a new terminal*, navigate to the project root and run the Tailwind CSS build process. This will watch for changes and automatically rebuild your CSS.
    ```bash
    # (From the project root directory)
    npm install
    npm run build-css
    ```

4.  **Access the application:**
    Open your browser and navigate to `http://127.0.0.1:8000`.

---

## 🧭 Architecture

The application is built using a modular, monolithic architecture. For a detailed breakdown of the components, data flow, and deployment strategy, please see the [**Architecture Document**](./docs/ARCHITECTURE.md).

---

## 🔐 Environment Configuration

All configuration is managed through a `.env` file in the root directory. See [**Configuration Details**](./docs/CONFIGURATION.md) for a full list of required and optional variables.

---

## 📝 Lessons Learned & Design Decisions

This project involved several key design trade-offs, such as choosing a monolithic architecture for simplicity and speed over a microservices approach. For a full discussion of what we learned and the reasoning behind our technical choices, see [**Lessons Learned**](./docs/LESSONS_LEARNED.md).

---

[**Docs**](./docs/)