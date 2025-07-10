# Mazzaly Backend

This is a Django REST API for managing recipes, meal plans and user accounts with JWT authentication and Google OAuth support.
It now includes email verification using one-time passwords (OTP).

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
4. Run the development server with HTTPS:
   ```bash
   ./run_https.sh
   ```
   The script will generate a self-signed certificate the first time you run it
   so the server can be accessed via `https://localhost:8000/`.

To enable HTTPS locally, install `django-sslserver` and run:
   ```bash
   python manage.py runsslserver
   ```
Set `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE` and `CSRF_COOKIE_SECURE` in
your `.env` file to enforce HTTPS and secure cookies in production.

After registering a new account, a verification code is sent to the provided email address.
Send a POST request to `/api/verify-email/` with the email and code to activate the account.

To send real emails instead of logging them to the console, configure the
`EMAIL_HOST_USER` and `EMAIL_HOST_PASSWORD` variables (and optionally
`EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS`) in your `.env` file. When these
variables are provided, the app will use Django's SMTP backend.

Environment variables can be configured using a `.env` file. See `.env.example` for the available keys.

### Importing Recipes

Recipes can be populated automatically using the Spoonacular API. Set
`SPOONACULAR_API_KEY` in your `.env` file and run:

```bash
python manage.py fetch_spoonacular --number 5
```

The command requests full recipe details and nutrition information from
Spoonacular by default.

If the API is not reachable, you can load recipes from a local JSON file using
the `--file` option. A small example file is provided at
`recipes/sample_spoonacular.json`:

```bash
python manage.py fetch_spoonacular --file recipes/sample_spoonacular.json
```

The importer also stores any categories (dish types or diets) returned by the
API and fills the nutrition fields (calories, protein, fats and carbs) if that
data is available. Nutrient names are matched case-insensitively so values
are captured even if the API uses slightly different labels. Remote images are
downloaded and stored in the `MEDIA_ROOT` directory so they can be served by
Django.
If you import from a local JSON file, image paths can also point to files on
disk relative to that JSON file.
The recipe description is derived from the summary text with HTML stripped so it
remains short and readable.

### Translating Recipes

Recipes are entered in English through the admin interface. The project uses
**django-modeltranslation** to store Uzbek and Russian versions of each field.
When the site's language is switched, the API automatically returns data in the
active language. When a recipe is first created, translations are populated
using Google Translate if the optional `googletrans` package is installed
(falling back to a small dictionary otherwise).

## Admin Panel

The project includes a customized Django admin interface with a cleaner
appearance. To access the admin panel, create a superuser and run the server as
described above. Navigate to `http://localhost:8000/admin/` (or `https://localhost:8000/admin/` if using HTTPS) and log in with your
credentials. The admin header and dashboard titles show **Mazzaly Admin** and a
few style tweaks are applied via `account/static/account/css/admin_custom.css`.

## Telegram Mini App Authentication

To use this backend from a Telegram Web App ("mini app"), configure the
`TELEGRAM_BOT_TOKEN` variable in your `.env` file. The endpoint
`/api/telegram-auth/` accepts the `initData` string provided by Telegram and
returns a JWT token. Users authenticated through Telegram are created
automatically using their Telegram ID.

