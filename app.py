import streamlit as st
import sqlite3
import pandas as pd
import io
import altair as alt

# 1. Ρύθμιση Σελίδας & Στρατηγικό Styling
st.set_page_config(page_title="Wine Intelligence Elite", layout="wide", page_icon="🍷")

# Χρώματα: Primary Green (#2e7d32), Light Green (#e8f5e9), Neutral Gray (#f8f9fa)
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }

    /* Ενοποίηση στυλ για όλα τα κουμπιά (Outline Style) */
    .stButton>button, .stDownloadButton>button { 
        width: 100% !important; 
        border-radius: 6px !important; 
        height: 3.5em !important; 
        background-color: transparent !important; 
        color: #2e7d32 !important; 
        border: 1px solid #2e7d32 !important;
        font-size: 16px !important;
        font-weight: bold !important;
        transition: 0.3s !important;
    }

    /* Hover εφέ (Fresh Green Highlight) */
    .stButton>button:hover, .stDownloadButton>button:hover { 
        background-color: #e8f5e9 !important; 
        border: 1px solid #1b5e20 !important;
        color: #1b5e20 !important;
    }

    /* Ρύθμιση για να μην κόβονται τα ονόματα στις κάρτες (Metrics) */
    [data-testid="stMetricLabel"] {
        white-space: normal !important;
        word-wrap: break-word !important;
        overflow: visible !important;
        line-height: 1.3 !important;
        min-height: 2.6em !important;
        font-size: 15px !important;
        color: #4a4a4a !important;
    }

    [data-testid="stMetricValue"] { 
        font-size: 26px !important; 
        font-weight: bold !important; 
        color: #1b5e20 !important; 
    }

    /* Τίτλοι & Γραμματοσειρές */
    h1 { color: #1b5e20; font-weight: 800; font-size: 2.4rem !important; }
    h3 { color: #2e7d32; font-size: 1.4rem !important; }
    html, body, [class*="css"] { font-size: 16px !important; }

    /* Αφαίρεση του κόκκινου από τα error/warning αν χρειαστεί */
    .stAlert { border-radius: 10px; border: none; background-color: #e8f5e9; color: #1b5e20; }
    </style>
    """, unsafe_allow_html=True)


def load_data():
    conn = sqlite3.connect('wines.db')
    df = pd.read_sql("SELECT * FROM wine_intelligence", conn)
    # Δημιουργία Link για Skroutz
    df['live_check'] = df['wine_name'].apply(lambda x: f"https://www.skroutz.gr/search?keyphrase={x.replace(' ', '+')}")
    # Υπολογισμός VfM Score
    df['VfM_Score'] = (df['score'] / df['best_price']) * 10
    conn.close()
    return df


def save_to_db(df):
    conn = sqlite3.connect('wines.db')
    # Αφαιρούμε τις βοηθητικές στήλες πριν την αποθήκευση
    to_save = df.drop(columns=['VfM_Score', 'live_check'], errors='ignore')
    to_save.to_sql('wine_intelligence', conn, if_exists='replace', index=False)
    conn.commit()
    conn.close()


# --- SIDEBAR (ΦΙΛΤΡΑ) ---
with st.sidebar:
    st.image("logo.png", width=160)
    st.markdown("### 🎯  Φίλτρα")
    search = st.text_input("🔍 Αναζήτηση")
    cat_filter = st.multiselect("Τύπος", ["Λευκό", "Ερυθρό", "Ροζέ", "Επιδόρπιος", "Αφρώδης"],
                                default=["Λευκό", "Ερυθρό", "Ροζέ"])
    price_range = st.slider("Εύρος Τιμής (€)", 5.0, 60.0, (5.0, 20.0))
    sort_option = st.selectbox("Ταξινόμηση", ["VfM Score", "Τιμή (Αύξουσα)", "Rating"])

# --- ΚΥΡΙΩΣ ΠΕΡΙΕΧΟΜΕΝΟ ---CLS
st.title("🍷 Ας φτιάξουμε την κάβα μας...")

try:
    if 'data' not in st.session_state:
        st.session_state.data = load_data()

    df = st.session_state.data
    filt_df = df.copy()

    # Εφαρμογή Φίλτρων
    filt_df = filt_df[(filt_df['best_price'] >= price_range[0]) & (filt_df['best_price'] <= price_range[1])]
    if cat_filter: filt_df = filt_df[filt_df['category'].isin(cat_filter)]
    if search: filt_df = filt_df[filt_df['wine_name'].str.contains(search, case=False)]

    # Ταξινόμηση
    if sort_option == "VfM Score":
        filt_df = filt_df.sort_values(by="VfM_Score", ascending=False)
    elif sort_option == "Τιμή (Αύξουσα)":
        filt_df = filt_df.sort_values(by="best_price", ascending=True)
    elif sort_option == "Rating":
        filt_df = filt_df.sort_values(by="score", ascending=False)

    # --- TOP 4 CARDS (Χωρίς περικοπή ονομάτων) ---
    st.write("### 🔥 Οι 4 Κορυφαίες Επιλογές")
    top_4 = filt_df.head(4)
    cols = st.columns(4)  # ΑΛΛΑΓΗ ΣΕ 4 ΓΙΑ ΠΕΡΙΣΣΟΤΕΡΟ ΧΩΡΟ
    for i, (idx, row) in enumerate(top_4.iterrows()):
        with cols[i]:
            st.metric(
                label=row['wine_name'],  # Χωρίς [:12], δείχνει όλο το όνομα
                value=f"{row['best_price']}€",
                delta=f"VfM Index: {row['VfM_Score']:.1f}"
            )

    st.write("---")
    c_left, c_right = st.columns([2, 1])

    with c_left:
        st.subheader("📊 Ανάλυση Value for Money")
        # Γράφημα σε Fresh Green
        chart = alt.Chart(filt_df.head(10)).mark_bar(color='#81c784').encode(
            x=alt.X('VfM_Score:Q', title='VfM Index'),
            y=alt.Y('wine_name:N', sort='-x', title=None),
            tooltip=['wine_name', 'best_price', 'score']
        ).properties(height=320)
        st.altair_chart(chart, use_container_width=True)

    with c_right:
        st.subheader("💰 Budget Optimizer")
        with st.expander("Υπολογισμός Καλαθιού"):
            user_budget = st.number_input("Budget (€)", min_value=10, value=60)
            num_bottles = st.slider("Φιάλες", 1, 8, 3)
            if st.button("Πρόταση Αγοράς"):
                opt_df = filt_df.head(num_bottles)
                st.table(opt_df[['wine_name', 'best_price']])
                st.info(f"Σύνολο: {opt_df['best_price'].sum():.2f}€")

    # --- ΠΙΝΑΚΑΣ ΔΙΑΧΕΙΡΙΣΗΣ (22px Bold Green) ---
    st.write("---")
    st.markdown(
        '<p style="font-size: 22px; font-weight: bold; color: #1b5e20; margin-bottom: 5px;">🍷 Διαχείριση 210 Βραβευμένων Ετικετών</p>',
        unsafe_allow_html=True)

    edited_df = st.data_editor(
        filt_df,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "id": None, "wine_name": "Ονομασία",
            "best_price": st.column_config.NumberColumn("Τιμή (€)", format="%.2f €"),
            "score": st.column_config.ProgressColumn("Rating", min_value=80, max_value=100),
            "VfM_Score": st.column_config.NumberColumn("VfM", format="%.1f", disabled=True),
            "live_check": st.column_config.LinkColumn("🛒 Skroutz", display_text="Link"),
            "category": "Τύπος", "region": "Περιοχή", "shop": None, "awards": None, "url": None
        },
        column_order=["wine_name", "live_check", "best_price", "VfM_Score", "score", "category", "region"]
    )

    # --- ΚΟΥΜΠΙΑ ΕΝΕΡΓΕΙΩΝ (Unified Outline) ---
    st.write("---")
    btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 1])
    with btn_col1:
        if st.button("💾 ΑΠΟΘΗΚΕΥΣΗ"):
            save_to_db(edited_df)
            st.session_state.data = load_data()
            st.success("✅ Αποθηκεύτηκε!")

    with btn_col2:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            filt_df.to_excel(writer, index=False)
        st.download_button("📥 ΕΞΑΓΩΓΗ ΣΕ EXCEL", output.getvalue(), "Wine_Strategy_Elite.xlsx",
                           "application/vnd.ms-excel")

    with btn_col3:
        if st.button("🔄 ΑΝΑΝΕΩΣΗ"):
            st.rerun()

except Exception as e:
    st.error(f"⚠️ Παρουσιάστηκε πρόβλημα: {e}")