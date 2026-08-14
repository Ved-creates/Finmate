"""
config.py
Central place for all configuration values.
Reads secrets from the .env file so nothing sensitive is hardcoded.
"""
import os
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-key-not-safe-for-production")

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'database', 'finmate.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_BOT_USERNAME = os.environ.get("TELEGRAM_BOT_USERNAME", "")

    BUDGET_WARNING_THRESHOLD = int(os.environ.get("BUDGET_WARNING_THRESHOLD", 50))
    BUDGET_DANGER_THRESHOLD = int(os.environ.get("BUDGET_DANGER_THRESHOLD", 80))

    UPLOAD_FOLDER = os.path.join(BASE_DIR, "imports")
    REPORT_FOLDER = os.path.join(BASE_DIR, "reports")
    ALLOWED_IMPORT_EXTENSIONS = {"csv", "xlsx", "xls"}

    EXPENSE_CATEGORIES = [
        "Food", "Transport", "Shopping", "Bills", "Education",
        "Entertainment", "Health", "Travel", "Personal", "Other",
    ]
    INCOME_SOURCES = ["Salary", "Pocket Money", "Freelancing", "Scholarship", "Other"]
    INVESTMENT_TYPES = ["Stocks", "Mutual Funds", "Gold", "Fixed Deposits", "Bonds", "PPF", "Other"]
