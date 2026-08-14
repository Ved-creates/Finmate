"""
telegram_bot.py

A standalone Telegram bot for FinMate. Run this SEPARATELY from app.py:
    python telegram_bot.py

--------------------------------------------------------------------------
LINKING YOUR ACCOUNT (do this once):
1. Log into the FinMate website, go to Settings.
2. Click "Generate Telegram Link Code" - you'll get a 6-character code.
3. Open your bot in Telegram, send:  /link CODE
   (replace CODE with the code shown in Settings)
4. The bot confirms linking. From then on, every message you send is
   recorded against YOUR real FinMate account.
--------------------------------------------------------------------------

Users can then send messages like:
    "spent 250 on food"
    "received 10000 salary"
    "show my balance"
    "show this month's expenses"
    "how much did I spend on food?"
"""
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

from app import create_app
from config import Config
from models import db
from models.user import User
from models.transaction import Transaction
from services.nlp_parser import parse_transaction
from services.dashboard_service import get_totals, get_expenses_by_category
from automation.engine import check_budget_alerts, check_unusual_spending

flask_app = create_app()

# Pending (unconfirmed) parsed transactions per chat, keyed by chat_id
PENDING = {}


def _get_linked_user(chat_id):
    return User.query.filter_by(telegram_chat_id=str(chat_id)).first()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    with flask_app.app_context():
        user = _get_linked_user(chat_id)

    if user:
        await update.message.reply_text(
            f"Welcome back, {user.name.split(' ')[0]}!\n\n"
            "Try:\n"
            "- spent 250 on food\n"
            "- received 15000 salary\n"
            "- show my balance\n"
            "- show this month's expenses"
        )
    else:
        await update.message.reply_text(
            "Hi! I'm your FinMate bot.\n\n"
            "Your Telegram isn't linked to a FinMate account yet.\n"
            "1. Log into the FinMate website\n"
            "2. Go to Settings -> Generate Telegram Link Code\n"
            "3. Send me:  /link CODE"
        )


async def link_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if not context.args:
        await update.message.reply_text("Usage: /link CODE  (get your code from FinMate Settings)")
        return

    code = context.args[0].strip().upper()

    with flask_app.app_context():
        user = User.query.filter_by(telegram_link_code=code).first()
        if not user:
            await update.message.reply_text("That code wasn't recognized or has already been used. "
                                             "Generate a new one in FinMate Settings and try again.")
            return

        user.telegram_chat_id = str(chat_id)
        user.telegram_link_code = None  # one-time use
        db.session.commit()

    await update.message.reply_text(
        f"Linked! Your Telegram is now connected to FinMate as {user.name.split(' ')[0]}. "
        "Try: 'spent 250 on food'"
    )


async def unlink_account(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    with flask_app.app_context():
        user = _get_linked_user(chat_id)
        if user:
            user.telegram_chat_id = None
            db.session.commit()
    await update.message.reply_text("Unlinked. Send /link CODE anytime to reconnect.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()
    chat_id = update.effective_chat.id

    with flask_app.app_context():
        user = _get_linked_user(chat_id)
        if not user:
            await update.message.reply_text(
                "Your Telegram isn't linked yet. Go to FinMate Settings -> "
                "Generate Telegram Link Code, then send me: /link CODE"
            )
            return

        # --- Query-style commands ---
        if "balance" in text or "savings" in text:
            totals = get_totals(user.id)
            await update.message.reply_text(
                f"Income: Rs.{totals['total_income']:,.0f}\n"
                f"Expenses: Rs.{totals['total_expense']:,.0f}\n"
                f"Savings: Rs.{totals['total_savings']:,.0f} ({totals['savings_rate']}%)"
            )
            return

        if "how much did i spend on" in text:
            category = text.split("on")[-1].strip(" ?.!").title()
            by_cat = get_expenses_by_category(user.id)
            amount = by_cat.get(category, 0)
            await update.message.reply_text(f"You've spent Rs.{amount:,.0f} on {category} this month.")
            return

        if "this month's expenses" in text or "show expenses" in text:
            by_cat = get_expenses_by_category(user.id)
            if not by_cat:
                await update.message.reply_text("No expenses recorded this month yet.")
                return
            lines = [f"- {c}: Rs.{a:,.0f}" for c, a in by_cat.items()]
            await update.message.reply_text("This month's expenses:\n" + "\n".join(lines))
            return

        # --- Transaction parsing ---
        parsed = parse_transaction(text)
        if parsed["type"] is None:
            await update.message.reply_text(
                "I couldn't understand that. Try: 'spent 250 on food' or 'received 10000 salary'."
            )
            return

        PENDING[chat_id] = {"user_id": user.id, **parsed}

        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("YES", callback_data="confirm"),
            InlineKeyboardButton("CANCEL", callback_data="cancel"),
        ]])

        await update.message.reply_text(
            f"I detected:\n\n"
            f"{parsed['type'].title()}\n"
            f"Rs.{parsed['amount']:,.0f}\n"
            f"Category: {parsed['category']}\n\n"
            f"Confirm?",
            reply_markup=keyboard,
        )


async def handle_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    pending = PENDING.pop(chat_id, None)

    if not pending:
        await query.edit_message_text("Nothing to confirm - that request expired.")
        return

    if query.data == "cancel":
        await query.edit_message_text("Cancelled.")
        return

    with flask_app.app_context():
        real_type = "income" if pending["type"] == "income" else "expense"
        category = "Investment" if pending["type"] == "investment" else pending["category"]

        txn = Transaction(
            user_id=pending["user_id"], type=real_type, amount=pending["amount"], category=category,
            description=pending["description"], date=datetime.utcnow().date(), source="telegram",
        )
        db.session.add(txn)
        db.session.commit()

        if real_type == "expense":
            check_budget_alerts(pending["user_id"])
            check_unusual_spending(pending["user_id"], category, pending["amount"])

    await query.edit_message_text("Expense added successfully." if real_type == "expense"
                                   else "Income added successfully.")


def main():
    if not Config.TELEGRAM_BOT_TOKEN:
        print("ERROR: TELEGRAM_BOT_TOKEN is not set in your .env file.")
        return

    application = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("link", link_account))
    application.add_handler(CommandHandler("unlink", unlink_account))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(handle_confirmation))

    print("FinMate Telegram bot is running. Press Ctrl+C to stop.")
    application.run_polling()


if __name__ == "__main__":
    main()
