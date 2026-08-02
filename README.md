# Privacy-Preserving Voting Web App

A full-stack polling prototype that applies Local Differential Privacy (LDP) in the browser before a vote reaches the server. The backend stores only the randomized report and the effective privacy parameter, then estimates aggregate results after the poll closes.

## Why this project

Traditional polling systems receive each participant's raw response. This project explores a different model: each browser randomizes the selected option locally using weighted k-ary randomized response. The server therefore receives a noisy report rather than the original vote.

This is an educational privacy prototype, not a production election system.

## Features

- Create polls with two or more weighted options
- Select an individual privacy level through epsilon
- Randomize votes locally before transmission
- Prevent repeated voting with an anonymous browser token
- Hide aggregate results until the poll closes
- Debias mixed-epsilon reports on the backend
- Compare true and estimated counts using synthetic experiments

## How the privacy mechanism works

For a poll with `k` options, the browser calculates an effective privacy value for the selected option:

```text
effective epsilon = user epsilon / option weight
```

It then reports the true option with probability:

```text
p = exp(epsilon) / (exp(epsilon) + k - 1)
```

Otherwise, it reports one of the remaining options. A lower epsilon provides stronger privacy but introduces more noise. Higher option weights further reduce the effective epsilon for selected sensitive options.

The backend stores the randomized option and effective epsilon. After the creator closes the poll, it applies per-report debiasing to estimate aggregate counts. Individual raw votes are never sent to the API.

## Architecture

```text
Browser voting UI
  -> weighted randomized response
  -> FastAPI REST API
  -> SQLAlchemy / SQLite
  -> mixed-epsilon debiasing
  -> aggregate results
```

- `frontend/index.html` and `frontend/script.js`: voting interface and client-side randomization
- `frontend/creator.html` and `frontend/creator.js`: poll creation, closing, and result review
- `backend/main.py`: FastAPI routes and debiasing logic
- `backend/models.py`: SQLAlchemy poll, option, vote, and anonymous vote-record models
- `backend/local_exp.py`: synthetic evaluation for sample sizes from 50 to 1,000
- `Final_Project_Report___CS323.pdf`: project methodology and evaluation report

## Technology stack

- Python and FastAPI
- SQLAlchemy and SQLite
- JavaScript, HTML, and CSS
- NumPy and Matplotlib for experiments

## Local setup

### 1. Create and activate a virtual environment

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

macOS or Linux:

```bash
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install fastapi uvicorn sqlalchemy requests numpy matplotlib
```

### 3. Initialize the database

```bash
python -m backend.create_db
```

### 4. Start the API

```bash
python -m uvicorn backend.main:app --reload
```

The API runs at `http://127.0.0.1:8000`. Interactive API documentation is available at `http://127.0.0.1:8000/docs`.

### 5. Serve the frontend

From the repository root, start a static file server:

```bash
python -m http.server 5500 --directory frontend
```

Open:

- Poll creator: `http://127.0.0.1:5500/creator.html`
- Voting interface: `http://127.0.0.1:5500/index.html`

## API endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/create_poll` | Create a poll |
| `POST` | `/add_option` | Add a weighted option |
| `GET` | `/poll/{poll_id}` | Load poll details |
| `POST` | `/vote` | Store a randomized report |
| `POST` | `/close_poll` | Close a poll |
| `GET` | `/results/{poll_id}` | Return debiased aggregate estimates |

## Evaluation

`backend/local_exp.py` simulates mixed privacy preferences and compares known true counts with debiased estimates. Included charts cover sample sizes of 50, 100, 200, 500, and 1,000 synthetic voters, averaged across five trials per sample size.

Run the experiment while the API is running:

```bash
python -m backend.local_exp
```

## Current limitations

- Anonymous voter tokens are stored in browser local storage and are not resistant to deliberate evasion.
- The development API allows all CORS origins.
- SQLite and the static frontend setup are intended for local demonstration.
- The implementation demonstrates privacy concepts but has not received a formal security or cryptographic audit.

## Authors

Philip Pearce-Pearson and project collaborators for Denison University CS 323.
# Privacy Voting Web App

pip install sqlalchemy fastapi uvicorn

clear db with:
    python -m backend.create_db
run app with:
    python -m uvicorn backend.main:app --reload
access app at:
    open creator.html and index.html in browser
