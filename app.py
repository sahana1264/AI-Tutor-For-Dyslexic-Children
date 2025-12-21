import os
from datetime import datetime
import io
import sqlite3
import cv2
import numpy as np
import pytesseract
import base64
import requests
import json
import time # Added for exponential backoff
from flask import Flask, request, jsonify, render_template ,redirect, url_for, session
import json
from concurrent.futures import ThreadPoolExecutor
from feedback_generator import generate_dynamic_feedback
from werkzeug.security import generate_password_hash, check_password_hash


# NOTE: Removed Chatterbot imports and related code
app = Flask(__name__)
app.secret_key = "supersecretkey123"


from gpt_module import generate_sentence, get_target_sentence, sentence_similarity
from vit_module import analyze_reversals
from bert_module import check_spelling
from rl_manager import RLManager
from reversal_helper import infer_reversed_letters_from_vit
# Assuming REVERSAL_PAIRS is defined in reversal_helper or available globally
def get_db():
    return sqlite3.connect("dyslexia.db", timeout=10)

# --- Configuration ---
# Set the API key to an empty string. The Canvas environment will inject the key at runtime.
GEMINI_API_KEY ="AIzaSyCMqC8AJWMOlXqsLPMLYH7l38UimSxsYtc"
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent"
SYSTEM_PROMPT = (
    "You are a friendly and encouraging AI assistant for dyslexia learning. "
    "Your core task is to answer the user's question, and if they provide a word, "
    "generate a simple, short, and clear sentence (under 10 words, simple SVO structure) "
    "using that word for them to practice handwriting. Always use high-frequency, "
    "easy-to-read vocabulary. Never explain your dyslexia-friendly rules. "
    "ONLY provide the requested information or the simple sentence."
)
# --- End Configuration ---

def init_db():
    conn = sqlite3.connect("dyslexia.db")
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            password TEXT,
            avatar TEXT,
            created_at TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            spelling_errors INTEGER,
            reversal_errors INTEGER,
            reversed_letters TEXT,
            sentence TEXT,
            timestamp TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()

init_db()

def upgrade_db():
    conn = sqlite3.connect("dyslexia.db")
    cur = conn.cursor()
    try:
        cur.execute("ALTER TABLE users ADD COLUMN learning_level TEXT DEFAULT 'easy'")
        conn.commit()
        print("Database upgraded: learning_level column added.")
    except sqlite3.OperationalError:
        # Column already exists → ignore
        pass
    conn.close()

upgrade_db()

rl = RLManager()  # Reinforcement learning manager

