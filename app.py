"""
app.py
The entry point of the whole application. Run this file to start FinMate:
    python app.py
"""
import os
from flask import Flask
from flask_login import LoginManager

from config import Config
from models import db, User


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Make sure the folders these features write to actually exist
    os.makedirs(os.path.dirname(app.config["SQLALCHEMY_DATABASE_URI"].replace("sqlite:///", "")), exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["REPORT_FOLDER"], exist_ok=True)

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # --- Register blueprints (each file in routes/ is one feature area) ---
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.transactions import transactions_bp
    from routes.budgets import budgets_bp
    from routes.investments import investments_bp
    from routes.goals import goals_bp
    from routes.reports import reports_bp
    from routes.automation_routes import automation_bp
    from routes.settings_routes import settings_bp
    from routes.imports import imports_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(transactions_bp)
    app.register_blueprint(budgets_bp)
    app.register_blueprint(investments_bp)
    app.register_blueprint(goals_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(automation_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(imports_bp)

    with app.app_context():
        db.create_all()
        from services.categorization_service import seed_default_rules
        seed_default_rules()

    return app


app = create_app()


if __name__ == "__main__":
    # Start the background automation scheduler (recurring txns, daily alerts)
    from automation.scheduler import start_scheduler
    start_scheduler(app)

    app.run(debug=True)
