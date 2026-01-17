import streamlit as st
import sqlite3
import pandas as pd
import os

# Ρύθμιση Σελίδας
st.set_page_config(page_title="Wine Intelligence Ultimate", layout="wide", page_icon="🍷")


def load_data():
    conn = sqlite3.connect('wines.db')
    df = pd.read_sql("SELECT * FROM wine_intelligence", conn)
    # Δημιουργία Live Link για Skroutz
    df['live_check'] = df['wine_name'].apply(lambda x: f"https://www.skroutz.gr/search?keyphrase={x.replace(' ', '+')}")
    # Υπολογισμός VfM Score
    df['VfM_Score'] = (df['score'] / df['best_price']) * 10
    conn.close()
    return df


def save_to_db(df):
    conn = sqlite3.connect('wines.db')
    # Αφαιρούμε τις υπολογισμένες στήλες πριν σώσουμε
    to_save = df.drop(columns=['VfM_Score', 'live_check'], errors='ignore')
    to_save.to_sql('wine_intelligence', conn, if_exists='replace', index=False)
    conn.commit()
    conn.close()


# --- ΑΡΙΣΤΕΡΗ ΣΤΗΛΗ (SIDEBAR) ---
with st.sidebar:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=150)

    st.header("🎯 Στρατηγικά Φίλτρα")
    search = st.text_input("🔍 Αναζήτηση")
    cat_filter = st.selectbox("Επιλογή Χρώματος", ["Όλα", "Λευκό", "Ερυθρό", "Ροζέ"])
    price_range = st.slider("Εύρος Τιμής (€)", 5.0, 50.0, (5.0, 25.0))

    st.write("---")
    st.header("⚖️ Ταξινόμηση")
    sort_option = st.selectbox("Ταξινόμηση βάσει:",
                               ["VfM Score (Φθίνουσα)", "Τιμή (Αύξουσα)", "Rating (Φθίνουσα)"])

    st.write("---")
    st.header("💰 BUDGET OPTIMIZER")
    user_budget = st.number_input("Διαθέσιμο Budget (€)", min_value=10, value=50)
    num_bottles = st.slider("Πλήθος Φιαλών", 1, 6, 3)
    optimize_btn = st.button("Πρόταση Αγοράς")

# --- ΚΥΡΙΩΣ ΠΕΡΙΟΧΗ ---
st.title("🍷 Wine Intelligence: Command Center")

try:
    if 'data' not in st.session_state:
        st.session_state.data = load_data()

    df = st.session_state.data

    # Εφαρμογή Φίλτρων
    filt_df = df.copy()
    filt_df = filt_df[(filt_df['best_price'] >= price_range[0]) & (filt_df['best_price'] <= price_range[1])]
    if cat_filter != "Όλα":
        filt_df = filt_df[filt_df['category'] == cat_filter]
    if search:
        filt_df = filt_df[filt_df['wine_name'].str.contains(search, case=False)]

    # Εφαρμογή Ταξινόμησης Sidebar
    if sort_option == "VfM Score (Φθίνουσα)":
        filt_df = filt_df.sort_values(by="VfM_Score", ascending=False)
    elif sort_option == "Τιμή (Αύξουσα)":
        filt_df = filt_df.sort_values(by="best_price", ascending=True)
    elif sort_option == "Rating (Φθίνουσα)":
        filt_df = filt_df.sort_values(by="score", ascending=False)

    # --- TOP 5 HIGHLIGHTS ---
    st.subheader("🔥 Κορυφαίες Επιλογές")
    top_5 = filt_df.head(5)
    cols = st.columns(5)
    for i, (idx, row) in enumerate(top_5.iterrows()):
        with cols[i]:
            st.markdown(f"**{row['wine_name']}**")
            st.metric("Τιμή", f"{row['best_price']}€", f"VfM: {row['VfM_Score']:.1f}")

    # --- BUDGET OPTIMIZER RESULT ---
    if optimize_btn:
        st.write("---")
        st.subheader("🛒 Προτεινόμενη Αγορά")
        # Παίρνουμε τα καλύτερα VfM που χωράνε στο budget
        opt_df = filt_df.sort_values(by="VfM_Score", ascending=False).head(num_bottles)
        total_cost = opt_df['best_price'].sum()
        if total_cost <= user_budget:
            st.success(f"Συνολικό Κόστος: {total_cost:.2f}€ (Εντός Budget)")
            st.table(opt_df[['wine_name', 'best_price', 'VfM_Score']])
        else:
            st.error(f"Κόστος: {total_cost:.2f}€ - Υπερβαίνει το Budget. Δοκίμασε λιγότερες φιάλες.")

    # --- DATA EDITOR ---
    st.write("---")
    st.subheader("📋 Διαχείριση Λίστας")
    edited_df = st.data_editor(
        filt_df,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "id": None,
            "wine_name": st.column_config.TextColumn("Ονομασία", width="large"),
            "best_price": st.column_config.NumberColumn("Τιμή (€)", format="%.2f €"),
            "score": st.column_config.ProgressColumn("Rating", min_value=80, max_value=100),
            "VfM_Score": st.column_config.NumberColumn("VfM", format="%.1f", disabled=True),
            "live_check": st.column_config.LinkColumn("🛒 Live Τιμή", display_text="Skroutz"),
            "url": None, "category": "Τύπος", "shop": "Κατάστημα", "region": "Περιοχή"
        },
        column_order=["wine_name", "live_check", "best_price", "VfM_Score", "score", "category", "shop"]
    )

    if st.button("💾 ΟΡΙΣΤΙΚΗ ΑΠΟΘΗΚΕΥΣΗ ΑΛΛΑΓΩΝ"):
        save_to_db(edited_df)
        st.session_state.data = load_data()
        st.success("✅ Η βάση ενημερώθηκε και κλείδωσε!")
        st.balloons()

except Exception as e:
    st.error(f"Σφάλμα: {e}")