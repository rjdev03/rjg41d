# Wind Forecast Analytics

A decision-support dashboard for exploring UK national wind generation forecasts and evaluating forecast accuracy against actual generation.

The application uses historical data from **Elexon BMRS** to compare wind generation forecasts with actual generation for January 2026. It provides hourly forecast-versus-actual analysis, forecast error metrics, and data availability information.

## Project Overview

The application addresses two questions relevant to a day-ahead electricity procurement team:

1. What wind generation forecasts were available at the assumed procurement decision cutoff?
2. How accurately did those forecasts predict actual wind generation?

The analysis selects the latest forecast published on or before the decision cutoff for each delivery hour. Forecasts published after that cutoff are excluded to avoid look-ahead bias.

**Scope:** National-level wind generation only, using Elexon BMRS data for January 2026.

## Features

- January 2026 delivery-date selection.
- Hourly wind generation forecast versus actual comparison.
- Forecast error analysis in MW.
- Mean Absolute Error (MAE), Root Mean Squared Error (RMSE), and forecast bias.
- Data availability and evaluation coverage indicators.
- Historical forecast selection based on publication timestamps.
- Interactive dashboard with charts, metric cards, and hourly data table.

## Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React 19, TypeScript, Vite |
| Styling | Tailwind CSS 4 |
| Charts | Recharts |
| Backend | Python 3.12, FastAPI |
| Data analysis | pandas, NumPy |
| Testing | pytest, Ruff |
| Containerization | Docker, Docker Compose |
| Data source | Elexon BMRS |

## Project Structure

```text
.
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── analytics.py
│   │   └── main.py
│   ├── tests/
│   │   ├── test_analytics.py
│   │   └── test_api.py
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── CoveragePanel.tsx
│   │   │   ├── DashboardHeader.tsx
│   │   │   ├── GenerationChart.tsx
│   │   │   ├── HourlyGenerationTable.tsx
│   │   │   └── MetricCard.tsx
│   │   ├── App.tsx
│   │   ├── index.css
│   │   ├── main.tsx
│   │   └── types.ts
│   ├── public/
│   ├── .env.example
│   ├── Dockerfile
│   ├── README.md
│   ├── package.json
│   ├── pnpm-lock.yaml
│   └── vite.config.ts
│
├── data/
│   └── raw/
│       ├── windfor-2026-01.json
│       └── fuelhh-wind-2026-01.json
│
├── scripts/
│   ├── ingest_january_data.py
│   ├── inspect_elexon.py
│   └── validate_january_forecasts.py
│
├── .dockerignore
├── .editorconfig
├── .env.example
├── .gitignore
├── compose.yaml
└── README.md
```

### Key files

- `backend/app/main.py` — FastAPI application, API endpoints, dataset loading, and delivery-date handling.
- `backend/app/analytics.py` — Forecast selection, hourly actual aggregation, error calculation, and accuracy metrics.
- `backend/tests/` — Backend analytics and API tests.
- `frontend/src/App.tsx` — Main dashboard and API integration.
- `frontend/src/components/` — Dashboard components for charts, metrics, coverage, and hourly data.
- `frontend/.env.example` — Example frontend environment configuration.
- `scripts/ingest_january_data.py` — Retrieves and prepares January 2026 Elexon data.
- `scripts/validate_january_forecasts.py` — Validates forecast and actual data coverage.
- `scripts/inspect_elexon.py` — Helps inspect Elexon API responses.
- `backend/Dockerfile`, `frontend/Dockerfile`, and `compose.yaml` — Container build and local application orchestration.

## Data Sources

The application uses two Elexon BMRS datasets:

### WINDFOR — Wind Generation Forecasts

[WINDFOR API documentation](https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/WINDFOR/stream)

Relevant fields:

- `startTime` — Target delivery timestamp.
- `publishTime` — Time the forecast was published.
- `generation` — Forecast wind generation in MW.

### FUELHH — Actual Generation

[FUELHH API documentation](https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/FUELHH/stream)

Relevant fields:

- `startTime` — Actual generation timestamp.
- `fuelType` — Used to select `WIND`.
- `generation` — Actual wind generation in MW.

The prepared datasets are stored under `data/raw/`.

