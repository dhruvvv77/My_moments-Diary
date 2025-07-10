from dateutil import parser
import streamlit as st
import sqlite3
from textblob import TextBlob
from datetime import datetime

# Database setup
# SQLite DB setup
conn = sqlite3.connect("mymoments_diary.db", check_same_thread=False)
cursor = conn.cursor()


# Create tables if not exist
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS diary_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_date TIMESTAMP,
    content TEXT,
    polarity REAL,
    subjectivity REAL,
    user_id INTEGER,
    FOREIGN KEY(user_id) REFERENCES users(id)
)
''')
conn.commit()


# Page settings
st.set_page_config(page_title="My Moments Diary", page_icon="📝")

# Session defaults
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.username = ""

# User authentication

def login():
    st.subheader("🔐 Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        cursor.execute("SELECT id FROM users WHERE username=? AND password=?", (username, password))
        user = cursor.fetchone()
        if user:
            st.session_state.logged_in = True
            st.session_state.user_id = user[0]
            st.session_state.username = username
            st.success("Logged in successfully!")
            st.rerun()

        else:
            st.error("Invalid credentials")

def signup():
    st.subheader("🆕 Create Account")
    username = st.text_input("New Username")
    password = st.text_input("New Password", type="password")
    if st.button("Create Account"):
        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()

            st.success("Account created! You can now log in.")
        except sqlite3.IntegrityError:
            st.error("Username already exists.")

if not st.session_state.logged_in:
    option = st.radio("Choose:", ["Login", "Create Account"])
    login() if option == "Login" else signup()
    st.stop()

def parse_date(date_str):
    for fmt in ('%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S'):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


# 🔓 Logout option
st.sidebar.write(f"👤 Logged in as: `{st.session_state.username}`")
if st.sidebar.button("🚪 Logout"):
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.username = ""
    st.rerun()


# App header
st.title("📝 MyMoments – Your Digital Twin Diary")
st.markdown(f"Welcome, **{st.session_state.username}**! Your personal AI diary.")
st.markdown("---")

# Main menu
menu = st.radio("Choose an option:", [
    "➕ Add Entry",
    "📖 View Entries",
    "🔍 Search Entries",
    "🗑️ Delete Entry",
    "🗣️ Talk to Your AI Twin",
    "📤 Export Entries",
    "🤖 Train Your AI Twin"
])

# ➕ ADD ENTRY
if menu == "➕ Add Entry":
    text = st.text_area("What's on your mind today?", height=200)
    if st.button("Save Entry"):
        if text.strip() == "":
            st.warning("⚠️ Please write something before saving.")
        else:
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity
            subjectivity = blob.sentiment.subjectivity
            sql = "INSERT INTO diary_entries (entry_date, content, polarity, subjectivity, user_id) VALUES (?, ?, ?, ?, ?)"
            val = (datetime.now(), text, polarity, subjectivity, st.session_state.user_id)
            cursor.execute(sql, val)
            conn.commit()

            mood_score = round((polarity + 1) * 5, 1)
            thought_score = round(subjectivity * 10, 1)
            st.success("✅ Entry saved successfully!")
            st.info(f"😊 Mood Score: {mood_score}/10 | 🤔 Thought Depth: {thought_score}/10")

# 📖 VIEW ENTRIES
elif menu == "📖 View Entries":
    if st.button("Show All Entries"):
        cursor.execute("SELECT entry_date, content, polarity, subjectivity FROM diary_entries WHERE user_id = ? ORDER BY entry_date DESC", (st.session_state.user_id,))
        entries = cursor.fetchall()
        if entries:
            for date, content, pol, subj in entries:
                mood_score = round((pol + 1) * 5, 1)
                thought_score = round(subj * 10, 1)
                st.markdown(f"""
                ---
                🗓️ **{datetime.strptime(date, '%Y-%m-%d %H:%M:?.%f').strftime('%Y-%m-%d %H:%M')}**
                📝 *{content}*
                😊 **Mood Score**: `{mood_score}/10`  
                🤔 **Thought Depth**: `{thought_score}/10`
                """)
        else:
            st.info("No entries found.")

# 🔍 SEARCH ENTRIES
elif menu == "🔍 Search Entries":
    search_mode = st.radio("Search by:", ["📅 Date", "😊 Mood"])
    if search_mode == "📅 Date":
        date_input = st.date_input("Pick a date to search")
        if st.button("Search by Date"):
            cursor.execute("SELECT entry_date, content, polarity, subjectivity FROM diary_entries WHERE DATE(entry_date) = ? AND user_id = ?", (date_input, st.session_state.user_id))
            entries = cursor.fetchall()
            if entries:
                for date, content, pol, subj in entries:
                    mood_score = round((pol + 1) * 5, 1)
                    thought_score = round(subj * 10, 1)
                    formatted_date = parser.parse(str(date)).strftime('%Y-%m-%d %H:%M')
                    st.markdown(f"""
                    ---
                    🗓️ **{datetime.strptime(date, '%Y-%m-%d %H:%M:?.%f').strftime('%Y-%m-%d %H:%M')}**
                    📝 *{content}*
                    😊 **Mood Score**: `{mood_score}/10`  
                    🤔 **Thought Depth**: `{thought_score}/10`
                    """)
            else:
                st.info("No entries found for that date.")
    elif search_mode == "😊 Mood":
        mood_input = st.selectbox("Choose a mood to filter by", ["Positive", "Negative", "Neutral"])
        if st.button("Search by Mood"):
            if mood_input == "Positive":
                query = "SELECT entry_date, content, polarity, subjectivity FROM diary_entries WHERE polarity > 0.2 AND user_id = ?"
            elif mood_input == "Negative":
                query = "SELECT entry_date, content, polarity, subjectivity FROM diary_entries WHERE polarity < -0.2 AND user_id = ?"
            else:
                query = "SELECT entry_date, content, polarity, subjectivity FROM diary_entries WHERE polarity BETWEEN -0.2 AND 0.2 AND user_id = ?"
            cursor.execute(query, (st.session_state.user_id,))
            entries = cursor.fetchall()
            if entries:
                for date, content, pol, subj in entries:
                    mood_score = round((pol + 1) * 5, 1)
                    thought_score = round(subj * 10, 1)
                    st.markdown(f"""
                    ---
                    🗓️ **{datetime.strptime(date, '%Y-%m-%d %H:%M:?.%f').strftime('%Y-%m-%d %H:%M')}**
                    📝 *{content}*
                    😊 **Mood Score**: `{mood_score}/10`  
                    🤔 **Thought Depth**: `{thought_score}/10`
                    """)
            else:
                st.info(f"No {mood_input.lower()} entries found.")

# 🗣️ TALK TO AI TWIN
elif menu == "🗣️ Talk to Your AI Twin":
    st.header("🗣️ Chat with Your AI Twin")
    cursor.execute("SELECT content FROM diary_entries WHERE user_id = ?", (st.session_state.user_id,))
    entries = cursor.fetchall()
    if not entries:
        st.info("You need to write some diary entries first.")
    else:
        memory = " ".join([e[0] for e in entries])
        user_input = st.text_input("You:", placeholder="Ask your AI twin anything...")
        if user_input:
            blob = TextBlob(memory + " " + user_input)
            response_sentiment = blob.sentiment.polarity
            if response_sentiment > 0.3:
                twin_reply = "That sounds lovely! You've been quite optimistic lately."
            elif response_sentiment < -0.3:
                twin_reply = "Hmm, that feels heavy. You've written quite a few deep thoughts."
            else:
                twin_reply = "Interesting... You seem thoughtful. Can you tell me more?"
            st.markdown(f"**AI Twin:** {twin_reply}")

# 📤 EXPORT ENTRIES
elif menu == "📤 Export Entries":
    st.header("📤 Export Your Diary")
    export_mode = st.radio("Choose export type:", ["All Entries", "By Date", "By Mood"])
    if export_mode == "All Entries":
        cursor.execute("SELECT entry_date, content, polarity, subjectivity FROM diary_entries WHERE user_id = ?", (st.session_state.user_id,))
        entries = cursor.fetchall()
    elif export_mode == "By Date":
        date_input = st.date_input("Pick a date")
        cursor.execute("SELECT entry_date, content, polarity, subjectivity FROM diary_entries WHERE DATE(entry_date) = ? AND user_id = ?", (date_input, st.session_state.user_id))
        entries = cursor.fetchall()
    elif export_mode == "By Mood":
        mood_input = st.selectbox("Choose mood", ["Positive", "Negative", "Neutral"])
        if mood_input == "Positive":
            query = "SELECT entry_date, content, polarity, subjectivity FROM diary_entries WHERE polarity > 0.2 AND user_id = ?"
        elif mood_input == "Negative":
            query = "SELECT entry_date, content, polarity, subjectivity FROM diary_entries WHERE polarity < -0.2 AND user_id = ?"
        else:
            query = "SELECT entry_date, content, polarity, subjectivity FROM diary_entries WHERE polarity BETWEEN -0.2 AND 0.2 AND user_id = ?"
        cursor.execute(query, (st.session_state.user_id,))
        entries = cursor.fetchall()
    if entries:
        lines = ""
        for date, content, pol, subj in entries:
            mood_score = round((pol + 1) * 5, 1)
            thought_score = round(subj * 10, 1)
            lines += f"🗓️ {datetime.strptime(date, '%Y-%m-%d %H:%M:?.%f').strftime('%Y-%m-%d %H:%M')}\n📝 {content}\n😊 Mood Score: {mood_score}/10\n🤔 Thought Depth: {thought_score}/10\n{'-'*40}\n"
        st.download_button("📥 Download Diary (.txt)", lines, "my_moments_diary.txt", "text/plain")
    else:
        st.info("❌ No entries found to export.")

# 🤖 TRAIN AI TWIN
elif menu == "🤖 Train Your AI Twin":
    st.header("🤖 Your Digital Twin Reflection")
    cursor.execute("SELECT content FROM diary_entries WHERE user_id = ?", (st.session_state.user_id,))
    entries = cursor.fetchall()
    if not entries:
        st.info("You need to write some diary entries first.")
    else:
        all_text = " ".join(entry[0] for entry in entries)
        blob = TextBlob(all_text)
        polarity = blob.sentiment.polarity
        subjectivity = blob.sentiment.subjectivity
        mood_score = round((polarity + 1) * 5, 1)
        thought_score = round(subjectivity * 10, 1)
        st.subheader("🧠 Twin Reflection")
        st.markdown(f"""
        Your digital twin reflects:

        - 😊 **Overall Mood**: `{mood_score}/10`
        - 🤔 **Thinking Style**: `{thought_score}/10`
        - 🧾 **Summary**: You tend to be {"positive" if polarity > 0.2 else "neutral" if -0.2 <= polarity <= 0.2 else "reflective"} and {"introspective" if subjectivity > 0.5 else "observant"}.
        """)

elif menu == "🗑️ Delete Entry":
    st.header("🗑️ Delete a Diary Entry")
    cursor.execute("SELECT id, entry_date, content FROM diary_entries ORDER BY entry_date DESC")
    entries = cursor.fetchall()
    if entries:
        options = [f"{entry[0]} | {entry[1]} | {entry[2][:30]}..." for entry in entries]
        selected = st.selectbox("Select an entry to delete:", options)
        if st.button("Delete Selected Entry"):
            entry_id = int(selected.split(" | ")[0])
            cursor.execute("DELETE FROM diary_entries WHERE id = ?", (entry_id,))
            conn.commit()
            st.success("✅ Entry deleted successfully.")
    else:
        st.info("No entries to delete.")



# Footer
st.markdown("---")
st.markdown("<center>🔐 Made with ❤️ by Dhruv • MyMoments © 2025</center>", unsafe_allow_html=True)
