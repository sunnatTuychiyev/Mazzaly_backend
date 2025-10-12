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

## Telegram Mini App Setup

Create a `.env` file in the project root or export the variables in your shell:

```bash
TELEGRAM_BOT_TOKEN="<PUT_YOUR_TOKEN_HERE>"
WEBAPP_URL="https://<your-public-domain>/telegram/recipes/"
BACKEND_ORIGIN="https://<your-public-domain>"
SECRET_KEY="change-me"

# Alternatively
export TELEGRAM_BOT_TOKEN="123456:ABCDEF..."
export WEBAPP_URL="https://example.com/telegram/recipes/"
export BACKEND_ORIGIN="https://example.com"
export SECRET_KEY="change-me"
```

### Expose HTTPS locally

```bash
# ngrok
ngrok http https://localhost:8000
# or cloudflared
cloudflared tunnel --url https://localhost:8000

# Configure the Mini App URL in @BotFather:
#   Bot Settings → Configure Mini App → set WEBAPP_URL (your public https URL)
Run Django:
python manage.py runserver
Start the demo bot in another shell:
python bot.py
Send /start to your bot; Telegram will show the WebApp button.
Opening the WebApp posts Telegram’s initData to /api/auth/telegram/login/, creating/signing-in the user and setting a JWT cookie (or returning a token).
Access a protected probe endpoint:
curl -H "Authorization: Bearer <ACCESS_TOKEN>" \
  $BACKEND_ORIGIN/api/me/
```

### Manual tests

```bash
# Test login endpoint with a captured init_data
curl -X POST $BACKEND_ORIGIN/api/auth/telegram/login/ \
  -H "Content-Type: application/json" \
  -d '{"init_data":"<INIT_DATA>"}'

# If opened outside Telegram, the page will still load, but authentication may fail because no Telegram data is available.

# Test recipe submission
curl -X POST https://localhost:8000/api/telegram/recipe-submissions/ \
  -F "name=My Salad" \
  -F "description=Tasty" \
  -F "prep_time=5" \
  -F "cook_time=0" \
  -F "servings=2" \
  -F 'ingredients=[{"name":"lettuce"}]' \
  -F 'instructions=[{"step_number":1,"description":"chop"}]' \
  -F "init_data=<INIT_DATA>"

# Test category creation
curl -X POST https://localhost:8000/api/telegram/categories/ \
  -d "name_uz=Shirinlik" \
  -d "name_ru=Десерт" \
  -d "init_data=<INIT_DATA>"

# List your submissions
curl -G --data-urlencode "init_data=<INIT_DATA>" \
  https://localhost:8000/api/telegram/recipe-submissions/mine/
```

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

Halal recipes can also be imported from the Edamam Recipe API. Add your
credentials to `.env`:

```
EDAMAM_APP_ID=your_app_id
EDAMAM_APP_KEY=your_app_key
EDAMAM_ACCOUNT_USER=your_user_id  # or set EDAMAM_USER_ID
```

Then run:

```bash
python manage.py add_edamam_recipes 10 --query egg
```

Or supply the credentials inline:

```bash
EDAMAM_APP_ID=your_app_id EDAMAM_APP_KEY=your_app_key \
    EDAMAM_ACCOUNT_USER=your_user_id \
    python manage.py add_edamam_recipes 10 --query egg
```

The command skips any recipes containing pork or alcohol and translates the
names, categories, ingredients and instructions to Uzbek and Russian
automatically. `.env` values are loaded with `python-dotenv`, and API requests
include the required `Edamam-Account-User` header.

Each recipe is validated before saving: missing ingredient amounts or units are
guessed from the ingredient text, basic descriptions and categories are
generated when absent, rough prep/cook times and servings are estimated, and
recipes without clear instructions or a downloadable image are skipped. Navigation
links and stray ingredient lines are filtered out so instructions contain only
meaningful cooking steps.

If you see an "Edamam API request unauthorized" error, the command prints the
HTTP status code and response body to help debug invalid credentials.

### Recipe Translations

Imported recipes are stored in Uzbek or Russian. Ingredient and category names
are translated as well. When adding recipes through the API, supply Uzbek and
Russian fields (`name_uz`/`name_ru`, `description_uz`/`description_ru` and
translations for ingredients and instructions). The Django admin and Telegram
mini app only expose these Uzbek and Russian fields; English values are filled
automatically from the Uzbek text. Use the `lang` query parameter on the `/api/recipes/`,
`/api/categories/` and ingredient search endpoints to retrieve data in a
specific language. The simplified `/api/recipe-cards/` endpoint accepts the same
parameter. Valid values are `uz` or `ru`; any other value defaults to Uzbek:

```bash
curl '/api/recipes/?lang=uz'
```

Translations are generated during import. If an `OPENAI_API_KEY` is provided,
the OpenAI API is used for higher quality results. Otherwise the optional
`googletrans` library is attempted, and if that fails a small built-in
dictionary provides basic word-level translations.

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
for Uzbek and Russian translations so text can be entered in both supported
languages.

