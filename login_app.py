# login_app.py
import streamlit as st
import sqlite3

# === データベース設定 ===
conn = sqlite3.connect("users.db", check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY)''')

# === 固定パスワード（共有用） ===
MASTER_PASSWORD = "makebody2025"  # 必要に応じて変更可能

# === ログイン処理 ===
def login():
    st.title("ログイン")
    username = st.text_input("ユーザー名を入力")
    password = st.text_input("パスワードを入力", type="password")
    login_btn = st.button("ログイン")

    if login_btn:
        if password == MASTER_PASSWORD:
            # DBにユーザーが存在しなければ追加
            c.execute("INSERT OR IGNORE INTO users (username) VALUES (?)", (username,))
            conn.commit()
            st.session_state["username"] = username
            st.success(f"{username} でログインしました！")
            st.experimental_rerun()
        else:
            st.error("パスワードが間違っています")

# === アプリ本体呼び出し ===
def run_main_app():
    import main_app  # 別ファイルとして保存している栄養管理アプリを呼び出し

# === 実行フロー ===
if "username" not in st.session_state:
    login()
else:
    run_main_app()
