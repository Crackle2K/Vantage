# Vantage

Vantage is a trust-first local discovery app. It ranks nearby businesses using verified activity, credibility-weighted reviews, and recency instead of relying only on static star ratings.

## Stack

- Frontend: React 19, Vite 7, TypeScript, Tailwind CSS 4, React Router 7, Lucide React
- Backend: FastAPI, Motor, PyMongo, Pydantic 2
- Database: MongoDB
- Auth: JWT bearer tokens, Google OAuth, reCAPTCHA Enterprise checks on signup
- External APIs: Google Places for nearby discovery backfill and photo enrichment
- Deployment: Vercel (`vercel.json` plus `api/index.py`), local backend via Uvicorn

### Backend

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn backend.main:app --reload
```

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
