# EquipZense — Chemical Equipment Parameter Visualizer

Hybrid application for analyzing and visualizing chemical equipment parameters. Runs as both:

- Web application (React + Chart.js)
- Desktop application (PyQt5 + Matplotlib)
  backed by a shared Django REST API.

## Overview

- Upload CSV files containing Equipment Name, Type, Flowrate, Pressure, Temperature
- Backend computes summary stats and returns per-equipment records
- Frontends render theme-aware interfaces with filtering, line charts, PDF reports, and upload history

## Tech Stack

- Backend: Django 4.x, Django REST Framework, Token Authentication
- Frontend (Web): React 18, react-chartjs-2 (Chart.js v4)
- Frontend (Desktop): PyQt5, Matplotlib, ReportLab
- Data: Pandas, SQLite

## Features

- Secure authentication (token-based) for uploading and viewing history
- CSV upload from web and desktop
- Summary statistics: total records, type distribution, averages
- Per-equipment line graphs for Flowrate, Pressure, Temperature
- Interactive filtering: by equipment type, name search, parameter ranges
- Theme toggle (light/dark), darker navbar with left app icon
- PDF report generation (summary, charts, upload date)
- History: last 10 uploads per user, read-only view

## Repository Layout

- backend: Django project (core) and app (api)
- frontend-web: React app
- frontend-desktop: PyQt5 desktop app
- media/uploads: Stored CSV files (development)

## API Reference

- POST /api/register/ — Register user; returns token and user
- POST /api/login/ — Obtain auth token for existing user
- POST /api/upload/ — Upload CSV; returns computed analysis
- GET /api/history/ — List last 10 uploads (current user)
- GET /api/history/<id>/ — Retrieve analysis for a specific upload

All protected endpoints require:

```
Authorization: Token <your_token>
```

Response schema (upload/history detail):

```
{
  "file_id": number,
  "uploaded_at": iso_datetime,
  "total_count": number,
  "averages": { "flowrate": number, "pressure": number, "temperature": number },
  "type_distribution": { "<Type>": count, ... },
  "preview": [ { "Equipment Name": "...", "Type": "...", "Flowrate": n, "Pressure": n, "Temperature": n }, ... ],
  "records": [ same shape as preview, full dataset ]
}
```

## CSV Format

Header row required:

```
Equipment Name,Type,Flowrate,Pressure,Temperature
```

Values should be numeric for Flowrate/Pressure/Temperature.

## Setup (From Scratch)

### Backend (Django)

```
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Notes:

- Token auth enabled in settings; CORS allows http://localhost:3000.
- Development uploads stored under backend/media/uploads.

### Web (React)

```
cd frontend-web
npm install
npm start
```

Usage:

- Register or login
- Upload CSV on Dashboard
- Use filters and download PDF
- View last 10 uploads under History (read-only)

### Desktop (PyQt5)

```
cd frontend-desktop
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Usage:

- Login via dialog
- Drag & drop CSV to upload
- Filters above charts; line graphs update live
- Save PDF report
- Click sidebar history items to load analyses

## Development Notes

- Web dev server: http://localhost:3000
- Backend dev server: http://127.0.0.1:8000
- Ensure backend runs before frontends to avoid upload/auth errors.
- React ESLint warnings are non-blocking; add lint scripts if desired.

## Troubleshooting

- 404 at backend root: API lives under /api; frontends call proper endpoints
- CORS issues: ensure backend CORS_ALLOWED_ORIGINS includes frontend URL
- Token errors: login/register to obtain token; frontends store it locally
- CSV validation: headers must match exactly; numeric values required
