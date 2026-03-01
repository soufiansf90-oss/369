import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import sqlite3

# --- 1. CONFIG & THEME ---
st.set_page_config(page_title="369 Elite Pro", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0b0e14; color: #e6edf3; }
    [data-testid="stMetricValue"] { color: #00ffcc !important; font-size: 1.8rem; }
    .stTabs [data-baseweb="tab-list"] { gap: 20px; }
    .stTabs [data-baseweb="tab"] { 
        height: 50px; background-color: #161b22; border-radius: 10px; 
        color: white; padding: 0 20px; border: 1px solid #30363d;
    }
    .stTabs [aria-selected="true"] { background-color: #00ffcc !important; color: black !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATABASE ---
conn = sqlite3.connect('elite_v14.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS trades 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, pair TEXT, type TEXT, 
              pnl REAL, setup TEXT, mindset TEXT, notes TEXT)''')
conn.commit()

# --- 3. NAVIGATION (4 Tabs) ---
tabs = st.tabs(["📥 Add Trades", "📜 Trades Journal", "📊 Performance Analysis", "🧠 Psychology Analysis"])

# --- 4. DATA LOADING ---
df = pd.read_sql_query("SELECT * FROM trades", conn)

# --- TAB 1: ADD TRADES ---
with tabs[0]:
    st.header("🚀 Log New Execution")
    col_a, col_b = st.columns([1, 2])
    
    with col_a:
        # خانة مبلغ الحساب
        account_balance = st.number_input("💰 Current Account Balance ($)", value=1000.0)
        
        with st.form("add_form", clear_on_submit=True):
            date = st.date_input("Date", datetime.now())
            pair = st.text_input("Asset", "NAS100").upper()
            t_type = st.selectbox("Type", ["LONG", "SHORT"])
            pnl = st.number_input("P&L Result ($)", value=0.0)
            
            # Dynamic Strategy Logic
            existing_setups = list(df['setup'].unique()) if not df.empty else []
            use_new = st.checkbox("New Setup?")
            setup = st.text_input("Setup Name").upper() if use_new or not existing_setups else st.selectbox("Select Setup", existing_setups)
            
            mindset = st.select_slider("Mindset", ["Cool", "Anxious", "Fear", "Revenge"])
            notes = st.text_area("Trade Notes")
            
            if st.form_submit_button("Submit Trade"):
                c.execute("INSERT INTO trades (date, pair, type, pnl, setup, mindset, notes) VALUES (?,?,?,?,?,?,?)",
                          (str(date), pair, t_type, pnl, setup, mindset, notes))
                conn.commit()
                st.success("Trade Locked!")
                st.rerun()

# --- TAB 2: TRADES JOURNAL ---
with tabs[1]:
    st.header("📜 Execution History")
    if not df.empty:
        st.dataframe(df.sort_index(ascending=False), use_container_width=True)
    else:
        st.info("No trades logged yet.")

# --- TAB 3: PERFORMANCE ANALYSIS ---
with tabs[2]:
    st.header("📊 Modern Analytics")
    if not df.empty:
        # Metrics Calculation
        total_pnl = df['pnl'].sum()
        win_count = len(df[df['pnl'] > 0])
        loss_count = len(df[df['pnl'] <= 0])
        win_rate = (win_count / len(df)) * 100
        pnl_pct = (total_pnl / account_balance) * 100

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total P&L", f"${total_pnl:,.2f}")
        m2.metric("Return %", f"{pnl_pct:.2f}%")
        m3.metric("Win Rate", f"{win_rate:.1f}%")
        m4.metric("Total Executions", len(df))

        st.write("---")
        
        c1, c2 = st.columns(2)
        with c1:
            # Bar Chart: P&L per Trade
            st.subheader("📊 Profit/Loss per Trade")
            fig_bar = px.bar(df, x=df.index, y='pnl', color='pnl', 
                             color_continuous_scale=['#ff4b4b', '#00ffcc'], template="plotly_dark")
            st.plotly_chart(fig_bar, use_container_width=True)

        with c2:
            # Pie Chart: Wins vs Losses
            st.subheader("🎯 Win/Loss Ratio")
            fig_pie = px.pie(values=[win_count, loss_count], names=['Wins', 'Losses'], 
                             color_discrete_sequence=['#00ffcc', '#ff4b4b'], hole=0.5)
            st.plotly_chart(fig_pie, use_container_width=True)

        # Line Chart: Equity Growth in %
        st.subheader("📈 Account Growth (%)")
        df['cum_pnl_pct'] = (df['pnl'].cumsum() / account_balance) * 100
        fig_line = px.line(df, x=df.index, y='cum_pnl_pct', template="plotly_dark")
        fig_line.update_traces(line_color='#00ffcc', mode='lines+markers')
        st.plotly_chart(fig_line, use_container_width=True)

# --- TAB 4: PSYCHOLOGY ANALYSIS ---
with tabs[3]:
    st.header("🧠 Psychological Insights")
    if not df.empty:
        # مبيان كيبين العلاقة بين النفسية والأرباح
        fig_psych = px.box(df, x='mindset', y='pnl', color='mindset', 
                           title="P&L Distribution by Mindset", template="plotly_dark")
        st.plotly_chart(fig_psych, use_container_width=True)
        
        st.subheader("💡 Analysis")
        avg_revenge = df[df['mindset'] == 'Revenge']['pnl'].mean()
        if avg_revenge < 0:
            st.warning(f"Stop! Your 'Revenge' trades are costing you an average of ${abs(avg_revenge):.2f}")
    else:
        st.info("Log trades to analyze your mindset.")
