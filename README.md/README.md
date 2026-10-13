# PocketSmart AI

PocketSmart AI is a generative AI budget-planning application.

It helps users create plans for:
- Home essentials and furniture
- Party expenses
- Jewelry recommendations

## Technologies

- Python
- FastAPI
- SQLite
- SQLAlchemy
- HTML
- CSS
- JavaScript
- Google Gemini API

## Requirements

- Python 3.10 or newer
- Visual Studio Code
- Internet access for installing packages and using Gemini
- A Gemini API key for live AI recommendations

## Installation

Open this folder in VS Code.

Create a virtual environment:

    python -m venv .venv

Activate it on Windows PowerShell:

    .\.venv\Scripts\Activate.ps1

Install dependencies:

    python -m pip install --upgrade pip
    pip install -r requirements.txt

Create your environment file:

    Copy-Item .env.example .env

Edit `.env` and configure your secret key and Gemini API key.

## Start the application

    python -m uvicorn app.main:app --reload

Open:

- Website: http://127.0.0.1:8000
- API documentation: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/api/health

## Run tests

    python -m pytest -q

## AI mode

When a valid Gemini API key is configured, the application attempts
to generate recommendations using the configured Gemini model.

If the AI service is not configured or a request fails, the application
uses its built-in fallback recommendation mode.

## Database

The default database is SQLite:

    sqlite:///./pocketsmart.db

Tables are created automatically when the application starts.

## Security notes

- Passwords are hashed before being stored.
- Authentication uses bearer tokens.
- Keep `.env` private.
- Change SECRET_KEY before any public deployment.
- Use HTTPS, secure token storage, rate limiting and production
  database migrations before deploying publicly.

## Pricing notes

Prices in fallback plans are illustrative estimates, not live
retailer listings. Product searches open Google Search. Live
shopping integrations require additional APIs or partnerships.