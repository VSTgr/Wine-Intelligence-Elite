"""
Wine Intelligence Elite App.
Created by VST.
A Streamlit application for managing and analyzing wine prices and ratings.
"""

import os
import sqlite3
import io
import pandas as pd
import altair as alt
import streamlit as st


def load_data():
    """Φορτώνει τα δεδομένα από τη βάση SQLite και υπολογίζει τα KPIs."""
    conn = sqlite3.connect('wines.db')
    data = pd.read_sql("SELECT * FROM wine_intelligence", conn)

    # Καθαρισμός των "None" στις σημειώσεις
    if 'notes' not in data.columns:
        data['notes'] = ""
    else:
        data['notes'] = data['notes'].fillna("")

    # Δημιουργία Link Skroutz (Σπασμένο σε γραμμές για το Pylint)
    data['live_check'] = data['wine_name'].apply(
        lambda x: f"https://www.skroutz.gr/search?keyphrase={x.replace(' ', '+')}"
    )

    data['VfM_Score'] = (data['score'] / data['best_price']) * 10
    conn.close()
    return data


def save_to_db(dataframe):
    """Αποθηκεύει το επεξεργασμένο dataframe πίσω στη βάση."""
    conn = sqlite3.connect('wines.db')
    to_save = dataframe.drop(columns=['VfM_Score', 'live_check'], errors='ignore')
    to_save.to_sql('wine_intelligence', conn, if_exists='replace', index=False)
    conn.commit()
    conn.close()


