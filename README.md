

# Vantage

**Vantage** is a community-powered local business discovery platform that ranks businesses based on verified activity and trust signals rather than static reviews.

This repository contains the full-stack implementation, including:

- **Backend:** FastAPI
- **Frontend:** React Client

---

## Tech Stack

### Backend

- FastAPI
- MongoDB (Motor async driver)
- Google Places API (seed data)
- Python 3.10+

### Frontend

- React (TypeScript/JavaScript)
- Tailwind CSS (if applicable)
- Vite / Next.js (update if needed)

---

## Features

- Geospatial business search (radius-based)
- Google Places API seeding with caching
- MongoDB 2dsphere indexing
- Business claiming system
- Verified visit validation (Haversine distance check)
- Live Visibility Score ranking engine
- Dark & light mode support
- Real-time activity indicators

---

## Project Structure

```
vantage/
│
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models/
│   ├── routes/
│   │   ├── search.py
│   │   ├── claim.py
│   │   ├── visit.py
│   ├── services/
│   │   ├── google_places.py
│   │   ├── ranking.py
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── hooks/
│   └── package.json
│
└── README.md
```

---

## Environment Variables

Create a `.env` file inside `backend/` with the following:

```env
MONGO_URI=your_mongodb_connection_string
GOOGLE_API_KEY=your_google_places_api_key
USE_GOOGLE_API=true
DEMO_MODE=false
DEMO_LAT=43.6532
DEMO_LNG=-79.3832
```

**Important:**
- Do not commit `.env` to version control.
- Restrict API key to Places API only.

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/vantage.git
cd vantage
```

### 2. Backend Setup

Create virtual environment:

```bash
python -m venv venv
```

Activate the virtual environment:

- **Mac/Linux:**  
  `source venv/bin/activate`
- **Windows:**  
  `venv\Scripts\activate`

Install dependencies:

```bash
pip install -r backend/requirements.txt
```

Run server:

```bash
uvicorn backend.main:app --reload
```

Backend runs at:  
`http://localhost:8000`

### 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at:  
`http://localhost:5173` (or your configured port)

---

## Core Concepts

### Business Seeding

- Google Places API used for initial discovery
- Businesses are stored in MongoDB
- `place_id` is used as unique identifier
- Duplicate prevention enforced

### Geospatial Search

- MongoDB 2dsphere index on location field
- Radius-based queries
- Sorted by `live_visibility_score`

### Claiming a Business

- Businesses can be claimed by authenticated users
- Sets `is_claimed = true`
- Associates `owner_id`

### Verified Visits

- User submits their location
- Backend verifies the distance using the Haversine formula
- If within threshold: visit marked as verified, ranking recalculated

### Ranking Algorithm

Live Visibility Score (LVS):

```text
LVS = (0.35 × verified_visits)
    + (0.30 × credibility_weighted_reviews)
    + (0.20 × recency_factor)
    + (0.15 × engagement_rate)
```

Scores are normalized (0–100) for display.

---

## API Endpoints

- **Search Businesses:**  
  `GET /api/search?lat=...&lng=...&radius=...`

- **Claim Business:**  
  `POST /api/business/{id}/claim`

- **Submit Visit:**  
  `POST /api/business/{id}/visit`

---

## Cost & API Controls

- Google API calls cached in MongoDB
- Daily quota limits configured
- Budget alerts enabled
- External API calls can be disabled (`USE_GOOGLE_API=false`)
- Demo Mode can seed a curated local showcase dataset (`DEMO_MODE=true`)

### Demo Mode

- Set `DEMO_MODE=true` in `backend/.env` to seed a compact curated cluster around `DEMO_LAT` / `DEMO_LNG` during backend startup.
- The demo seed includes businesses, descriptions, generated image assets, verified check-ins, reviews, owner events, and activity feed entries so Explore, Pulse, and owner content still feel alive when local data is sparse.
- For internal frontend builds, set `VITE_DEMO_MODE=true` to show a small `Demo Mode` label on Explore while running in development only.

---

## Development Notes

- Seed data before demo for stability
- Ensure MongoDB 2dsphere index is created
- Verify API key restrictions are applied

---

## Deployment

### Vercel Deployment

This application is configured for deployment on Vercel. For detailed deployment instructions, see [VERCEL_DEPLOYMENT.md](./VERCEL_DEPLOYMENT.md).

**Quick Deploy Checklist:**

1. Set up MongoDB Atlas with network access from anywhere (`0.0.0.0/0`)
2. Configure environment variables in Vercel dashboard
3. Ensure `FRONTEND_URL` and `MONGODB_URI` are correctly set
4. Push to GitHub and let Vercel auto-deploy

**Required Environment Variables for Production:**

```env
# MongoDB
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/
DATABASE_NAME=vantage

# Security
SECRET_KEY=<generate-with-openssl-rand-hex-32>

# URLs
API_URL=https://your-app.vercel.app
FRONTEND_URL=https://your-app.vercel.app
VITE_API_URL=https://your-app.vercel.app

# Google Services
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_API_KEY=your-api-key
```


