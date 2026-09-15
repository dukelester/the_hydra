# H.Y.D.R.A.

**Human-centered Yield, Data, Rights & Accountability**

Follow the money. Find the evidence. Take action.

H.Y.D.R.A. is an evidence-first civic record for public projects, budgets, institutions, policies, and source documents. It helps people inspect what the files support — without inventing missing facts or treating a gap in the record as a finding of guilt.

The main path is:

**Search → Project → Evidence → Investigation → Report**

Along the way you can watch a county, track a project, compare files, and read county totals from recorded budgets and statuses.

## What it does

- A **project** holds location (county, constituency, ward), institution, contractor, budget, financial year, status, and a timeline from allocation through completion. Stages without a linked source say evidence is unavailable.
- **Evidence** ties a claim to a source document, a page, and a verification status.
- **Evidence coverage** measures how much of the recorded file is supported by sources. It is not a corruption score, fraud score, or trust score.
- **Source documents** can be searched by title, filename, and extracted text (PDF, Word, Excel). Previews stream; large files are not loaded all at once.
- Citizens submit an **investigation** (observation vs official information). Official information and citizen observation stay in separate columns.
- The system generates a structured, neutral **accountability report** from those fields. Reports stay private by default. Language stays: potential discrepancy, evidence indicates, information unavailable, requires further verification.
- **Track my county** follows up to four counties, constituencies, or wards. Constituency and ward lists are linked to the county you pick.
- **Track** and **favourite** pin a project. **Compare** puts up to four projects side by side, or reads county totals from recorded budgets and statuses.
- **County report** charts recorded allocation, delivery mix, and sector budgets — a reading of the file, not a performance verdict.
- Signed-in users get a **dashboard** and a workspace sidebar (hidden on public pages and small screens).
- Staff can manage records at `/admin_dashboard/` (staff accounts only). Django Admin remains at `/admin/`.

H.Y.D.R.A. does not determine guilt, corruption, or fraud. It does not invent missing facts. It does not score people, counties, or contractors for trust.

## Stack

- Python 3.12+
- Django 5.2+ and Django REST Framework
- PostgreSQL in Docker; SQLite for local development (`USE_SQLITE=true`) and tests
- HTMX, HTML, CSS
- Gunicorn, Nginx, Docker Compose
- Uploads: PDF, Word, Excel, images — default **200MB** each, up to **8** files per investigation. Text extraction runs after save.

Primary keys are **UUIDs**. Public project, institution, and policy pages still use slugs. Documents, investigations, reports, evidence, and staff/API object routes use UUIDs (`/sources/<uuid>/`, not `/sources/7/`).

## Project structure

```
the_hydra/
├── config/                 # Settings, root URLs, API URLs
├── apps/
│   ├── accounts/           # Users, dashboard, Track my county
│   ├── projects/           # Institutions, projects, allocations, timeline, compare
│   ├── sources/            # Source documents and evidence
│   ├── investigations/     # Citizen observations and attachments
│   ├── reports/            # Accountability reports and county charts
│   ├── policies/           # Browseable policies
│   ├── staff/              # Staff console at /admin_dashboard/
│   └── core/               # Search, coverage, uploads, shared services
├── templates/
├── static/
├── tests/
├── nginx/
├── Dockerfile
├── docker-compose.yml
└── manage.py
```

## Setup

### Docker

```bash
cp .env.example .env
docker compose up --build
```