## Telegram Mini App Example

Copy `.env.example` to `.env` and set:

```env
TELEGRAM_BOT_TOKEN="<PUT_YOUR_TOKEN_HERE>"
WEBAPP_URL="https://<your-public-domain>/telegram/recipes/"
BACKEND_ORIGIN="https://<your-public-domain>"
SECRET_KEY="change-me"
```

Replace the placeholders and ensure these variables are exported (or present in a `.env` file) before running `bot.py`; the bot will exit if they are missing.

Expose your local HTTPS server when testing:

```bash
# ngrok
ngrok http https://localhost:8000
# or cloudflared
cloudflared tunnel --url https://localhost:8000
```

Configure the URL in @BotFather → **Bot Settings → Configure Mini App**. Run
your Django server as usual:

```bash
python manage.py runserver
```

Start the demo bot in a separate shell so the WebApp button appears when you
send `/start`:

```bash
python bot.py
```

Opening the WebApp button posts Telegram's `initData` to
`/api/auth/telegram/login/`, automatically creating or signing in the user and
setting a JWT token cookie. The token can be used to access `/api/me/`.
If you open the same URL outside of Telegram, a guard message will be shown
instead of the app.

Test the login endpoint manually:

```bash
curl -X POST $BACKEND_ORIGIN/api/auth/telegram/login/ \
  -H "Content-Type: application/json" \
  -d '{"init_data":"<INIT_DATA>"}'
```

If the page is opened outside Telegram it will attempt to load, though authentication may fail without Telegram context.

## Telegram Recipe Submissions

Telegram Mini App users can send new recipes for moderation. `POST /api/telegram/recipe-submissions/` accepts multipart form data with fields like `name`, `name_uz`, `name_ru`, `description`, `description_uz`, `description_ru`, `prep_time`, `cook_time`, `servings`, `subscription_plan`, `healthy`, `calories`, `protein`, `fats`, `carbs`, `categories` (repeatable), structured `ingredients` and `instructions` JSON strings, optional `images` (up to five files) and the `init_data` string from Telegram. To view your own submissions, call `GET /api/telegram/recipe-submissions/mine/` with the same `init_data` as a query parameter.

Example submission:

```bash
curl -X POST https://localhost:8000/api/telegram/recipe-submissions/ \
  -F "name=My Salad" \
  -F "description=Tasty" \
  -F "prep_time=5" \
  -F "cook_time=0" \
  -F "servings=2" \
  -F 'ingredients=[{"name":"lettuce"}]' \
  -F 'instructions=[{"step_number":1,"description":"chop"}]' \
  -F "init_data=<INIT_DATA>"
```

List your submissions:

```bash
curl -G --data-urlencode "init_data=<INIT_DATA>" \
  https://localhost:8000/api/telegram/recipe-submissions/mine/
```

### Try it with a bot

A minimal `python-telegram-bot` script is provided in `bot.py`.
The script loads a `.env` file automatically, so set `TELEGRAM_BOT_TOKEN` and
`WEBAPP_URL` there or export them in your shell. After configuring the
environment variables, start it with:

```bash
python bot.py
```

Send `/start` to your bot and Telegram will show a button that opens the mini app.
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

## Meal Plans

Authenticated users can create meal plans via `/api/meal-plan/`. Provide the
date, time and meal type by name. A recipe can be referenced with
`recipe_id` or you may supply a short description with `custom_meal` when no
recipe is selected:

All meal plan endpoints accept an optional `lang` query parameter to select the
response language (`uz` or `ru`). If omitted, Uzbek is used.

Default meal types (**breakfast**, **lunch**, **dinner**) are created by the
database migrations. If you provide a new meal type name it will be added
automatically.

```json
{
  "date": "2025-07-31",
  "time": "19:00",
  "type": "dinner",
  "recipe_id": null,
  "custom_meal": "Grilled vegetables"
}
```

To highlight days with scheduled meals, call `/api/meal-plan/planned-dates/`.
It returns a list of dates that have any entries:

```json
{"planned_dates": ["2025-07-30", "2025-07-31"]}
```

To see plans for a specific day, request `/api/meal-plan/date/<YYYY-MM-DD>/`:

```json
{
  "date": "2025-07-31",
  "meals": [
    {
      "type": "breakfast",
      "time": "07:30",
      "recipe": null,
      "custom_meal": null
    },
    {
      "type": "lunch",
      "time": "12:30",
      "recipe": null,
      "custom_meal": null
    },
    {
      "type": "dinner",
      "time": "19:00",
      "recipe": null,
      "custom_meal": null
    }
  ]
}
```

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
- **Recipe Card Visits** – hourly and daily charts of unique visitors
Tables for user activity and total recipe views are paginated 20 rows per page.
Clicking "Download Monthly PDF" first asks for the month you want to report on
and then generates the PDF using WeasyPrint.
The page uses Bootstrap cards so the charts and tables have a clean, responsive layout.

