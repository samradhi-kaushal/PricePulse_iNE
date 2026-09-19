# PricePulse

A product price tracker built for the INE Software Engineer Intern assignment.

## What it does

PricePulse lets users:
- search products
- track products
- check current price and stock
- view price history
- see scrape attempts
- detect price/stock changes
- receive in-app alerts
- configure scrape frequency

Live production links:
- **Frontend App**: [https://ine-price-tracker-mauve.vercel.app](https://ine-price-tracker-mauve.vercel.app)
- **API Health Check**: [https://ine-price-tracker-api-vfq3.onrender.com/api/health](https://ine-price-tracker-api-vfq3.onrender.com/api/health)

---

## Tech Stack

### Frontend
- React 19
- TypeScript
- Vite

### Backend
- Django 5.2 & Django REST Framework
- Python 3.12
- Playwright (Headless Chromium engine)

### Database
- PostgreSQL / Supabase (Local fallback: SQLite3)

### Deployment & Infrastructure
- Vercel (Frontend SPA Hosting)
- Render (Docker Container Backend)
- cron-job.org (External 2-Hour Scrape Scheduler)

---

## How it works

PricePulse operates as a decoupled web application. The React/Vite frontend communicates with the Django REST Framework API to browse catalogue items, toggle product tracking, trigger manual price checks, view price history charts, inspect raw scrape audit logs, and receive real-time notifications for price or stock movements.

```text
React / Vite (Vercel)
        ↓
Django REST Framework (Render Docker)
        ↓
PostgreSQL Database (Supabase)
        ↓
Playwright Scraper Engine
        ↓
INE Storefront
```

---

## Scraping

The INE store features dynamic pricing element reveals and occasional storefront errors, so Playwright Chromium is used for automated browser interaction.

Each scrape:
1. **opens the product page**: Launches a fresh Playwright browser context with desktop User-Agent string.
2. **loads the price/stock**: Handles page interactions (mouse hover over price container, clicking reveal buttons, listening to dynamic background layout requests).
3. **validates the values**: Parses currency (`₹`, `$`, `€`), extracts numeric price values (`price > 0`), and parses stock levels (`N units left`, `Out of Stock` -> `0`, `In Stock` -> `None`).
4. **retries when necessary**: Performs up to 3 bounded attempts with exponential backoff on temporary store timeouts or HTTP errors.
5. **records the scrape attempt**: Every attempt (Success, Retried, or Failed) is recorded as a `ScrapeLog` entry for audit trails.
6. **stores history only when the result is valid**: Price history, change detection events, and user alerts are written atomically only upon a validated successful scrape.

---

## Scheduling

The external cron runs every 2 hours (via cron-job.org triggering `POST /api/jobs/scrape-due`).

Django checks `next_scrape_at <= now()` before deciding which active tracked products are due for scraping. Each product supports configurable intervals (`2h`, `4h`, `6h`, `12h`, `24h`).

Upon a successful scrape, `next_scrape_at` is updated to `attempted_at + interval_hours`. On permanent failure, `next_scrape_at` is rescheduled to `now() + 10 minutes` to avoid infinite retry loops.

---

## Running locally

### 1. Backend Setup (Django + Python Playwright)

```powershell
cd apps/api_django
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
python manage.py migrate
python manage.py runserver 8000
```

The Django REST API will run at `http://127.0.0.1:8000/api`.

### 2. Frontend Setup (React + Vite)

From the project root:

```powershell
npm install
npm run dev -w @tracker/web
```

The React frontend will be available at `http://localhost:5173`.

---

## Environment variables

Local development values are pre-configured with safe defaults in `.env.example`.

### Local Backend (`apps/api_django/.env`)
```ini
SECRET_KEY=django-insecure-local-dev-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
CRON_SECRET=dev-cron-secret-12345
```

### Local Frontend (`apps/web/.env`)
```ini
VITE_API_BASE_URL=http://127.0.0.1:8000/api
```

### Production Environment Variables (Render & Vercel)
- `DATABASE_URL`: Supabase PostgreSQL URI connection string.
- `SECRET_KEY`: Strong random secret key.
- `DEBUG`: `False`
- `ALLOWED_HOSTS`: Render service domain.
- `CORS_ALLOWED_ORIGINS` & `FRONTEND_ORIGIN`: Vercel frontend URL.
- `CRON_SECRET`: Bearer token for external scheduler authentication.
- `VITE_API_BASE_URL`: Public Render API URL.

---

## Testing

### Backend Unit & Integration Tests (Pytest)
```powershell
# From apps/api_django directory
venv\Scripts\pytest -v
```

All 27 backend tests cover models, API views, price/stock parsing logic, scraper retry handling, alert creation, and scheduled batch runs.

### Frontend Production Build Verification (TypeScript & Vite)
```powershell
# From project root
npm run build -w @tracker/web
```

Validates type safety (`tsc -b`) and bundles production assets with Vite.

---

## CI

GitHub Actions workflow (`.github/workflows/ci.yml`) automatically executes on every `push` and `pull_request` to `main` / `master`:
1. **Backend Job**: Runs Django system checks (`python manage.py check`), migration checks (`python manage.py makemigrations --check`), and the 27-test `pytest` suite.
2. **Frontend Job**: Runs `npm ci` and compiles the React application (`npm run build -w @tracker/web`).

---

## Deployment

### 1. Supabase PostgreSQL
Create a project on Supabase and obtain the direct PostgreSQL URI string from **Project Settings -> Database**.

### 2. Render Backend Web Service (Docker)
Connect the repository to Render using the provided root `Dockerfile`. Set environment variables (`DATABASE_URL`, `SECRET_KEY`, `DEBUG=False`, `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, `CRON_SECRET`). Migrations run automatically during startup.

### 3. Vercel Frontend Deployment
Import the repository on Vercel with build output directory `apps/web/dist` (managed via `vercel.json`). Set `VITE_API_BASE_URL` to your live Render API URL.

### 4. External Cron (cron-job.org)
Create an HTTP POST cron job pointing to `https://<render-app>.onrender.com/api/jobs/scrape-due` with header `Authorization: Bearer <CRON_SECRET>` scheduled every 2 hours.

---

## Design decisions

1. **Failure Isolation**: Failed or retried scrapes generate an audit log (`ScrapeLog`) but **never** write false `PriceHistory` entries, `ProductChange` records, or `Alert` notifications.
2. **Change Detection Accuracy**: Price and stock movements are detected strictly by comparing the latest successful observation against the previous successful observation.
3. **External Cron Simplicity**: Instead of running background worker loops (Celery/APScheduler) that consume paid compute, an external HTTP ping wakes Render free-tier instances, while Django manages per-product eligibility using `next_scrape_at <= now()`.
4. **Scraper Resiliency**: Scraper utilizes mouse movement emulation and dynamic layout response interception to reliably parse hidden price elements on storefront layouts.
