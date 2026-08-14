# FinMate — Personal Finance & Investment Manager

A full-stack personal finance tracker built with Flask + SQLite, featuring
natural-language transaction entry, a Telegram bot, bank statement import,
budgets, investments, goals, automation, and PDF reports.

Built as a first software project by a first-year Electronics & Computer
Science student — the codebase favors clarity over cleverness.

## Features

- Secure login/registration (hashed passwords, Flask-Login)
- Dashboard: income/expense/savings/investment summary cards, charts, budgets,
  recent transactions, automation alerts, goals, and a Financial Health Score
- Income & Expense tracking with auto-categorization
- Natural language quick-add: type "spent 250 on food" and confirm
- Budgets per category with 50%/80%/exceeded alerts (thresholds configurable)
- Investment tracker (stocks, mutual funds, gold, FDs, bonds, PPF) with
  gain/loss and allocation chart
- Financial goals with progress tracking
- Bank statement import (CSV/Excel) with auto-categorization and duplicate detection
- Automation engine: budget alerts, unusual spending detection, recurring
  transactions, goal reminders, monthly summaries
- Monthly PDF report generation (ReportLab)
- Telegram bot (optional, separate process) - same natural language commands
- Voice assistant module (optional, separate process)
- Pytest test suite for the NLP parser and core transaction math

## Tech Stack

Flask · SQLAlchemy · SQLite · Flask-Login · Flask-WTF · Bootstrap 5 · Chart.js
· Pandas · OpenPyXL · ReportLab · APScheduler · python-telegram-bot · Pytest

## Project Structure

```
FinMate/
├── app.py                  # App factory & entry point
├── config.py                # Central configuration (reads .env)
├── telegram_bot.py          # Optional: Telegram bot (run separately)
├── voice_assistant.py       # Optional: voice input (run separately)
├── requirements.txt
├── .env.example              # Copy to .env and fill in secrets
├── .gitignore
│
├── models/                  # SQLAlchemy database models
├── routes/                  # Flask blueprints (one file per feature area)
├── services/                # Business logic: NLP parser, categorization,
│                             #   budgets, dashboard data, health score,
│                             #   anomaly detection, imports, PDF reports
├── automation/               # Background automation engine & scheduler
├── utils/                    # Flask-WTF forms
├── templates/                # Jinja2 HTML templates
├── static/css, static/js     # Stylesheet and client-side assets
├── database/                 # SQLite database file lives here (auto-created)
├── reports/                  # Generated PDF reports land here
├── imports/                  # Uploaded bank statements land here
└── tests/                    # Pytest test suite
```

## Setup

```bash
# 1. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # Mac/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment variables
copy .env.example .env         # Windows
cp .env.example .env           # Mac/Linux
# then open .env and set SECRET_KEY to a long random string

# 4. Run the app
python app.py
```

Visit **http://127.0.0.1:5000**, register an account, and start adding transactions.

## Running Tests

```bash
pytest -v
```

## Optional: Telegram Bot

1. Message **@BotFather** on Telegram, send `/newbot`, copy the token it gives you.
2. Paste it into `.env` as `TELEGRAM_BOT_TOKEN=...`
3. In a **separate terminal** (with venv active): `python telegram_bot.py`

## Optional: Voice Assistant

Requires extra packages not in the default install (microphone access is
environment-specific): `pip install SpeechRecognition pyttsx3 pyaudio`
Then run `python voice_assistant.py`. See the file's docstring for
Windows microphone permission steps.

## Security Notes

- Passwords are hashed with Werkzeug, never stored in plain text.
- All secrets (SECRET_KEY, Telegram token) live in `.env`, which is
  git-ignored and never committed.
- CSRF protection is enabled on every form via Flask-WTF.
- This project is a learning tool: it does NOT connect to real bank
  logins. Bank data enters only via CSV/Excel statement upload.

## Disclaimer

The Financial Health Score and all budgeting/investment insights are
project-defined educational indicators, not professional financial advice.
