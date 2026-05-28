import sqlite3
import json

def get_db():
    return sqlite3.connect("pv_clinic.db")

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            step TEXT,
            answers TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT,
            phone TEXT,
            username TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_session(user_id, step=None, answers=None):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    if cur.fetchone():
        if step:
            cur.execute("UPDATE users SET step = ? WHERE user_id = ?", (step, user_id))
        if answers:
            cur.execute("UPDATE users SET answers = ? WHERE user_id = ?", (json.dumps(answers), user_id))
    else:
        cur.execute("INSERT INTO users VALUES (?, ?, ?)", (user_id, step, json.dumps(answers or {})))
    conn.commit()
    conn.close()

def save_contact(user_id, name, phone, username):
    conn = get_db()
    conn.execute("INSERT INTO contacts (user_id, name, phone, username) VALUES (?, ?, ?, ?)",
                 (user_id, name, phone, username))
    conn.commit()
    conn.close()

init_db()