## Analysis Methodology

### Forecast selection

For each delivery hour, the application selects the latest forecast whose `publishTime` is at or before the decision cutoff.

This ensures that the evaluation uses only information that would have been available at the assumed decision time and avoids look-ahead bias.

Forecast records are selected by delivery timestamp, not by publication month. Consequently, forecasts published in December 2025 may be required to evaluate January 1, 2026 delivery periods.

### Decision cutoff

The current prototype assumes a decision cutoff of **16:00 UK local time on the day before delivery**.

This is an analytical assumption for the prototype, not a claim that 16:00 is an official procurement deadline.

### Hourly actual generation

FUELHH actual generation is provided at 30-minute resolution, while the forecast data used in this prototype is hourly.

The application aggregates actual generation into hourly values by averaging the two half-hourly readings for each hour. Incomplete hours are excluded rather than filled with zero.

### Forecast error

The forecast error is calculated as:

`Forecast error = Forecast generation − Actual generation`

A positive error indicates that the forecast overestimated generation; a negative error indicates underestimation.

### Accuracy metrics

- **MAE:** Average absolute forecast error, measured in MW.
- **RMSE:** Square root of the average squared forecast error, measured in MW. Larger errors have greater influence.
- **Bias:** Average signed forecast error, measured in MW. It indicates systematic over- or under-forecasting.

MAPE is not used because actual generation can be zero or close to zero.

## Data Limitations and Assumptions

- The analysis is limited to national-level wind generation from Elexon BMRS.
- The evaluation period covers January 2026 delivery dates.
- Forecasts are selected using publication timestamps to prevent look-ahead bias.
- Actual generation is used as the retrospective evaluation reference; it is not restricted by the forecast decision cutoff.
- Half-hourly actual generation is averaged into hourly values to align with the hourly forecast data.
- Incomplete actual hours are excluded, not treated as zero.
- Forecast accuracy alone does not determine an optimal electricity procurement decision. Demand, other generation sources, market prices, and operational constraints are outside this prototype's scope.

## Running Locally with Docker

### Prerequisites

- Docker Engine
- Docker Compose

### Start the application

From the repository root:

```bash
docker compose up --build -d
```

The frontend and backend will start as separate services.

| Service | URL |
|---|---|
| Dashboard | http://localhost:5173 |
| API | http://localhost:8000 |
| API health check | http://localhost:8000/api/health |
| API documentation | http://localhost:8000/docs |

### Stop the application

```bash
docker compose down
```

### View logs

```bash
docker compose logs -f
```

### Rebuild containers

```bash
docker compose up --build -d
```

## Running Tests

The backend test suite can be run locally using a Python virtual environment.

Run these commands from the repository root. The virtual environment and dependencies will be installed under `backend/.venv/`.

```bash
cd backend

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

python -m pytest -v
ruff check app tests
```

The test suite covers hourly actual aggregation, forecast selection, forecast error calculations, accuracy metrics, and API responses.

## Deployment

The application is deployed as a two-part client-server system:

- **Frontend:** React + Vite, hosted on Vercel.
- **Backend:** FastAPI, hosted on Render using Docker.
- **Data:** Curated January 2026 Elexon WINDFOR and FUELHH datasets are bundled with the backend image.

### Live Application

- **Dashboard:** https://wind-forecast-frontend-six.vercel.app
- **Backend API:** https://wind-forecast-api-6v9b.onrender.com
- **API Health Check:** https://wind-forecast-api-6v9b.onrender.com/api/health
- **API Documentation:** https://wind-forecast-api-6v9b.onrender.com/docs

The backend may take some time to respond after a period of inactivity because the hosting platform's free instance can spin down.

### Deployment Configuration

The frontend uses the `VITE_API_BASE_URL` environment variable to identify the backend API.

The backend uses:
- `PORT` to configure the HTTP listening port.
- `CORS_ORIGINS` to configure the permitted frontend origins.

See the local setup instructions above for running the application using Docker Compose.

## AI Assistance Disclosure

AI tools were used during development for planning, technical guidance, implementation assistance, debugging, and documentation refinement. All generated or suggested code was reviewed and tested as part of the development process.
