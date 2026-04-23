import streamlit as st
from groq import Groq
import sqlite3
import speech_recognition as sr
import tempfile
from duckduckgo_search import DDGS
from pypdf import PdfReader
import docx
import re
from collections import Counter
import io
from gtts import gTTS
import hashlib
import os


# ======================
# CONFIG & THEME
# ======================
st.set_page_config(page_title="AI Assistant Pro", layout="wide")

with st.sidebar:
    st.title("🎨 UI Customization")
    theme_choice = st.selectbox("Select Theme", ["Default", "Glass Blue"])
    st.divider()

if theme_choice == "Glass Blue":
    st.markdown("""
    <style>
    .stApp { 
        background: linear-gradient(135deg, #e0f2fe 0%, #bae6fd 50%, #7dd3fc 100%) !important; 
    }
    </style>
    """, unsafe_allow_html=True)

# ======================
# 🔐 SECURE API
# ======================
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# ======================
# DB
# ======================
conn = sqlite3.connect("ai_pro_ultra_v7.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""CREATE TABLE IF NOT EXISTS sessions(
    id INTEGER PRIMARY KEY,
    title TEXT,
    username TEXT,
    is_archived INTEGER DEFAULT 0
)""")

cursor.execute("""CREATE TABLE IF NOT EXISTS messages(
    session_id INTEGER,
    role TEXT,
    content TEXT,
    username TEXT
)""")

cursor.execute("""CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
)""")

conn.commit()

# ======================
# ⚡ CACHE
# ======================
@st.cache_data
def get_user_messages(username):
    return cursor.execute(
        "SELECT content FROM messages WHERE role='user' AND username=?",
        (username,)
    ).fetchall()

# ======================
# LOGIN SYSTEM
# ======================
def is_admin():
    return st.session_state.username == "admin"

def hash_pass(p):
    return hashlib.sha256(p.encode()).hexdigest()

def login_user(username, password):
    return cursor.execute(
        "SELECT * FROM users WHERE username=? AND password=?",
        (username, hash_pass(password))
    ).fetchone()

def signup_user(username, password):
    try:
        cursor.execute(
            "INSERT INTO users(username, password) VALUES(?, ?)",
            (username, hash_pass(password)))
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Signup Error: {e}")
        return False

# ======================
# SESSION STATE
# ======================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
 
if "username" not in st.session_state:
    st.session_state.username = ""

if "session_id" not in st.session_state:
    st.session_state.session_id = None

if "messages" not in st.session_state:
    st.session_state.messages = []

if "predict_val" not in st.session_state:
    st.session_state.predict_val = ""

# ======================
# LOGIN UI
# ======================

if not st.session_state.logged_in:
    st.title("🔐 Login / Signup")

    mode = st.radio("Select", ["Login", "Signup"])
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if mode == "Login":
        if st.button("Login"):
            user = login_user(username, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("Invalid Credentials")

    else:
        if st.button("Signup"):
            if signup_user(username, password):
                st.success("Account Created")
            else:
                st.error("Username exists")

    st.stop()

# ======================
# FILE READ
# ======================
def extract_text_from_file(file):
    try:
        if file.name.endswith('.pdf'):
            pdf_reader = PdfReader(file)
            return " ".join([p.extract_text() or "" for p in pdf_reader.pages])
        elif file.name.endswith('.docx'):
            doc = docx.Document(file)
            return "\n".join([para.text for para in doc.paragraphs])
        else:
            return file.read().decode("utf-8")
    except Exception as e:
        return str(e)

# ======================
# WORD PREDICTION
# ======================
def predict_next_word(input_text):
    if not input_text or " " not in input_text:
        return []

    rows = get_user_messages(st.session_state.username)
    data = " ".join([r[0].lower() for r in rows])
    words = re.findall(r'\w+', data)

    last_word = input_text.split()[-1].lower()
    matches = [words[i+1] for i in range(len(words)-1) if words[i] == last_word]

    return [w for w, c in Counter(matches).most_common(3)]

# ======================
# SIDEBAR
# ======================
with st.sidebar:
    st.write(f"👤 {st.session_state.username}")

    if st.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.messages = []
        st.session_state.session_id = None
        st.rerun()

    st.subheader("🛠️ Context & Search")
    s_mode = st.radio("Intensity", ["Short Search", "Deep Search"])
    u_file = st.file_uploader("Context File", type=["pdf", "docx", "txt"])

    st.subheader("🎤 Voice Settings")
    voice_lang = st.selectbox("Language", ["hi", "en"])

    st.divider()
    st.subheader("📂 Conversations")

    if st.button("➕ New Chat"):
        st.session_state.messages = []
        st.session_state.session_id = None
        st.rerun()

    show_arc = st.toggle("Show Archived Chats")

    cursor.execute("""
    SELECT id, title FROM sessions 
    WHERE is_archived=? AND username=? 
    ORDER BY id DESC
    """, (1 if show_arc else 0, st.session_state.username))

    sessions = cursor.fetchall()

    if sessions:
        session_dict = {f"{title[:20]} (ID:{sid})": sid for sid, title in sessions}
        selected = st.selectbox("Select Chat", list(session_dict.keys()))

        col1, col2, col3 = st.columns(3)

        if col1.button("📂 Load"):
            sid = session_dict[selected]
            st.session_state.session_id = sid
            st.session_state.messages = [
                {"role": r, "content": c}
                for r, c in cursor.execute(
                    "SELECT role, content FROM messages WHERE session_id=? AND username=?",
                    (sid, st.session_state.username)
                ).fetchall()
            ]
            st.rerun()

        if col2.button("🗄 Archive"):
            cursor.execute("UPDATE sessions SET is_archived=1 WHERE id=? AND username=?",
                           (session_dict[selected], st.session_state.username))
            conn.commit()
            st.rerun()

        if col3.button("🗑 Delete"):
            sid = session_dict[selected]
            cursor.execute("DELETE FROM sessions WHERE id=? AND username=?", (sid, st.session_state.username))
            cursor.execute("DELETE FROM messages WHERE session_id=? AND username=?", (sid, st.session_state.username))
            conn.commit()
            st.rerun()

    # 📊 ANALYTICS
    if is_admin():
        st.divider()
        st.subheader("📊 Analytics")

        try:
            total_users = cursor.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            total_msgs = cursor.execute("SELECT COUNT(*) FROM messages").fetchone()[0]

            st.write(f"👥 Users: {total_users}")
            st.write(f"💬 Messages: {total_msgs}")

            top_users = cursor.execute("""
                SELECT username, COUNT(*) FROM messages
                GROUP BY username ORDER BY COUNT(*) DESC LIMIT 3
            """).fetchall()

            for u, c in top_users:
                st.write(f"{u} → {c}")
        except Exception as e:
            st.error(e)

# ======================
# MAIN UI
# ======================
st.title("AI Assistant Pro 🚀")

if "messages" not in st.session_state:
    st.session_state.messages = []

for i, m in enumerate(st.session_state.messages):
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

        if m["role"] == "assistant":
            if st.button("🔊 Listen", key=f"listen_{i}"):
                tts = gTTS(text=m["content"], lang=voice_lang)
                temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
                tts.save(temp_audio.name)
                st.audio(open(temp_audio.name, "rb").read())

st.write("---")

if "predict_val" not in st.session_state:
    st.session_state.predict_val = ""

preds = predict_next_word(st.session_state.predict_val)

if preds:
    st.markdown(f"💡 Suggested: {' | '.join(preds)}")

prompt = st.chat_input("Ask me anything...")

# 🎤 VOICE INPUT
if st.button("🎤"):
    r = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            audio = r.listen(source, timeout=4)
            prompt = r.recognize_google(audio)
    except:
        st.error("Mic Error!")

# ======================
# GENERATION
# ======================
if prompt:
    st.session_state.predict_val = prompt

    if not st.session_state.session_id:
        cursor.execute(
            "INSERT INTO sessions(title, username) VALUES(?,?)",
            (prompt[:30], st.session_state.username)
        )
        conn.commit()
        st.session_state.session_id = cursor.lastrowid

    sid = st.session_state.session_id

    st.session_state.messages.append({"role": "user", "content": prompt})
    cursor.execute("INSERT INTO messages VALUES(?,?,?,?)",
                   (sid, "user", prompt, st.session_state.username))
    conn.commit()

    with st.chat_message("user"):
        st.markdown(prompt)

    # 🧠 MEMORY
    history = st.session_state.messages[-5:]

    # 🌐 CONTEXT
    context = ""

    if u_file:
        context += extract_text_from_file(u_file)

    try:
        with DDGS() as ddgs:
            results = [
                f"{r['title']} - {r['body']}"
                for r in ddgs.text(prompt, max_results=5)
            ]
            context += "\n".join(results)
    except:
        pass

    with st.chat_message("assistant"):
        with st.spinner("Thinking... 🤔"):
            full_res = ""
            ph = st.empty()

            messages = [{"role": "system", "content": f"Mode: {s_mode}"}]
            messages += history
            messages.append({"role": "user", "content": context + "\n" + prompt})

            stream = client.chat.completions.create(
                messages=messages,
                model="llama-3.1-8b-instant",
                stream=True
            )

            for chunk in stream:
                full_res += (chunk.choices[0].delta.content or "")
                ph.markdown(full_res + "▌")

            ph.markdown(full_res)

        st.session_state.messages.append({"role": "assistant", "content": full_res})
        cursor.execute("INSERT INTO messages VALUES(?,?,?,?)",
                       (sid, "assistant", full_res, st.session_state.username))
        conn.commit()