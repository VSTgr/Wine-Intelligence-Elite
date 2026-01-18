import streamlit as st
import sqlite3
import pandas as pd
import io
import os
import altair as alt

# 1. Ρύθμιση Σελίδας
st.set_page_config(
    page_title="Wine Intelligence Elite",
    page_icon="🍷",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CSS ΓΙΑ UI/UX ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    @media (max-width: 768px) {
        .block-container { padding: 1rem 0.7rem !important; }
        h1 { font-size: 1.6rem !important; }
        h3 { font-size: 1.2rem !important; }
    }
    .stButton>button, .stDownloadButton>button { 
        width: 100% !important; border-radius: 6px !important; height: 3.5em !important; 
        background-color: transparent !important; color: #2e7d32 !important; 
        border: 1px solid #2e7d32 !important; font-weight: bold !important;
    }
    .stButton>button:hover { background-color: #e8f5e9 !important; }
    [data-testid="stMetricLabel"] { white-space: normal !important; word-wrap: break-word !important; }
    h1 { color: #1b5e20; font-weight: 800; }
    h3 { color: #2e7d32; }
    </style>
    """, unsafe_allow_html=True)


def load_data():
    conn = sqlite3.connect('wines.db')
    df = pd.read_sql("SELECT * FROM wine_intelligence", conn)

    # Καθαρισμός των "None" για να μη φαίνονται άσχημα
    if 'notes' not in df.columns:
        df['notes'] = ""
    else:
        df['notes'] = df['notes'].fillna("")

    df['live_check'] = df['wine_name'].apply(lambda x: f"https://www.skroutz.gr/search?keyphrase={x.replace(' ', '+')}")
    df['VfM_Score'] = (df['score'] / df['best_price']) * 10
    conn.close()
    return df


def save_to_db(df):
    conn = sqlite3.connect('wines.db')
    # Κρατάμε τις σημειώσεις, αφαιρούμε μόνο τις προσωρινές στήλες
    to_save = df.drop(columns=['VfM_Score', 'live_check'], errors='ignore')
    to_save.to_sql('wine_intelligence', conn, if_exists='replace', index=False)
    conn.commit()
    conn.close()


# --- SIDEBAR ---
with st.sidebar:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=160)

    st.markdown("### 🔐 Admin Access")
    admin_password = st.text_input("Admin Key", type="password")

    st.divider()
    st.markdown("### 🎯 Φίλτρα")
    search = st.text_input("🔍 Αναζήτηση")
    cat_filter = st.multiselect("Τύπος", ["Λευκό", "Ερυθρό", "Ροζέ", "Επιδόρπιος", "Αφρώδης"],
                                default=["Λευκό", "Ερυθρό", "Ροζέ"])
    price_range = st.slider("Εύρος Τιμής (€)", 5.0, 60.0, (5.0, 20.0))
    sort_option = st.selectbox("Ταξινόμηση", ["VfM Score", "Τιμή (Αύξουσα)", "Rating"])

# --- CONTENT ---
st.title("🍷 Ας φτιάξουμε την κάβα μας...")

try:
    if 'data' not in st.session_state:
        st.session_state.data = load_data()
    df = st.session_state.data
    filt_df = df.copy()

    # Φίλτρα
    filt_df = filt_df[(filt_df['best_price'] >= price_range[0]) & (filt_df['best_price'] <= price_range[1])]
    if cat_filter: filt_df = filt_df[filt_df['category'].isin(cat_filter)]
    if search: filt_df = filt_df[filt_df['wine_name'].str.contains(search, case=False)]

    if sort_option == "VfM Score":
        filt_df = filt_df.sort_values(by="VfM_Score", ascending=False)
    elif sort_option == "Τιμή (Αύξουσα)":
        filt_df = filt_df.sort_values(by="best_price", ascending=True)
    elif sort_option == "Rating":
        filt_df = filt_df.sort_values(by="score", ascending=False)

    # --- ΤΑ ΜΕΤΡΙΚΑ ΣΟΥ (METRICS) ---
    st.write("### 🔥 Οι 4 Κορυφαίες Επιλογές")
    top_4 = filt_df.head(4)
    cols = st.columns(4)
    for i, (idx, row) in enumerate(top_4.iterrows()):
        with cols[i]:
            st.metric(label=row['wine_name'], value=f"{row['best_price']}€", delta=f"VfM: {row['VfM_Score']:.1f}")

    st.write("---")

    # --- ΓΡΑΦΗΜΑ & BUDGET OPTIMIZER ---
    c_left, c_right = st.columns([2, 1])
    with c_left:
        st.subheader("📊 Ανάλυση Value for Money")
        chart = alt.Chart(filt_df.head(10)).mark_bar(color='#81c784').encode(
            x=alt.X('VfM_Score:Q', title='VfM Index'),
            y=alt.Y('wine_name:N', sort='-x', title=None),
            tooltip=['wine_name', 'best_price', 'score']
        ).properties(height=320)
        st.altair_chart(chart, use_container_width=True)

    with c_right:
        st.subheader("💰 Budget Optimizer")
        with st.expander("Υπολογισμός Καλαθιού", expanded=True):
            user_budget = st.number_input("Budget (€)", min_value=10, value=60)
            num_bottles = st.slider("Φιάλες", 1, 8, 3)
            if st.button("Πρόταση Αγοράς"):
                opt_df = filt_df.head(num_bottles)
                st.table(opt_df[['wine_name', 'best_price']])
                st.info(f"Σύνολο: {opt_df['best_price'].sum():.2f}€")

    st.write("---")

    # --- Ο ΠΙΝΑΚΑΣ ΜΕ ΤΙΣ ΣΗΜΕΙΩΣΕΙΣ ---
    st.markdown('<p style="font-size: 22px; font-weight: bold; color: #1b5e20;">🍷 Διαχείριση Ετικετών</p>',
                unsafe_allow_html=True)
    edited_df = st.data_editor(
        filt_df, use_container_width=True, num_rows="dynamic",
        column_config={
            "id": None, "wine_name": "Ονομασία",
            "best_price": st.column_config.NumberColumn("Τιμή (€)", format="%.2f €"),
            "score": st.column_config.ProgressColumn("Rating", min_value=80, max_value=100),
            "VfM_Score": st.column_config.NumberColumn("VfM", format="%.1f", disabled=True),
            "live_check": st.column_config.LinkColumn("🛒 Skroutz", display_text="Link"),
            "notes": st.column_config.TextColumn("📝 Σημειώσεις"),
            "category": "Τύπος", "region": "Περιοχή", "shop": None, "awards": None, "url": None
        },
        column_order=["wine_name", "live_check", "best_price", "VfM_Score", "score", "notes", "category", "region"]
    )

    st.write("---")
    btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 1])

    with btn_col1:
        if admin_password == "lara":
            if st.button("💾 ΑΠΟΘΗΚΕΥΣΗ"):
                save_to_db(edited_df)
                st.session_state.data = load_data()
                st.success("✅ Ενημερώθηκε!")
        else:
            st.info("💡 Εισάγετε Admin Key για αποθήκευση.")

    with btn_col2:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            filt_df.to_excel(writer, index=False)
        st.download_button("📥 EXCEL", output.getvalue(), "Wine_Strategy.xlsx", "application/vnd.ms-excel")

    with btn_col3:
        if st.button("🔄 ΑΝΑΝΕΩΣΗ"): st.rerun()

except Exception as e:
    st.error(f"⚠️ Παρουσιάστηκε πρόβλημα: {e}")