Open [http://localhost:8080](http://localhost:8080). If that port is taken, set `NGINX_PORT=8088` in `.env`.

Optional Docker admin (change in `.env`): username `admin`, password `adminpass123`.

### Local virtualenv

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

With `USE_SQLITE=true` (the `.env.example` default), Django uses `db.sqlite3`. Unset that and set `POSTGRES_HOST` to use Postgres.

## Environment

See `.env.example`. Important keys:

| Variable | Purpose |
| --- | --- |
| `DJANGO_SECRET_KEY` | Django secret. Must be strong in production. |
| `DJANGO_DEBUG` | `true` in development only. |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated hosts. |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Comma-separated origins, including `http://localhost:8080`. |
| `USE_SQLITE` | `true` for local SQLite. |
| `POSTGRES_*` | Database name, user, password, host, port. |
| `LOAD_DEMO_DATA` | Load labelled seed records on container start. |
| `THEHYDRA_MAX_UPLOAD_MB` | Max size per file (default 200). |
| `THEHYDRA_MAX_UPLOAD_FILES` | Max files per investigation (default 8). |
| `DJANGO_SUPERUSER_*` | Optional bootstrap admin for Docker. |

Never commit real secrets.

Production uses `config.settings.production` (HTTPS cookies, no debug, required secret key).

## Demo data

```bash
python manage.py load_demo_data --reset
```

Seed records are fictional. Project names in the seed set are labelled `[DEMO]`. They include a mix of fully evidenced, partially evidenced, missing, and conflicting files.

Walkthrough (~3–5 minutes):

1. Open H.Y.D.R.A. and search for `Community Water Access`.
2. Open the project. Read budget, institution, Follow the money, evidence, and missing information.
3. Click **Investigate this project**. You can attach up to eight files.
4. Generate, review, and save the accountability report (private by default).
5. Optionally: Track my county, compare projects, or open the county report.

## Tests

```bash
python manage.py test
```

Coverage includes projects, search, institutions, evidence, timeline, investigations, reports, uploads, staff access, and the API.

## HTML routes

| Path | Description |
| --- | --- |
| `/` | Home |
| `/how-it-works/` | Method and evidence rules |
| `/what-hydra-means/` | About H.Y.D.R.A. |
| `/features/` | Feature list |
| `/terms/` | Terms of use |
| `/search/` | Ranked search (HTMX suggestions in the header and on home) |
| `/projects/` | Project list |
| `/projects/<slug>/` | Project record |
| `/projects/<slug>/investigate/` | Citizen observation form |
| `/projects/compare/` | Compare projects or counties |
| `/institutions/` | Institution directory |
| `/institutions/<slug>/` | Institution, related projects and policies |
| `/policies/` | Policy list |
| `/policies/<slug>/` | Policy detail |
| `/sources/` | Source document list |
| `/sources/<uuid>/` | Source document (preview, extracted text, linked projects) |
| `/accounts/login/` `/accounts/register/` | Auth |
| `/accounts/dashboard/` | Signed-in dashboard |
| `/accounts/my-county/` | Track up to four areas |
| `/accounts/profile/` | Profile |
| `/investigations/` | Your investigations |
| `/investigations/<uuid>/` | Investigation detail |
| `/reports/` | Your reports |
| `/reports/counties/` | County report charts |
| `/reports/generate/<uuid>/` | Generate a structured report |
| `/reports/<uuid>/` | Review and save a report (private) |
| `/admin_dashboard/` | Staff console (staff users) |
| `/admin/` | Django Admin |

## API

Base: `/api/v1/`

| Method | Path |
| --- | --- |
| GET | `/api/v1/projects/` |
| GET | `/api/v1/projects/<uuid>/` |
| GET | `/api/v1/projects/<uuid>/evidence/` |
| GET | `/api/v1/projects/<uuid>/timeline/` |
| GET | `/api/v1/institutions/` |
| GET | `/api/v1/policies/` |
| GET | `/api/v1/search/?q=` |
| POST | `/api/v1/investigations/` |
| GET | `/api/v1/investigations/<uuid>/` |
| POST | `/api/v1/reports/` |
| GET | `/api/v1/reports/<uuid>/` |

Pagination uses page numbers. Investigations and reports are private unless the requester is the owner, staff, or the same browser session that created them.

## Evidence core

The source of truth is the underlying evidence and source documents. Coverage, compare rankings, and county charts are readings of the file — not a verdict.

`apps/core/ai.py` is a deferred interface for a later document-processing layer. It must not replace the Evidence model. Any future answer would still need to cite source, document, page, evidence, and claim.

## Data note

Seed institutions, contractors, and documents are fictional. Do not treat them as real-world allegations.
