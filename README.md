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
4. Run the development server:
   ```bash
   python manage.py runserver
   ```

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

Recipes are stored in English by default. A helper endpoint is available to
get Uzbek and Russian translations for a recipe using `/api/recipes/<id>/translate/`.
The implementation uses the `googletrans` library if it is installed. Without
that dependency the translations fall back to a very small built-in dictionary,
so consider installing `googletrans` for better results.

## Admin Panel

The project includes a customized Django admin interface with a cleaner
appearance. To access the admin panel, create a superuser and run the server as
described above. Navigate to `http://localhost:8000/admin/` and log in with your
credentials. The admin header and dashboard titles show **Mazzaly Admin** and a
few style tweaks are applied via `account/static/account/css/admin_custom.css`.

