# GitRev

A resilient backend service that stays running.

**Tech Stack:** ![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white) ![Peewee ORM](https://img.shields.io/badge/Peewee_ORM-3776AB?style=for-the-badge&logo=python&logoColor=white) ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white) ![uv](https://img.shields.io/badge/uv-DE5FE9?style=for-the-badge&logo=uv&logoColor=white) ![ArgoCD](https://img.shields.io/badge/ArgoCD-EF7B4D?style=for-the-badge&logo=argo&logoColor=white) ![Proxmox](https://img.shields.io/badge/Proxmox-E57000?style=for-the-badge&logo=proxmox&logoColor=white)

**Deployment:** ![Production](https://img.shields.io/badge/Production-Live-brightgreen?style=for-the-badge&logo=checkmarx&logoColor=white)

**CI Status:** [![codecov](https://codecov.io/gh/nic5694/PaneraBreadWarriors/branch/main/graph/badge.svg)](https://codecov.io/gh/nic5694/PaneraBreadWarriors)
[![Build and push Docker image](https://img.shields.io/github/actions/workflow/status/nic5694/PaneraBreadWarriors/python_ci.yml?branch=main&label=Build+%26+Push+Docker&style=for-the-badge&logo=docker&logoColor=white)](https://github.com/nic5694/PaneraBreadWarriors/actions/workflows/python_ci.yml)
[![Run tests and collect coverage](https://img.shields.io/github/actions/workflow/status/nic5694/PaneraBreadWarriors/python_ci.yml?branch=main&label=Tests+%26+Coverage&style=for-the-badge&logo=pytest&logoColor=white)](https://github.com/nic5694/PaneraBreadWarriors/actions/workflows/python_ci.yml)

<img width="333" height="333" alt="medium" src="screenshots/GitRev.png" />

Track #1 Reliability
Track #2 Scalability
Track #3 Incident Response

## Prerequisites

- **uv** — a fast Python package manager that handles Python versions, virtual environments, and dependencies automatically.
  Install it with:
  ```bash
  # macOS / Linux
  curl -LsSf https://astral.sh/uv/install.sh | sh

  # Windows (PowerShell)
  powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```
  For other methods see the [uv installation docs](https://docs.astral.sh/uv/getting-started/installation/).
- PostgreSQL running locally (you can use Docker or a local instance)

## uv Basics

`uv` manages your Python version, virtual environment, and dependencies automatically — no manual `python -m venv` needed.

| Command | What it does |
|---------|--------------|
| `uv sync` | Install all dependencies (creates `.venv` automatically) |
| `uv run <script>` | Run a script using the project's virtual environment |
| `uv add <package>` | Add a new dependency |
| `uv remove <package>` | Remove a dependency |

## Quick Start

```bash
# 1. Clone the repo
git clone <repo-url> && cd mlh-pe-hackathon

# 2. Install dependencies
uv sync

# 3. Create the database
createdb hackathon_db

# 4. Configure environment
cp .env.example .env   # edit if your DB credentials differ

# 5. Run the server
uv run run.py

# 6. Verify
curl http://localhost:5000/health
# → {"status":"ok"}
```

## Reset For Load Tests

Use this before a stress run if you want to clear persisted rows and reseed the cluster database with a Kubernetes Job:

```bash
kubectl apply -f helm/reset-load-test-job.yaml
kubectl wait --for=condition=complete job/reset-load-test-data --timeout=120s
```

If you want to rerun the job, delete the previous one first:

```bash
kubectl delete job reset-load-test-data --ignore-not-found
kubectl apply -f helm/reset-load-test-job.yaml
```

## Project Structure

```
PaneraBreadWarriors/
├── app/
│   ├── __init__.py          # App factory (create_app)
│   ├── database.py          # DatabaseProxy, BaseModel, connection hooks
│   ├── models/
│   │   └── __init__.py      # Import models here
│   └── routes/
│       └── __init__.py      # register_routes() — add blueprints here
├── docs/
│   └── API.md               # API endpoint documentation
├── helm/                    # Helm charts for deployment
├── screenshots/             # Screeshots and Logo
├── seed/                    # Database seed files
├── tests/                   # Unit and integration tests
├── .env.example
├── quest_log.md             # Hackathon progress log
├── run.py
└── README.md
```

# API Docs
See `Docs/API.md` for full endpoint documentation.

# Team
- Nic Martoccia
- Han Lee
- Luciano Scarpaci
- Dylan Brassard
# screenshots
![Screenshot 1](screenshots/pipeline.png)
![Screenshot 2](screenshots/unittest.png)
# Demo
https://youtu.be/ryN-CXHXBS8
