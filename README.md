# SONAR-X

**Physics-Aware Explainable Marine Debris Intelligence System**

> Problem Statement SIH26057 — AI-Powered Automated Underwater Marine Debris and Anomaly Detection System using Side-Scan Sonar  
> Theme: Marine & Ocean | Team: Team Kurukshetra

---

## Overview

SONAR-X is an end-to-end sonar intelligence platform implementing the workflow:

```
DETECT → FINGERPRINT → FUSE → CLASSIFY → HAZARD → MAP → VERIFY → TRACK
```

The central differentiator is a sonar-aware verification layer that analyses seven acoustic cues before producing a final classification, rather than relying on a single object detector output.

---

## Architecture

```
sonar-x/
├── frontend/          React + Vite + TypeScript + Tailwind
├── backend/           Django + DRF + JWT + SQLite/PostgreSQL
├── ai/                Python CV/AI engines
│   ├── preprocessing/ Sonar preprocessing pipeline
│   ├── fingerprint/   Seven-cue Sonar Fingerprint Engine
│   ├── fusion/        Evidence Fusion Engine
│   ├── hazard/        Precautionary Hazard Engine
│   ├── temporal/      Temporal Matching Engine
│   ├── detection/     Classical CV fallback detector
│   ├── demo/          Deterministic demo engine + synthetic images
│   └── report_generator.py  PDF report generation
├── tests/             80 tests (unit + API)
└── demo_data/         Demo dataset metadata
```

---

## Quick Start (Development)

### Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL 15+ (optional — SQLite used for development/demo)

### Backend Setup

```bash
cd sonar-x/backend

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Linux/Mac

# Install dependencies
pip install -r requirements.txt
pip install reportlab==4.2.0  # PDF generation

# Run migrations (SQLite for demo)
python manage.py migrate --settings=config.settings_check

# Seed demo data
python manage.py seed_demo --settings=config.settings_check

# Start server
python manage.py runserver 8000 --settings=config.settings_check
```

### Frontend Setup

```bash
cd sonar-x/frontend

# Install dependencies
npm install --legacy-peer-deps

# Start dev server
npm run dev
# Starts at http://localhost:5173 (or 5174 if port in use)

# Production build
npm run build
```

---

## Demo Login

```
URL:      http://localhost:5173
Email:    demo@sonarx.ai
Password: demo123
```

---

## PostgreSQL Configuration (Production)

Copy `.env.example` to `.env` and fill in:

```env
DB_NAME=sonarx_db
DB_USER=sonarx
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
DJANGO_SECRET_KEY=your-secret-key
JWT_SECRET=your-jwt-secret
```

Run with production settings:
```bash
python manage.py migrate
python manage.py seed_demo
python manage.py runserver 8000
```

---

## Docker

```bash
docker compose up --build
```

Services: frontend (port 3000), backend (port 8000), postgres.

---

## Running Tests

```bash
# From repo root
python run_tests.py
# Expected: 80 passed

# API verification (requires server running on port 8000)
cd backend
python run_api_verify.py

# Full demo verification
python full_demo_verify.py

# Scientific claims audit
python scientific_audit.py
```

---

## Key Features

### 1. Sonar-Specific Preprocessing

Pipeline: Ingestion → Nadir Handling → Gain Correction → Slant-Range Correction → Noise Reduction → Contrast Enhancement → Quality Assessment

- Nadir region estimated from across-track intensity profile when metadata unavailable (labelled ESTIMATED)
- Slant-range correction applied only when altitude + range scale are available; otherwise clearly labelled NOT APPLIED
- Original image never modified; processing produces a derivative
- All steps show: APPLIED / SKIPPED / ESTIMATED with reason

### 2. Seven-Cue Sonar Fingerprint

Each detection receives a structured fingerprint:

| Cue | Description |
|-----|-------------|
| Backscatter | Local acoustic intensity relative to seabed |
| Texture | Image variance and entropy analysis |
| Geometry | Shape, aspect ratio, contour regularity |
| Acoustic Shadow | Dark region behind target |
| Object-Shadow Relationship | Geometric consistency check |
| Seabed Context | Target vs. surrounding seabed comparison |
| Signal Quality | Preprocessing quality score |

