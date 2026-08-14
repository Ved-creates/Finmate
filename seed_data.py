"""
seed_data.py

Fills your FinMate database with realistic sample data so the dashboard
looks populated (like the reference UI) instead of showing zeros.

HOW TO USE:
1. Save this file directly inside your FinMate folder (same level as app.py)
2. Make sure you've already registered at least one account on the website
   (this script adds data to your FIRST registered user)
3. Run it once:
       python seed_data.py
4. Refresh your dashboard in the browser - it should now show real numbers.

Safe to run multiple times - it just adds more data each time. If you want
a clean slate again, delete database/finmate.db and restart app.py to
regenerate empty tables.
"""
import random
from datetime import date, timedelta

from app import app
from models import db
from models.user import User
from models.transaction import Transaction
from models.budget import Budget
from models.investment import Investment, InvestmentTransaction
from models.goal import Goal
from models.notification import Notification

EXPENSE_CATEGORIES = {
    "Food": (100, 600),
    "Transport": (50, 400),
    "Shopping": (200, 2500),
    "Bills": (500, 2000),
    "Education": (300, 1500),
    "Entertainment": (100, 700),
    "Health": (150, 1200),
}

INCOME_ENTRIES = [
    ("Salary", 15000, "Monthly stipend"),
    ("Pocket Money", 3000, "From family"),
    ("Freelancing", 4500, "Small web project"),
]


def seed():
    with app.app_context():
        user = User.query.first()
        if not user:
            print("No user found. Please register an account on the website first, then re-run this script.")
            return

        print(f"Seeding data for user: {user.email}")
        today = date.today()

        # ---------------- Transactions across the last 8 months ----------------
        for month_offset in range(7, -1, -1):
            month_date = today.replace(day=1) - timedelta(days=month_offset * 30)

            # Income for the month
            for category, base_amount, desc in INCOME_ENTRIES:
                if category == "Salary" or random.random() > 0.4:
                    db.session.add(Transaction(
                        user_id=user.id, type="income",
                        amount=base_amount + random.randint(-500, 1500),
                        category=category, description=desc,
                        date=month_date + timedelta(days=random.randint(0, 4)),
                        source="seed",
                    ))

            # Expenses for the month, a handful per category
            for category, (low, high) in EXPENSE_CATEGORIES.items():
                for _ in range(random.randint(2, 5)):
                    db.session.add(Transaction(
                        user_id=user.id, type="expense",
                        amount=round(random.uniform(low, high), 2),
                        category=category, description=f"{category} expense",
                        date=month_date + timedelta(days=random.randint(0, 27)),
                        source="seed",
                    ))

        db.session.commit()
        print("Added 8 months of income & expense transactions.")

        # ---------------- Budgets for the current month ----------------
        current_month = today.strftime("%Y-%m")
        budget_targets = {"Food": 3000, "Transport": 2000, "Shopping": 2500, "Bills": 2200, "Entertainment": 1000}
        for category, limit in budget_targets.items():
            existing = Budget.query.filter_by(user_id=user.id, category=category, month=current_month).first()
            if not existing:
                db.session.add(Budget(user_id=user.id, category=category, monthly_limit=limit, month=current_month))
        db.session.commit()
        print("Added monthly budgets.")

        # ---------------- Investments ----------------
        investments_data = [
            ("HDFC Mutual Fund", "Mutual Funds", 10000, 11500, 45.2),
            ("Reliance Stocks", "Stocks", 8000, 7400, 20),
            ("Gold ETF", "Gold", 5000, 5650, None),
            ("PPF Account", "PPF", 12000, 12960, None),
        ]
        for name, itype, invested, current, units in investments_data:
            if not Investment.query.filter_by(user_id=user.id, name=name).first():
                inv = Investment(
                    user_id=user.id, name=name, investment_type=itype,
                    invested_amount=invested, current_value=current, units=units,
                    date=today - timedelta(days=random.randint(30, 200)),
                )
                db.session.add(inv)
                db.session.flush()
                db.session.add(InvestmentTransaction(investment_id=inv.id, action="buy", amount=invested))
        db.session.commit()
        print("Added sample investments.")

        # ---------------- Goals ----------------
        goals_data = [
            ("Emergency Fund", 50000, 20000, 180),
            ("New Laptop", 60000, 15000, 120),
            ("Travel Fund", 25000, 8000, 90),
        ]
        for name, target, current, days_ahead in goals_data:
            if not Goal.query.filter_by(user_id=user.id, name=name).first():
                db.session.add(Goal(
                    user_id=user.id, name=name, target_amount=target,
                    current_amount=current, target_date=today + timedelta(days=days_ahead),
                ))
        db.session.commit()
        print("Added sample goals.")

        # ---------------- Notifications ----------------
        sample_notifications = [
            ("Budget Alert", "Food budget is 75% used.", "warning"),
            ("Monthly Summary", "Your savings rate improved this month.", "info"),
            ("Goal Reminder", "'New Laptop' is on track.", "success"),
        ]
        for title, message, level in sample_notifications:
            db.session.add(Notification(user_id=user.id, title=title, message=message, level=level))
        db.session.commit()
        print("Added sample notifications.")

        print("\nDone! Refresh your dashboard in the browser to see the data.")


if __name__ == "__main__":
    seed()
