import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, timedelta
from streamlit_echarts import st_echarts
import math

# ===== ログイン処理 =====
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("#### ログイン")
    username = st.text_input("ユーザー名（任意）", label_visibility="visible")
    password = st.text_input("パスワード", type="password", label_visibility="visible")
    if st.button("ログイン"):
        if password == "bodymake2025":
            st.session_state.logged_in = True
            st.session_state.username = username.strip()
            st.rerun()
        else:
            st.error("パスワードが間違っています。")
    st.stop()

username = st.session_state.username
DATA_FILE = f"daily_nutrition_{username}.csv"

st.markdown(f"## {username}さんのボディメイク記録アプリ")

# ===== データ読み込み =====
try:
    df = pd.read_csv(DATA_FILE)
    df["日付"] = pd.to_datetime(df["日付"]).dt.date
except FileNotFoundError:
    df = pd.DataFrame(columns=["日付", "カロリー", "タンパク質", "脂質", "炭水化物", "体重"])
    df.to_csv(DATA_FILE, index=False)

# ===== 初期化 =====
if "selected_date" not in st.session_state:
    st.session_state.selected_date = date.today()

# ===== 目標自動計算 =====
with st.container():
    st.markdown("### 🧮 目標自動計算")
    col1, col2 = st.columns(2)
    with col1:
        mode = st.radio("目的", ["減量", "増量"], horizontal=True)
    with col2:
        gender = st.radio("性別", ["男性", "女性"], horizontal=True)

    if mode == "減量":
        kg = st.number_input("あと何kg減量したいですか？", min_value=0.0, step=0.1)
        days = st.number_input("あと何日で達成したいですか？", min_value=1)
        base = 2000 if gender == "男性" else 1800
        diff_per_day = (kg * 7000) / days
        intake = base - diff_per_day
        p = math.ceil(intake * 0.25 / 4)
        f = math.ceil(intake * 0.20 / 9)
        c = math.ceil(intake * 0.55 / 4)
        st.markdown(f"**1日の摂取カロリー: {int(intake)} kcal**")
        st.markdown(f"**P: {p}g　F: {f}g　C: {c}g**")
    else:
        kg = st.number_input("あと何kg増量したいですか？", min_value=0.0, step=0.1)
        days = st.number_input("あと何日で達成したいですか？", min_value=1)
        base = 2800 if gender == "男性" else 2300
        diff_per_day = (kg * 7000) / days
        intake = base + diff_per_day
        p = math.ceil(intake * 0.20 / 4)
        f = math.ceil(intake * 0.20 / 9)
        c = math.ceil(intake * 0.60 / 4)
        st.markdown(f"**1日の摂取カロリー: {int(intake)} kcal**")
        st.markdown(f"**P: {p}g　F: {f}g　C: {c}g**")

# ===== 目標値設定 =====
with st.container():
    st.markdown("### 🎯 目標値設定")
    targets = {
        "カロリー": st.number_input("目標カロリー (kcal)", min_value=0, value=2000),
        "タンパク質": st.number_input("目標タンパク質 (g)", min_value=0, value=100),
        "脂質": st.number_input("目標脂質 (g)", min_value=0, value=60),
        "炭水化物": st.number_input("目標炭水化物 (g)", min_value=0, value=250)
    }

# ===== 日付選択 =====
with st.container():
    st.markdown("### 📅 表示・入力する日付を選択")
    selected_date = st.date_input("日付選択", value=st.session_state.selected_date, min_value=date(2020, 1, 1))
    st.session_state.selected_date = selected_date
    input_date = selected_date

# ===== 入力フォーム =====
with st.form("input_form", clear_on_submit=True):
    st.markdown("### 📝 新しい記録を入力")
    st.markdown("#### カロリー・PFC")
    inputs = {
        "カロリー": st.number_input("摂取カロリー (kcal)", min_value=0, value=None, placeholder=""),
        "タンパク質": st.number_input("摂取タンパク質 (g)", min_value=0, value=None, placeholder=""),
        "脂質": st.number_input("摂取脂質 (g)", min_value=0, value=None, placeholder=""),
        "炭水化物": st.number_input("摂取炭水化物 (g)", min_value=0, value=None, placeholder="")
    }
    st.markdown("#### 体重")
    weight = st.number_input("体重 (kg)", min_value=0.0, format="%.1f", value=None, placeholder="")
    submitted = st.form_submit_button("保存")
    reset = st.form_submit_button("リセット")
    if reset:
        df = df[df["日付"] != input_date]
        df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')
        st.success("該当日のデータをリセットしました！")
    elif submitted:
        existing_row = df[df["日付"] == input_date]
        if not existing_row.empty:
            idx = existing_row.index[0]
            for key in inputs:
                if pd.notna(inputs[key]):
                    if pd.isna(df.at[idx, key]):
                        df.at[idx, key] = inputs[key]
                    else:
                        df.at[idx, key] += inputs[key]
            if not pd.isna(weight):
                df.at[idx, "体重"] = weight
        else:
            new_data = pd.DataFrame([{"日付": input_date, **inputs, "体重": weight}])
            df = pd.concat([df, new_data])
        df.drop_duplicates(subset="日付", keep="last", inplace=True)
        df.sort_values("日付", inplace=True)
        df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')
        st.success("データを保存しました！")
