"""
voice_assistant.py

OPTIONAL module. Run separately:
    python voice_assistant.py

Flow:
    Microphone -> Speech-to-text (SpeechRecognition) -> parse_transaction()
    -> speak back a confirmation question -> listen for yes/no -> save

--------------------------------------------------------------------------
SETUP (Windows):
1. Install extra packages (NOT in the main requirements.txt, since this
   module is optional and pyaudio can be tricky to install):

       pip install SpeechRecognition pyttsx3 pipwin
       pipwin install pyaudio

   (pipwin installs a prebuilt PyAudio wheel for Windows - plain
   `pip install pyaudio` often fails on Windows with a "Microsoft Visual
   C++ 14.0 required" error, this avoids that.)

2. Microphone permissions:
   Settings -> Privacy & Security -> Microphone -> allow desktop apps
   to access your microphone.

3. Run:
       python voice_assistant.py

If microphone setup fails, this module simply won't run - the main
FinMate website keeps working normally, since this is a separate script.
--------------------------------------------------------------------------
"""
from datetime import datetime

try:
    import speech_recognition as sr
    import pyttsx3
    VOICE_LIBS_AVAILABLE = True
except ImportError:
    VOICE_LIBS_AVAILABLE = False

from app import create_app
from models import db
from models.user import User
from models.transaction import Transaction
from services.nlp_parser import parse_transaction
from automation.engine import check_budget_alerts, check_unusual_spending

DEMO_USER_EMAIL = "demo@finmate.local"  # change to match a real registered account

flask_app = create_app()


def speak(engine, text):
    print(f"FinMate says: {text}")
    engine.say(text)
    engine.runAndWait()


def listen(recognizer, mic):
    with mic as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        print("Listening...")
        audio = recognizer.listen(source, timeout=6, phrase_time_limit=8)
    try:
        text = recognizer.recognize_google(audio)
        print(f"You said: {text}")
        return text
    except sr.UnknownValueError:
        return None
    except sr.RequestError:
        print("Speech recognition service unavailable (check internet connection).")
        return None


def run_voice_assistant():
    if not VOICE_LIBS_AVAILABLE:
        print(
            "Voice libraries not installed. Run:\n"
            "  pip install SpeechRecognition pyttsx3 pipwin\n"
            "  pipwin install pyaudio"
        )
        return

    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    engine = pyttsx3.init()

    speak(engine, "FinMate voice assistant is ready. Say a transaction, like: I spent 250 on food.")

    while True:
        text = listen(recognizer, mic)
        if not text:
            speak(engine, "Sorry, I didn't catch that. Please try again.")
            continue

        if "stop" in text.lower() or "exit" in text.lower():
            speak(engine, "Goodbye!")
            break

        parsed = parse_transaction(text)
        if parsed["type"] is None:
            speak(engine, "I couldn't understand that as a transaction. Please try again.")
            continue

        speak(engine, (
            f"I heard: {parsed['type']} of {int(parsed['amount'])} rupees "
            f"under {parsed['category']}. Should I add this transaction?"
        ))

        confirmation = listen(recognizer, mic)
        if confirmation and "yes" in confirmation.lower():
            with flask_app.app_context():
                user = User.query.filter_by(email=DEMO_USER_EMAIL).first()
                if not user:
                    speak(engine, "No linked FinMate account found. Please register on the website first.")
                    continue

                real_type = "income" if parsed["type"] == "income" else "expense"
                txn = Transaction(
                    user_id=user.id, type=real_type, amount=parsed["amount"], category=parsed["category"],
                    description=parsed["description"], date=datetime.utcnow().date(), source="voice",
                )
                db.session.add(txn)
                db.session.commit()

                if real_type == "expense":
                    check_budget_alerts(user.id)
                    check_unusual_spending(user.id, parsed["category"], parsed["amount"])

            speak(engine, "Transaction added successfully.")
        else:
            speak(engine, "Okay, not adding that transaction.")


if __name__ == "__main__":
    run_voice_assistant()
