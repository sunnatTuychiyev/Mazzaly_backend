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

## Admin Panel

The project includes a customized Django admin interface with a cleaner
appearance. To access the admin panel, create a superuser and run the server as
described above. Navigate to `http://localhost:8000/admin/` and log in with your
credentials. The admin header and dashboard titles show **Mazzaly Admin** and a
few style tweaks are applied via `account/static/account/css/admin_custom.css`.

