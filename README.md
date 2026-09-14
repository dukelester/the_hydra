# TheHydra

**Follow the money. Find the evidence. Take action.**

TheHydra is an evidence-first civic accountability platform. It helps people understand public projects, budgets, government decisions, source documents, and potential discrepancies — then investigate and report them.

The core product is:

**SEARCH → PROJECT → EVIDENCE → INVESTIGATION → REPORT**

**AI is intentionally excluded from the MVP.** There are no LLM integrations, embeddings, RAG, vector search, or AI-generated reports. The source of truth is always the underlying evidence and source documents.

## Problem

Public project information is scattered across budgets, tenders, contracts, and reports. Citizens cannot easily see what was allocated, what evidence supports official claims, or where information is missing. Tools that jump straight to “AI answers” hide the evidence trail.

## Solution

TheHydra keeps claims tied to sources:

- A **project** has a budget, institution, status, and timeline.
- **Evidence** connects a claim to a source document, page, and verification status.
- **Evidence Coverage** measures how much recorded information is supported by sources. It is **not** a corruption, fraud, or trust score.
- Citizens can submit an **investigation** (observation vs official information).
- The system generates a structured, neutral **accountability report** from those fields. Reports stay private by default.

## MVP scope

Included:

- Landing page and How It Works
- Projects, institutions, budget allocations, timelines
- Source documents and evidence records
- Evidence coverage and missing-information notes
- HTMX search across projects, institutions, policies, and documents
- Citizen investigation form (anonymous allowed)
- Structured report generation and private review/save
- Django Admin for data entry
- REST API (`/api/v1/`)
- Demo data, tests, Docker Compose (web, Postgres, Nginx)

Not included (by design):

- OpenAI / Anthropic / Gemini
- RAG, embeddings, pgvector
- AI-generated answers, reports, or “corruption detection”

## Architecture

```
Browser (HTML + HTMX)
        │
Django views  ── shared services ──  Django REST Framework
        │
PostgreSQL (projects, evidence, investigations, reports)
```

Future AI (not implemented) should sit beside this, never on top of it:

```
Django  →  AI Service  →  Document retrieval  →  Evidence  →  LLM
```

Any future answer must still cite **source, document, page, evidence, and claim**. See `apps/core/ai.py`.

## Technology stack

- Python 3.12+
- Django 5.2 and Django REST Framework
- PostgreSQL (SQLite for local/dev and tests if Postgres is not configured)
- HTMX, HTML, custom CSS (Tailwind-inspired design tokens)
- Gunicorn, Nginx, Docker Compose

## Project structure

```
the_hydra/
├── config/                 # Django project (settings, urls, wsgi)
├── apps/
│   ├── accounts/           # Custom user
│   ├── projects/           # Institutions, projects, allocations, timeline
│   ├── sources/            # Source documents and evidence
│   ├── investigations/     # Citizen observations
│   ├── reports/            # Structured accountability reports
│   ├── policies/           # Browseable policies
│   └── core/               # Search, coverage, uploads, AI boundary
├── templates/
├── static/
├── tests/
├── nginx/
├── Dockerfile
├── docker-compose.yml
└── manage.py
```

## Setup

### Option A — Docker (recommended for the demo)

```bash
cp .env.example .env
docker compose up --build
```

Open [http://localhost:8080](http://localhost:8080). If port 8080 is already in use, set `NGINX_PORT=8088` in `.env` (or the environment) and open that port instead.

Default demo admin (change in `.env`):

- Username: `admin`
- Password: `adminpass123`

### Option B — Local virtualenv

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py load_demo_data
python manage.py createsuperuser
python manage.py runserver
```

Without Docker, development settings use SQLite unless `POSTGRES_HOST` is set.

## Environment variables

See `.env.example`. Important keys:

| Variable | Purpose |
| --- | --- |
| `DJANGO_SECRET_KEY` | Django secret. Required and must be strong in production. |
| `DJANGO_DEBUG` | `true` in development only. |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated hosts. |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Comma-separated origins, including `http://localhost:8080`. |
| `POSTGRES_*` | Database name, user, password, host, port. |
| `LOAD_DEMO_DATA` | Load labelled demo records on container start. |
| `DJANGO_SUPERUSER_*` | Optional bootstrap admin for Docker. |

Never commit real secrets.

## Database setup

Docker Compose starts PostgreSQL 16 and runs migrations on boot.

Locally:

```bash
python manage.py migrate
```

Production uses `config.settings.production` (HTTPS cookies, no debug, required secret key).

## Demo data

```bash
python manage.py load_demo_data --reset
```

Records are clearly labelled `[DEMO]` and are fictional. They include a mix of fully evidenced, partially evidenced, missing, and conflicting projects.

Demo path (~3–5 minutes):

1. Open TheHydra.
2. Search for `Community Water Access`.
3. Open the project.
4. Read budget, institution, Follow the Money, evidence, and missing information.
5. Click **Investigate This Project**.
6. Submit a citizen observation and optional photo.
7. Generate, review, and save the accountability report.

## Tests

```bash
python manage.py test
```

Coverage includes project creation, search, institutions, evidence, timeline, investigations, authorization, report generation, file validation, and API endpoints.

## HTML routes

| Path | Description |
| --- | --- |
| `/` | Landing page |
| `/how-it-works/` | Method and evidence rules |
| `/search/` | Search (HTMX partials supported) |
| `/projects/` | Project list |
| `/projects/<slug>/` | Project investigation page |
| `/projects/<slug>/investigate/` | Citizen observation form |
| `/institutions/` | Institution list |
| `/institutions/<slug>/` | Institution and related projects |
| `/policies/` | Policy list |
| `/policies/<slug>/` | Policy detail |
| `/sources/<id>/` | Source document |
| `/investigations/` | Current user’s investigations |
| `/investigations/<id>/` | Private investigation |
| `/reports/` | Current user’s reports |
| `/reports/generate/<investigation_id>/` | Generate structured report |
| `/reports/<id>/` | Review and save report (private) |
| `/accounts/login/` `/accounts/register/` | Auth |
| `/admin/` | Django Admin |

## API

Base: `/api/v1/`

| Method | Path |
| --- | --- |
| GET | `/api/v1/projects/` |
| GET | `/api/v1/projects/<id>/` |
| GET | `/api/v1/projects/<id>/evidence/` |
| GET | `/api/v1/projects/<id>/timeline/` |
| GET | `/api/v1/institutions/` |
| GET | `/api/v1/policies/` |
| GET | `/api/v1/search/?q=` |
| POST | `/api/v1/investigations/` |
| GET | `/api/v1/investigations/<id>/` |
| POST | `/api/v1/reports/` |
| GET | `/api/v1/reports/<id>/` |

Pagination uses page numbers. Investigations and reports are private unless the requester is the owner, staff, or the same browser session that created them.

## Future AI layer

`apps/core/ai.py` defines the deferred interface:

- question answering that must cite evidence
- document analysis
- retrieval / RAG
- assisted investigations and reports

Do not replace the Evidence model. Do not install AI dependencies until that phase.

## Licence / data note

Demo institutions, contractors, and documents are fictional and labelled. Do not treat them as real-world allegations.
