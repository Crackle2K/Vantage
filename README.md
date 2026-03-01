# Vantage

Vantage is a trust-first local discovery app. It ranks nearby businesses using verified activity, credibility-weighted reviews, and recency instead of relying only on static star ratings.

## Stack

- Frontend: React 19, Vite 7, TypeScript, Tailwind CSS 4, React Router 7, Lucide React
- Backend: FastAPI, Motor, PyMongo, Pydantic 2
- Database: MongoDB
- Auth: JWT bearer tokens, Google OAuth, reCAPTCHA Enterprise checks on signup
- External APIs: Google Places for nearby discovery backfill and photo enrichment
- Deployment: Vercel (`vercel.json` plus `api/index.py`), local backend via Uvicorn

## Project Structure

```text
Vantage/
  api/
    index.py
  backend/
    main.py
    config.py
    database/
      mongodb.py
    models/
    routes/
      activity.py
      businesses.py
      claims.py
      deals.py
      discovery.py
      saved.py
      subscriptions.py
      users.py
    services/
      business_metadata.py
      google_places.py
      photo_proxy.py
      visibility_score.py
  frontend/
    package.json
    src/
      api.ts
      components/
      contexts/
      hooks/
      pages/
  data/
    demo_businesses.json
  scripts/
    seed_demo_data.py
    smoke_test.py
  requirements.txt
  requirements-dev.txt
```

## Local Setup

### Backend

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn backend.main:app --reload
```

Backend default URL: `http://localhost:8000`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend default URL: `http://localhost:5173`

## Environment

The backend reads `backend/.env` first, then falls back to the repo root `.env`.

Core variables used today:

```env
MONGODB_URI=mongodb://localhost:27017
DATABASE_NAME=vantage
SECRET_KEY=replace-me
GOOGLE_API_KEY=
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
RECAPTCHA_ENTERPRISE_PROJECT_ID=
RECAPTCHA_ENTERPRISE_API_KEY=
RECAPTCHA_ENTERPRISE_SITE_KEY=
FRONTEND_URL=http://localhost:5173
API_URL=http://localhost:8000
DEMO_MODE=false
DEMO_LAT=43.6532
DEMO_LNG=-79.3832
```

## Demo Data

The fixed judges demo dataset lives in [data/demo_businesses.json](/c:/Users/nadee/OneDrive/Documents/GitHub/Vantage/data/demo_businesses.json). It is centered on Toronto core.

Dry run:

```bash
python scripts/seed_demo_data.py --dry-run
```

Seed development DB:

```bash
set ENV=development
python scripts/seed_demo_data.py
```

Useful filters:

```bash
python scripts/seed_demo_data.py --city Toronto --tag judge-demo --count 2
```

Outside `ENV=development`, the script refuses to write unless you pass `--i-understand-this-will-modify-db`.

## Smoke Test

Install dev-only script dependencies:

```bash
pip install -r requirements-dev.txt
```

Run against local backend:

```bash
python scripts/smoke_test.py
```

Run against another deployment:

```bash
python scripts/smoke_test.py --base-url https://your-host
```

What it checks:

- `/health` returns `{"status": "ok", "version": ...}`
- `/api/businesses/nearby` responds with a list and the fields used by the UI
- `/api/auth/me` returns `401` when no bearer token is sent
- `/api/saved` returns `401` when no bearer token is sent

## Key Design Decisions

### Trust-first ranking

The main ranking logic lives in [backend/routes/discovery.py](/c:/Users/nadee/OneDrive/Documents/GitHub/Vantage/backend/routes/discovery.py) and [backend/services/visibility_score.py](/c:/Users/nadee/OneDrive/Documents/GitHub/Vantage/backend/services/visibility_score.py).

- `live_visibility_score` is the base signal.
- Canonical explore ranking then blends that with `local_confidence` and a modest freshness boost.
- Personalized lanes change which items are surfaced, but the final order inside a lane still respects the canonical score.

This keeps Explore feeling personalized without letting weak recommendations outrank high-trust businesses.

### MongoDB for geospatial discovery

MongoDB is used because the app needs:

- fast `$near` queries for nearby businesses
- flexible business documents while the Google Places import path is still evolving
- cached discovery cells and activity-heavy documents without a rigid migration cycle

The backend creates a `2dsphere` index and several supporting indexes in [backend/database/mongodb.py](/c:/Users/nadee/OneDrive/Documents/GitHub/Vantage/backend/database/mongodb.py).

### Spam and fake activity controls

The anti-spam model is partial, but it is intentional:

- distance-based visit verification using Haversine checks
- cooldown windows on visits and check-ins
- reviewer credibility weighting inside the ranking score
- auth-required mutations for saved items, claims, subscriptions, owner events, and comments
- reCAPTCHA Enterprise on signup

This does not fully prevent abuse, but it raises the cost of low-effort fake engagement.

## Demo Flow For Judges (2 Minutes)

1. Open Explore and show the trust-ranked nearby businesses list.
2. Open a business card and show details, ratings, activity, and saved state.
3. Use Decide For Me to generate three goal-based picks.
4. Save a business, then open the Saved page to show the shortlist flow.
5. Sign in as a business owner, claim a listing, then show owner-only profile/event controls.
6. Return to Explore and point out how activity and trust signals affect surfacing.

## API Notes

Common routes used by the UI:

- `GET /health`
- `GET /api/businesses/nearby`
- `GET /api/discover`
- `GET /api/explore/lanes`
- `GET /api/feed`
- `GET /api/activity/pulse`
- `POST /api/checkins`
- `POST /api/feed/{activity_id}/comments`
- `POST /api/claims`

## Known Limitations

- The app still depends on Google Places data quality for some imported listings.
- Some fallback/demo flows are tuned for Toronto and should be parameterized more cleanly.
- There is duplicated frontend helper logic in a few page components (`getBusinessId`, image candidate shaping).
- There is not yet a full automated test suite; current verification is mostly smoke checks plus type/syntax checks.

## Next Steps

- Consolidate repeated frontend view helpers into shared utilities.
- Add route-level backend tests for ranking, auth guards, and saved/check-in flows.
- Add stronger moderation tooling for fake reviews and coordinated engagement.
- Separate demo-only operational scripts from production deployment docs more aggressively.
