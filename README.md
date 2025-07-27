# Mazzaly Backend

This is a Django REST API for managing recipes, meal plans and user accounts with JWT authentication and Google OAuth support.
It now includes email verification using one-time passwords (OTP).

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   The statistics dashboard requires the optional packages `django-admin-charts` and `django-geoip2` which are included in `requirements.txt`.
2. Apply migrations:
   ```bash
   python manage.py migrate
   ```
   This creates the tables including the `created_at` timestamp on recipes used
   for the new recipe statistics.
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
Set `CORS_ALLOWED_ORIGINS` to the URLs of any frontend applications that should
be allowed to make authenticated requests, e.g.
`http://localhost:8080,https://mazzaly.uz`.

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
data is available. Amounts are parsed even when units like ``"kcal"`` or ``"g"``
appear next to the number. Nutrient names are matched case-insensitively so values
are captured even if the API uses slightly different labels. Remote images are
downloaded and stored in the `MEDIA_ROOT` directory so they can be served by
Django.
Recipes include optional nutrition fields for calories (kcal) and macronutrients
in grams. These values are editable through the admin panel and returned by the
API.
If you import from a local JSON file, image paths can also point to files on
disk relative to that JSON file.
The recipe description is derived from the summary text with HTML stripped so it
remains short and readable.

### Recipe Translations

Imported recipes are stored in English and automatically translated to Uzbek and
Russian. Ingredient and category names are translated as well. Use the `lang`
query parameter on the `/api/recipes/`, `/api/categories/` and ingredient search
endpoints to retrieve data in a specific language. Valid values are `en`, `uz`
or `ru`; any other value defaults to English:

```bash
curl '/api/recipes/?lang=uz'
```

Translations are generated during import using the optional `googletrans`
library. If the library is not available, a small built-in dictionary is used.

### Pagination

Recipe lists are paginated using DRF's standard page number pagination.
Ten recipes are returned per page.
Request a specific page with the `page` query parameter:

```bash
curl '/api/recipes/?page=2'
```

## Admin Panel

The project includes a customized Django admin interface with a cleaner
appearance. To access the admin panel, create a superuser and run the server as
described above. Navigate to `http://localhost:8000/admin/` (or `https://localhost:8000/admin/` if using HTTPS) and log in with your
credentials. The admin header and dashboard titles show **Mazzaly Admin** and a
few style tweaks are applied via `account/static/account/css/admin_custom.css`.

Ingredient, category, recipe and instruction forms expose additional fields
for Uzbek and Russian translations so text can be entered in all three
supported languages.

## Telegram Mini App Authentication

To use this backend from a Telegram Web App ("mini app"), configure the
`TELEGRAM_BOT_TOKEN` variable in your `.env` file. The endpoint
`/api/telegram-auth/` accepts the `initData` string provided by Telegram and
returns a JWT token. Users authenticated through Telegram are created
automatically using their Telegram ID.

## Authenticated Requests

Include the JWT access token in the `Authorization` header. The token may be
provided either with or without the `Bearer` prefix. The recipe list endpoint
automatically filters by the user's active
subscription so no `subscription_plan` query parameter is needed:

```bash
curl -H "Authorization: Bearer <ACCESS_TOKEN>" \
     'https://localhost:8000/api/recipes/'
```

Unauthenticated requests always return only the free **Standard** recipes. When
a user is logged in, recipes for their current subscription tier are included in
the results. If the subscription has expired, the response again falls back to
Standard recipes only.

## Admin Statistics

The admin panel provides a `/admin/statistics/` page with charts and tables
showing recipe views, daily traffic and subscription breakdowns. Data comes from
the `RecipeViewLog` model and the GeoIP database configured via `GEOIP_PATH`.

Charts are rendered with Chart.js and include:

- **Views per Recipe** – bar chart
- **Subscription Distribution** – pie chart
- **Views per Day** – line chart showing the last week
- **Verification Status** – doughnut chart of verified vs unverified users
- **New Recipes** – bar chart of recipes added in the last 30 days
Tables for user activity and total recipe views are paginated 20 rows per page.
Clicking "Download Monthly PDF" first asks for the month you want to report on
and then generates the PDF using WeasyPrint.
The page uses Bootstrap cards so the charts and tables have a clean, responsive layout.

## Chatbot Endpoints

Two API endpoints expose the AI chatbot:

- `POST /api/chatbot/message/` – send a text message and receive a reply.
- `POST /api/chatbot/image/` – upload an image of food and get the predicted food name and kcal value.

Example request sending a text message:

```bash
curl -X POST -H "Content-Type: application/json" \
     -d '{"message": "What can I make with chicken and rice?"}' \
     https://localhost:8000/api/chatbot/message/
```

`/api/chatbot/message/` also accepts URL encoded form data so you can submit `message=...` from an HTML form.

Example request uploading an image:

```bash
curl -X POST -F image=@photo.jpg \
     https://localhost:8000/api/chatbot/image/
```

The chatbot looks up recipes from the existing database before falling back to the Hugging Face conversational model. Recipe names and ingredient names are matched in Uzbek, Russian or English. If a known recipe is mentioned, preparation steps and calorie information are pulled directly from your stored records.

It understands questions like:

- "How do I cook plov?" – returns the preparation steps from the database.
- "Ingredients for lagman" – lists all ingredients of the recipe.
- "How many calories does shashlik have?" – responds with the stored kcal value if available.
- "What can I make with chicken and rice?" – suggests recipes that use those ingredients.
- "Give me healthy options" – lists a few recipes marked as healthy.

For a quick smoke test of the chatbot endpoints you can run `python scripts/test_chatbot.py`. Set the `BASE_URL` environment variable if your server isn't running on `http://localhost:8000`.