def main():
    """Κύρια συνάρτηση εκτέλεσης της εφαρμογής (Main Logic)."""
    # pylint: disable=too-many-locals, too-many-branches, too-many-statements

    # 1. Ρύθμιση Σελίδας
    st.set_page_config(
        page_title="Wine Intelligence Elite",
        page_icon="🍷",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    # --- CSS ΓΙΑ UI/UX (Αισθητική) ---
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
        /* Κρύβουμε το default margin του τίτλου */
        .block-container { padding-top: 2rem; }
        </style>
        """, unsafe_allow_html=True)

    # --- SIDEBAR (PROFESSIONAL LAYOUT) ---
    with st.sidebar:
        # 1. PROFILE & BRANDING
        if os.path.exists("logo.png"):
            # Βάζουμε την εικόνα σε κύκλο (μέσω CSS, αλλά εδώ απλά κεντράρουμε)
            col1, col2, col3 = st.columns([1, 2, 1])  # pylint: disable=unused-variable
            with col2:
                st.image("logo.png", width=130)

        st.markdown("""
        <div style="text-align: center; margin-bottom: 20px;">
            <h3 style="margin:0; padding:0; color: #444;">Wine Selection</h3>
            <p style="font-size: 14px; color: #888; margin:0;">Curated by VST</p>
        </div>
        """, unsafe_allow_html=True)

        # 2. ΟΔΗΓΟΣ (Χρήσιμος για όλους)
        with st.expander("📘 Η Λογική της Επιλογής"):
            st.markdown("""
            **1. 🎯 Βάλε Στόχο:** Διάλεξε χρώμα (π.χ. *Ερυθρό*) και όρισε Budget.

            **2. 🦊 Κυνήγησε το VfM:** Ταξινόμησε με βάση το **VfM Score**.
            *Υψηλό VfM = Κορυφαίο κρασί σε τιμή ευκαιρίας.*

            **3. 🏆 Δες τους Νικητές:** Οι 4 κάρτες στην κορυφή.

            **4. 🛒 Αγόρασε Έξυπνα:** Πάτα το **Link** για το κατάστημα.

            ---
            ⚠️ **Σημείωση:**
            *Οι τιμές έχουν καταγραφεί σε συγκεκριμένη χρονική περίοδο.*
            """)

        st.divider()

        # 3. ΦΙΛΤΡΑ (Το βασικό εργαλείο)
        st.markdown("### 🎯 Κριτήρια Αναζήτησης")

        search_term = st.text_input("🔍 Ψάχνεις κάτι συγκεκριμένο;", placeholder="π.χ. Μαλαγουζιά")

        st.markdown("---")

        cat_filter = st.multiselect(
            "🍷 Χρώμα / Τύπος",
            ["Λευκό", "Ερυθρό", "Ροζέ", "Επιδόρπιος", "Αφρώδης"],
            default=["Λευκό", "Ερυθρό", "Ροζέ"]
        )

        price_range = st.slider("💶 Budget (€)", 5.0, 60.0, (5.0, 20.0))

        sort_option = st.selectbox(
            "📊 Ταξινόμηση κατά",
            ["VfM Score", "Τιμή (Αύξουσα)", "Rating"]
        )

        # Κενό για να σπρώξουμε τα admin tools κάτω
        st.markdown("<br><br>", unsafe_allow_html=True)

        # 4. ADMIN & FOOTER (Διακριτικά στο τέλος)
        st.divider()
        with st.expander("⚙️ Διαχείριση (Admin Only)"):
            admin_password = st.text_input("Admin Key", type="password", placeholder="Κωδικός...")

        st.caption("© 2024 Wine Intelligence | VSTgr")

    # --- MAIN CONTENT (Με Hero Image & Lifestyle) ---

    # 1. HERO IMAGE (Ατμόσφαιρα)
    st.image(
        "https://images.unsplash.com/photo-1506377247377-2a5b3b417ebb"
        "?q=80&w=2070&auto=format&fit=crop",
        use_container_width=True
    )

    # 2. ΤΙΤΛΟΣ & ΥΠΟΤΙΤΛΟΣ (Κεντραρισμένα)
    st.markdown("""
        <div style='text-align: center; padding-top: 10px;'>
            <h1 style='color: #1b5e20; margin-bottom: 0;'>🍷 Wine Intelligence Elite</h1>
            <p style='font-size: 18px; color: #555; margin-top: 5px;'>
                Ο έξυπνος τρόπος να ανακαλύπτεις διαμάντια, χωρίς να σπαταλάς χρήματα.
            </p>
        </div>
        <hr style='margin-top: 20px; margin-bottom: 30px; border-top: 1px solid #ddd;'>
    """, unsafe_allow_html=True)

    try:
        if 'data' not in st.session_state:
            st.session_state.data = load_data()
        df_main = st.session_state.data
        filt_df = df_main.copy()

        # Εφαρμογή Φίλτρων
        filt_df = filt_df[
            (filt_df['best_price'] >= price_range[0]) &
            (filt_df['best_price'] <= price_range[1])
        ]
        if cat_filter:
            filt_df = filt_df[filt_df['category'].isin(cat_filter)]
        if search_term:
            filt_df = filt_df[filt_df['wine_name'].str.contains(search_term, case=False)]

        # Ταξινόμηση
        if sort_option == "VfM Score":
            filt_df = filt_df.sort_values(by="VfM_Score", ascending=False)
        elif sort_option == "Τιμή (Αύξουσα)":
            filt_df = filt_df.sort_values(by="best_price", ascending=True)
        elif sort_option == "Rating":
            filt_df = filt_df.sort_values(by="score", ascending=False)

        # --- TOP 4 CARDS ---
        st.markdown("### 🔥 Οι Top 4 Ευκαιρίες Τώρα")
        top_4 = filt_df.head(4)
        cols = st.columns(4)
        for i, (_, row) in enumerate(top_4.iterrows()):
            with cols[i]:
                st.metric(
                    label=row['wine_name'],
                    value=f"{row['best_price']}€",
                    delta=f"VfM: {row['VfM_Score']:.1f}"
                )

        st.write("---")
        st.write("---")

        # --- CHARTS & BUDGET (ΠΤΥΣΣΟΜΕΝΑ ΓΙΑ ΚΑΘΑΡΗ ΕΙΚΟΝΑ) ---
        with st.expander(
            "📊 Εργαλεία Ανάλυσης & Υπολογισμός Καλαθιού (Κλικ για άνοιγμα)",
            expanded=False
        ):
            c_left, c_right = st.columns([2, 1])

            with c_left:
                st.subheader("📈 Γράφημα Value for Money")
                chart = alt.Chart(filt_df.head(10)).mark_bar(color='#81c784').encode(
                    x=alt.X('VfM_Score:Q', title='VfM Index'),
                    y=alt.Y('wine_name:N', sort='-x', title=None),
                    tooltip=['wine_name', 'best_price', 'score']
                ).properties(height=320)
                st.altair_chart(chart, use_container_width=True)

            with c_right:
                st.subheader("💰 Budget Optimizer")
                st.markdown("Βρες τον ιδανικό συνδυασμό για το budget σου.")

                user_budget = st.number_input("Διαθέσιμο ποσό (€)", min_value=10, value=60)
                num_bottles = st.slider("Επιθυμητές φιάλες", 1, 8, 3)

                if st.button("Πρόταση Αγοράς"):
                    opt_df = filt_df.head(num_bottles)
                    st.dataframe(opt_df[['wine_name', 'best_price']], hide_index=True)

                    total_cost = opt_df['best_price'].sum()
                    if total_cost <= user_budget:
                        st.success(f"✅ Σύνολο: {total_cost:.2f}€ (Εντός budget)")
                    else:
                        diff = total_cost - user_budget
                        st.error(f"❌ Σύνολο: {total_cost:.2f}€ (+ {diff:.2f}€)")

        st.write("---")

        # --- EDITOR (ΜΕ LARA LOGIC) ---
        # 1. Καθορίζουμε ποιες στήλες βλέπει ο απλός χρήστης
        cols_to_show = [
            "wine_name", "live_check", "best_price",
            "VfM_Score", "score", "category", "region"
        ]

        # 2. Αν ο κωδικός είναι "lara", εμφανίζουμε τις σημειώσεις
        if admin_password == "lara":
            cols_to_show.insert(5, "notes")

        st.markdown(
            '<p style="font-size: 22px; font-weight: bold; color: #1b5e20;">'
            '🍷 Διαχείριση Ετικετών</p>',
            unsafe_allow_html=True
        )

        edited_df = st.data_editor(
            filt_df, use_container_width=True, num_rows="dynamic",
            column_config={
                "id": None,
                "wine_name": st.column_config.TextColumn("Ονομασία", width=220),
                "live_check": st.column_config.LinkColumn(
                    "🛒 Skroutz", display_text="Link", width=90
                ),
                "best_price": st.column_config.NumberColumn(
                    "Τιμή (€)", format="%.2f €", width=100
                ),
                "VfM_Score": st.column_config.NumberColumn(
                    "VfM", format="%.1f", disabled=True, width=80
                ),
                "score": st.column_config.ProgressColumn(
                    "Rating", min_value=80, max_value=100, width=120
                ),
                "notes": st.column_config.TextColumn("📝 Σημειώσεις", width=300),
                "category": st.column_config.TextColumn("Τύπος", width=110),
                "region": st.column_config.TextColumn("Περιοχή", width=150),
                "shop": None, "awards": None, "url": None
            },
            column_order=cols_to_show
        )

        st.write("---")

        # --- SAVE BUTTONS ---
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
            st.download_button(
                "📥 EXCEL", output.getvalue(),
                "Wine_Strategy.xlsx", "application/vnd.ms-excel"
            )

        with btn_col3:
            if st.button("🔄 ΑΝΑΝΕΩΣΗ"):
                st.rerun()

    # pylint: disable=broad-exception-caught
    except Exception as e:
        st.error(f"⚠️ Παρουσιάστηκε πρόβλημα: {e}")


if __name__ == "__main__":
    main()