Each cue returns a score (0–100) and status (STRONG / MODERATE / WEAK / UNAVAILABLE).

### 3. Evidence Fusion

Configurable weighted fusion of seven cues into:
- Evidence Score (prototype heuristic, NOT a probability)
- False Positive Risk (LOW / MEDIUM / HIGH)

Weights are demonstration values, not scientifically validated coefficients.

### 4. Classification

Four classes:
- MARINE DEBRIS
- NATURAL FORMATION  
- SONAR ARTIFACT
- UNKNOWN ANOMALY (valid result — not forced)

### 5. Precautionary Hazard Assessment

Levels: NONE / CAUTION / HIGH CAUTION

The system says **"Potential Hazard — Do Not Disturb"**. It NEVER identifies specific objects as mines, bombs, munitions, or wrecks. Hazard assessment is precautionary only.

### 6. Human Verification

All detections pass through human verification before any operational action. Audit trail stores reviewer, decision, comment, timestamp. Hazard downgrade requires mandatory comment.

### 7. Temporal Debris Tracking

Tracks debris objects across repeat surveys using Haversine spatial filtering + fingerprint similarity scoring.

Statuses:
- STILL PRESENT — detected near original location
- NOT DETECTED — not found (does NOT prove removal)
- POTENTIALLY RELOCATED — nearby candidate with similar fingerprint (requires verification)
- POSSIBLE MATCH / REQUIRES VERIFICATION

The label **POTENTIALLY RELOCATED** is used until human verification confirms the case. A missing detection does NOT prove the object moved.

### 8. Exports

- GeoJSON (RFC 7946, WGS84, longitude-first)
- KML (Google Earth compatible)
- CSV (all detections, empty coords if unavailable, formula-injection protected)

All exports include: data source, software version, survey ID, timestamp, disclaimer.

### 9. Evaluation Metrics

Evaluation page shows **NOT EVALUATED** when no genuine held-out evaluation run exists. No fake accuracy/precision/recall values are ever displayed.

---

## Inference Modes

| Mode | Description |
|------|-------------|
| DEMO | Deterministic cached results — works offline, no model needed |
| CLASSICAL CV | Adaptive threshold + contour detection fallback — NOT a trained model |
| YOLO | Trained model from `AI_MODEL_PATH` — optional |

The UI always displays the inference mode clearly.

---

## Scientific Constraints

1. Side-scan sonar does NOT directly provide water temperature
2. Conventional SSS is NOT a direct bathymetric sensor
3. Missing detection does NOT prove debris was removed or moved
4. POTENTIALLY RELOCATED requires a plausible nearby candidate
5. Unknown Anomaly is a valid classification — not forced into debris
6. Hazard assessment is precautionary — no specific object identification
7. Demo/synthetic data is NOT field performance
8. Evidence scores are prototype heuristics, NOT calibrated probabilities
9. Evaluation metrics only appear when a genuine evaluation run exists

---

## Environment Variables

See `.env.example` for all configuration options.

---

## Limitations

- Image-based sonar input only (XTF/JSF raw ingestion is future scope)
- Classical CV fallback is not a trained model
- Slant-range correction requires altitude + range scale metadata
- GPS coordinates require field calibration for accuracy
- PDF reports require ReportLab (`pip install reportlab`)
- No Redis/Celery in MVP (synchronous processing)
- PostgreSQL requires setup; SQLite used for demo

---

## Future Scope

- Raw XTF/JSF ingestion
- Trained marine debris YOLO model
- PostGIS spatial queries
- Celery async processing
- Multi-survey temporal batch analysis
- Uncertainty quantification
- Calibrated probabilistic detection
- Field validation dataset

---

*SONAR-X Prototype v0.1.0 | Team Kurukshetra | SIH 2025 | Marine & Ocean Theme*
