# Mazzaly Backend

This is a Django REST API for managing recipes, meal plans and user accounts with JWT authentication and Google OAuth support.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Apply migrations:
   ```bash
   python manage.py migrate
   ```
3. Create a superuser (optional):
   ```bash
   python manage.py createsuperuser
   ```
4. Run the development server:
   ```bash
   python manage.py runserver
   ```

Environment variables can be configured using a `.env` file. See `.env.example` for the available keys.

