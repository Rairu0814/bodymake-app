import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, timedelta
from streamlit_echarts import st_echarts

# ファイル設定
DATA_FILE = "daily_nutrition_data.csv"

# データ読み込み
try:
    df = pd.read_csv(DATA_FILE)
    df["日付"] = pd.to_datetime(df["日付"]).dt.date
except FileNotFoundError:
    df = pd.DataFrame(columns=["日付", "カロリー", "タンパク質", "脂質", "炭水化物", "体重"])
    df.to_csv(DATA_FILE, index=False)

# 初期化
if "selected_date" not in st.session_state:
    st.session_state.selected_date = date.today()

# 目標値設定
st.sidebar.header("目標値設定")
targets = {
    "カロリー": st.sidebar.number_input("目標カロリー (kcal)", min_value=0, value=2000),
    "タンパク質": st.sidebar.number_input("目標タンパク質 (g)", min_value=0, value=100),
    "脂質": st.sidebar.number_input("目標脂質 (g)", min_value=0, value=60),
    "炭水化物": st.sidebar.number_input("目標炭水化物 (g)", min_value=0, value=250)
}

st.title("ボディメイク記録アプリ")

# ===== 日付選択 =====
st.subheader("表示・入力する日付を選択")
selected_date = st.date_input("日付選択", value=st.session_state.selected_date, min_value=date(2020, 1, 1))
st.session_state.selected_date = selected_date
input_date = selected_date

# ===== 入力フォーム =====
st.subheader("新しい記録を入力")
with st.form("input_form", clear_on_submit=True):
    st.markdown("### カロリー・PFC")
    inputs = {
        "カロリー": st.number_input("摂取カロリー (kcal)", min_value=0, value=None, placeholder=""),
        "タンパク質": st.number_input("摂取タンパク質 (g)", min_value=0, value=None, placeholder=""),
        "脂質": st.number_input("摂取脂質 (g)", min_value=0, value=None, placeholder=""),
        "炭水化物": st.number_input("摂取炭水化物 (g)", min_value=0, value=None, placeholder="")
    }
    st.markdown("### 体重")
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

# ===== 円形ゲージ表示 =====
def circular_gauge(label, value, target, color, value_color):
    percent = 100 if value > target else (value / target * 100 if target > 0 else 0)
    over_amount = value - target
    if over_amount > 0:
        detail_text = f"{value:.0f}/{target}\n{over_amount:.0f}over"  # ← 修正箇所
    else:
        detail_text = f"{value:.0f}/{target}\nあと{abs(over_amount):.0f}"

    option = {
        "title": {"text": label, "left": "center", "top": "0%", "textStyle": {"fontSize": 16, "color": "#FFFFFF"}},
        "series": [
            {
                "type": "gauge",
                "startAngle": 90,
                "endAngle": -270,
                "progress": {"show": True, "roundCap": True, "width": 15},
                "axisLine": {"lineStyle": {"width": 15}},
                "axisTick": {"show": False},
                "splitLine": {"show": False},
                "axisLabel": {"show": False},
                "pointer": {"show": False},
                "title": {"show": False},
                "detail": {
                    "valueAnimation": True,
                    "formatter": detail_text,
                    "offsetCenter": [0, "30%"],
                    "color": value_color,
                    "fontSize": 16
                },
                "data": [{"value": percent, "name": label}]
            }
        ]
    }
    st_echarts(option, height="200px")


st.subheader(f"{selected_date.strftime('%Y/%m/%d')} の摂取状況")
selected_row = df[df["日付"] == selected_date]

if not selected_row.empty:
    row = selected_row.iloc[0]
    circular_gauge("カロリー", row["カロリー"], targets["カロリー"], "#3B5BA5", "#66BB6A")
    col1, col2, col3 = st.columns(3)
    with col1:
        circular_gauge("タンパク質", row["タンパク質"], targets["タンパク質"], "#3B5BA5", "#EF5350")
    with col2:
        circular_gauge("脂質", row["脂質"], targets["脂質"], "#3B5BA5", "#FFD700")
    with col3:
        circular_gauge("炭水化物", row["炭水化物"], targets["炭水化物"], "#3B5BA5", "#42A5F5")
else:
    st.info("この日付の記録が見つかりません。")

# ===== 体重グラフ =====
st.subheader("体重推移")
weight_data = df.dropna(subset=["体重"])
if not weight_data.empty:
    fig = px.line(weight_data, x="日付", y="体重", markers=True)
    fig.update_layout(xaxis_title="日付", yaxis_title="体重 (kg)", yaxis_range=[0, weight_data["体重"].max() + 5])
    fig.update_xaxes(tickformat="%Y/%m/%d")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("体重データがまだありません。")

# ===== 平均表示 =====
st.subheader("摂取量の週間・月間平均")

df_weekly = df.copy()
df_weekly["週"] = pd.to_datetime(df_weekly["日付"]).apply(lambda d: (d - timedelta(days=d.weekday())).strftime("%Y-%m-%d"))
weekly_avg = df_weekly.groupby("週")[["カロリー", "タンパク質", "脂質", "炭水化物"]].mean().reset_index()

st.markdown("#### 週間平均")
st.dataframe(weekly_avg.rename(columns={"週": "週開始日"}), use_container_width=True)

monthly_avg = df.copy()
monthly_avg["月"] = pd.to_datetime(monthly_avg["日付"]).dt.to_period("M")
monthly_avg = monthly_avg.groupby("月")[["カロリー", "タンパク質", "脂質", "炭水化物"]].mean().reset_index()

st.markdown("#### 月間平均")
st.dataframe(monthly_avg.rename(columns={"月": "月(年月)"}), use_container_width=True)

# ===== 実行コマンド =====
st.code("""
cd C:\\Users\\smrrr\\Documents\\bodymake_app
streamlit run main_app.py
""")