# Helper function for making the Gemini API request with retry logic
def _make_gemini_request(payload, max_retries=5, initial_delay=1.0):
    """Handles the Gemini API request with exponential backoff."""
    delay = initial_delay
    headers = {"Content-Type": "application/json"}
    
    for attempt in range(max_retries):
        try:
            response = requests.post(
                f"{GEMINI_API_URL}?key={GEMINI_API_KEY}", 
                headers=headers, 
                data=json.dumps(payload)
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if attempt == max_retries - 1:
                # Last attempt failed, raise the error
                raise e
            # Wait for delay seconds before retrying
            time.sleep(delay)
            delay *= 2  # Exponential backoff
    
    # Should be unreachable if max_retries > 0
    raise requests.exceptions.RequestException("Max retries exceeded.")

@app.route("/index")
def index():
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT name, avatar FROM users WHERE id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()

    if not row:
        return redirect("/login")

    profile = {"name": row[0], "avatar": row[1]}

    return render_template("index.html", profile=profile)



def get_flashcard_data(reversed_letters):
    """
    Build structured data for flashcards based on reversed letters.
    (This function was already in your script, keeping it for completeness)
    """
    # Placeholder for REVERSAL_PAIRS
    REVERSAL_PAIRS = {"b": "d", "d": "b", "p": "q", "q": "p"}
    flashcards = []
    
    for letter in reversed_letters:
        reversed_form = REVERSAL_PAIRS.get(letter)
        if not reversed_form:
            reversed_form = next((k for k, v in REVERSAL_PAIRS.items() if v == letter), None)
        
        if not reversed_form:
            continue
        
        flashcards.append({
            "wrong": letter,
            "correct": reversed_form,
            "image_wrong": f"letters/{letter}.png",
            "image_correct": f"letters/{reversed_form}.png"
        })
    return flashcards

@app.route("/flashcards", methods=["GET"])
def flashcards():
    reversed_letters = request.args.get("letters", "")
    letters_list = reversed_letters.split(",") if reversed_letters else []
    return render_template("flashcard.html", reversed_letters=letters_list)

@app.route("/get_sentence", methods=["GET"])
def get_sentence_route():
    level = rl.get_current_level()
    sentence = generate_sentence(level)
    return jsonify({"sentence": sentence, "level": level})

# LOGIN
# -----------------------------
# @app.route("/login", methods=["GET", "POST"])
# def login():
#     if request.method == "POST":
#         name = request.form.get("name", "").strip().lower()

#         conn = sqlite3.connect("dyslexia.db")
#         cur = conn.cursor()

#         cur.execute("SELECT id,name FROM users WHERE LOWER(name)=?", (name,))
#         user = cur.fetchone()
#         conn.close()

#         if user:
#             session["user_id"] = user[0]
#             session["name"] = user[1]
#             cur.execute("SELECT learning_level FROM users WHERE id = ?", (session["user_id"],))
#             saved_level = cur.fetchone()[0] or "easy"
#             rl.set_current_level(saved_level)

#             return redirect("/home")

#         return render_template("login.html", error="User not found!")

#     return render_template("login.html")
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        name = request.form.get("name", "").strip().lower()
        password = request.form.get("password", "").strip()


        conn = sqlite3.connect("dyslexia.db")
        cur = conn.cursor()

        cur.execute("SELECT id, name, password,learning_level FROM users WHERE LOWER(name)=?", (name,))
        user = cur.fetchone()
        conn.close()

        if user and check_password_hash(user[2], password):
            session["user_id"] = user[0]
            session["name"] = user[1]

            # Restore level from DB if exists, else use 'easy'
            saved_level = user[3] if user[3] else "easy"
            rl.set_current_level(saved_level)

            return redirect("/home")

        return render_template("login.html", error="User not found!")

    return render_template("login.html")

# -----------------------------
# CREATE PROFILE
# -----------------------------
@app.route("/create_profile", methods=["GET", "POST"])
def create_profile():
    avatar_folder = os.path.join("static", "avatars")
    avatars = [f for f in os.listdir(avatar_folder) if f.endswith((".png", ".jpg"))]

    if request.method == "POST":
        name = request.form.get("name")
        password = request.form.get("password") 
        avatar = request.form.get("avatar")

        if not avatar or not password:
            return render_template(
                "create_profile.html",
                avatars=avatars,
                error="Please select an avatar and enter password"
            )
        
        hashed_pw = generate_password_hash(password)

        conn = get_db()
        cur = conn.cursor()

        try:
            cur.execute(
                "INSERT INTO users (name, password,avatar, created_at) VALUES (?,?, ?, ?)",
                (name,hashed_pw, avatar, datetime.now().strftime("%Y-%m-%d"))
            )
            conn.commit()

        except sqlite3.IntegrityError:
            conn.close()
            # Username already exists
            return render_template(
                "create_profile.html",
                avatars=avatars,
                error="Name already exists! Please choose another or login."
            )

        conn.close()

        session["user_id"] = cur.lastrowid
        session["name"] = name

        return redirect("/login")

    return render_template("create_profile.html", avatars=avatars)


# -----------------------------
# HOME
# -----------------------------
@app.route("/home")
def home():
    if "user_id" not in session:
        return redirect("/login")
    return render_template("home.html", name=session["name"])

@app.route("/")
def root():
    return redirect("/login")




# -----------------------------
# PROGRESS PAGE
# -----------------------------
@app.route("/progress")
def progress():
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    conn = sqlite3.connect("dyslexia.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Fetch progress rows
    cur.execute("SELECT * FROM progress WHERE user_id = ? ORDER BY timestamp", (user_id,))
    rows = cur.fetchall()
    conn.close()

    # Convert rows → dictionary (JSON serializable)
    sessions = []
    for r in rows:
        sessions.append({
            "id": r["id"],
            "spelling_errors": r["spelling_errors"],
            "reversal_errors": r["reversal_errors"],
            "reversed_letters": r["reversed_letters"],
            "sentence": r["sentence"],
            "timestamp": r["timestamp"]
        })

    return render_template("progress.html", sessions=sessions)

# -----------------------------
# PROCESS HANDWRITING
# -----------------------------
@app.route("/process", methods=["POST"])
def process():
    if "user_id" not in session:
        return redirect("/login")

    user_id = session["user_id"]

    if "image" not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    # Read uploaded image
    img_file = request.files['image']
    arr = np.frombuffer(img_file.read(), np.uint8)
    image_cv = cv2.imdecode(arr, cv2.IMREAD_COLOR)

    # Step 1: OCR
    ocr_text = pytesseract.image_to_string(image_cv)

    # Expected sentence
    expected_sentence = request.form.get("expected_sentence")
    if not expected_sentence:
        expected_sentence = get_target_sentence()

    # Step 2: Similarity check
    similarity_score, matches_target = sentence_similarity(expected_sentence, ocr_text)

    if not matches_target:
        return render_template(
            "results.html",
            ocr_text=ocr_text.strip(),
            expected_sentence=expected_sentence,
            matches_target=False,
            similarity_score=round(similarity_score, 3),
            message="The written sentence does not match the target. Please try again.",
            reversed_letters=[],
            flashcards=[],
            chosen_level="easy",
            stats={},
            spelling_errors=[],
            corrections=[],
            feedback=""
        )

    # Step 3: Parallel execution (ViT + BERT)
    with ThreadPoolExecutor() as executor:
        vit_future = executor.submit(analyze_reversals, image_cv)
        bert_future = executor.submit(check_spelling, ocr_text)

        annotated_img, stats, vit_results = vit_future.result()
        spelling_errors, corrections = bert_future.result()

    # Step 4: Infer reversed letters
    reversed_letters = infer_reversed_letters_from_vit(
        expected_sentence, ocr_text, vit_results, image_cv
    )

    # Get reversal error counts
    reversal_count = stats.get("Reversal", 0)
    normal_count = stats.get("Normal", 0)
    corrected_count = stats.get("Corrected", 0)

    # Step 5: RL agent update
    
    # Step 5: RL agent update
    rl.update(spelling_errors, reversal_count)
    level = rl.get_current_level()
    next_sentence = generate_sentence(level)

# -------------------------------
# SAVE PROGRESS and LEVEL INTO SQLITE (Single Transaction)
# -------------------------------
    conn = sqlite3.connect("dyslexia.db")
    cur = conn.cursor()

# Insert session progress
    cur.execute("""
    INSERT INTO progress (user_id, spelling_errors, reversal_errors,
                          reversed_letters, sentence, timestamp)
    VALUES (?, ?, ?, ?, ?, ?)
""", (
    user_id,
    spelling_errors,
    reversal_count,
    ",".join(reversed_letters),
    expected_sentence,
    datetime.now().strftime("%Y-%m-%d %H:%M")
))

# Update RL level for continuity in future sessions
    cur.execute("""
    UPDATE users SET learning_level = ? WHERE id = ?
""", (level, user_id))

    conn.commit()
    conn.close()


    # Step 7: Generate feedback (your function)
    feedback = generate_dynamic_feedback(
        spelling_errors=spelling_errors,
        corrections=corrections,
        reversal_errors=reversal_count
    )

    # Step 8: Encode annotated image
    _, buf = cv2.imencode('.png', annotated_img)
    img_b64 = base64.b64encode(buf).decode('utf-8')

    # Step 9: Prepare flashcards
    flashcards = get_flashcard_data(reversed_letters)

    # Step 10: Render page
    return render_template(
        "results.html",
        stats=stats,
        spelling_errors=spelling_errors,
        corrections=corrections,
        reversed_letters=reversed_letters,
        flashcards=flashcards,
        chosen_level=level,
        next_sentence=next_sentence,
        ocr_text=ocr_text.strip(),
        annotated_image=img_b64,
        expected_sentence=expected_sentence,
        matches_target=True,
        feedback=feedback,
        similarity_score=round(similarity_score, 2),
        reversal_count=reversal_count,
        normal_count=normal_count,
        corrected_count=corrected_count
    )

# ==================================
# 💡 NEW: Dyslexia-Friendly Chatbot
# ==================================


@app.route("/chat", methods=["POST"])
def chat():
    """
    Receives a user message and returns a dyslexic-friendly, concise response
    using the Gemini API with a specialized system prompt, utilizing exponential backoff.
    """
    data = request.get_json()
    user_message = data.get("message", "").strip()

    if not user_message:
        return jsonify({"reply": "Please type something to start the chat!"})

    try:
        # Prepare the CORRECTED payload structure
        payload = {
            # 1. User Message (Contents)
            "contents": [
                {"role": "user", "parts": [{"text": user_message}]},
            ],
            
            # 2. GENERATION CONFIGURATION 
            "generationConfig": {
                "temperature": 0.5, 
            },

            # 3. System Instructions 
            "systemInstruction": {
                "parts": [{"text": SYSTEM_PROMPT}]
            }
        }
        
        # Make the request with exponential backoff
        result = _make_gemini_request(payload)
        
        # Parse the result
        bot_response = result.get("candidates", [{}])[0]\
                             .get("content", {})\
                             .get("parts", [{}])[0]\
                             .get("text", "Sorry, I couldn't generate a response.")
        
        return jsonify({"reply": bot_response.strip()})
        
    except requests.exceptions.RequestException as e:
        # This catches errors from the API call and the exponential backoff helper
        print(f"Gemini API Request Error: {e}")
        return jsonify({"reply": "I'm sorry, I couldn't connect to the helper service. Check the API key and internet connection."})
    except Exception as e:
        print(f"General Chat Error: {e}")
        return jsonify({"reply": f"Sorry, something went wrong. ({type(e).__name__})"})
    


@app.route("/results")
def results():
    return render_template("results.html")

@app.before_request
def force_login_first():
    if request.endpoint == "static":
        return

    if request.endpoint != "login" and "user_id" not in session:
        return redirect("/login")

if __name__ == '__main__':
    # NOTE: The GEMINI_API_KEY is set to "" above. 
    # In the Canvas environment, the key will be injected automatically.
    app.run(debug=True)