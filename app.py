"""
Wine Intelligence Elite App.
Refactored by VST & AI for performance and maintainability.
"""

import os
import io
import pandas as pd
import altair as alt
import streamlit as st
import services  # Import the new backend service

# --- CONFIGURATION ---
st.set_page_config(
    page_title="Wine Intelligence Elite",
    page_icon="🍷",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# --- CACHING & DATA LOADING ---
@st.cache_data
def get_wine_data():
    """Wrapper για φόρτωση δεδομένων με caching."""
    return services.load_wine_data()


def clear_app_cache():
    """Καθαρίζει την cache για να δούμε τα φρέσκα δεδομένα μετά από save."""
    st.cache_data.clear()


# --- UI COMPONENTS ---
def apply_custom_css():
    """Εφαρμογή του Custom CSS."""
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
        .block-container { padding-top: 2rem; }
        </style>
        """, unsafe_allow_html=True)


def render_sidebar():
    """Δημιουργία Sidebar και επιστροφή φίλτρων."""
    with st.sidebar:
        if os.path.exists("logo.png"):
            col1, col2, col3 = st.columns([1, 2, 1])  # pylint: disable=unused-variable
            with col2:
                st.image("logo.png", width=130)

        st.markdown("""
        <div style="text-align: center; margin-bottom: 20px;">
            <h3 style="margin:0; padding:0; color: #444;">Wine Selection</h3>
            <p style="font-size: 14px; color: #888; margin:0;">Curated by VST</p>
        </div>
        """, unsafe_allow_html=True)

        # ΕΔΩ ΕΠΑΝΑΦΕΡΟΥΜΕ ΤΟ ΔΙΚΟ ΣΟΥ ΚΕΙΜΕΝΟ
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
        st.markdown("### 🎯 Κριτήρια Αναζήτησης")

        search = st.text_input("🔍 Ψάχνεις κάτι;", placeholder="π.χ. Μαλαγουζιά")
        cats = st.multiselect(
            "🍷 Χρώμα / Τύπος",
            ["Λευκό", "Ερυθρό", "Ροζέ", "Επιδόρπιος", "Αφρώδης"],
            default=["Λευκό", "Ερυθρό", "Ροζέ"]
        )
        price = st.slider("💶 Budget (€)", 5.0, 60.0, (5.0, 20.0))
        sort = st.selectbox("📊 Ταξινόμηση", ["VfM Score", "Τιμή (Αύξουσα)", "Rating"])

        st.markdown("<br><br>", unsafe_allow_html=True)
        st.divider()

        # Ανάγνωση κωδικού από τα secrets ή fallback σε κενό
        try:
            stored_pass = st.secrets["admin"]["password"]
        except (FileNotFoundError, KeyError):
            stored_pass = "admin_not_set"

        with st.expander("⚙️ Διαχείριση"):
            input_pass = st.text_input("Admin Key", type="password")

    return search, cats, price, sort, (input_pass == stored_pass)


def render_hero_section():
    """Εμφάνιση Hero Image και Τίτλων."""
    st.image(
        "https://images.unsplash.com/photo-1506377247377-2a5b3b417ebb"
        "?q=80&w=2070&auto=format&fit=crop",
        use_container_width=True
    )
    st.markdown("""
        <div style='text-align: center; padding-top: 10px;'>
            <h1 style='color: #1b5e20; margin-bottom: 0;'>🍷 Wine Intelligence Elite</h1>
            <p style='font-size: 18px; color: #555; margin-top: 5px;'>
                Ο έξυπνος τρόπος να ανακαλύπτεις διαμάντια.
            </p>
        </div>
        <hr style='margin-top: 20px; margin-bottom: 30px; border-top: 1px solid #ddd;'>
    """, unsafe_allow_html=True)


def filter_data(df, search, cats, price, sort_option):
    """Εφαρμογή φίλτρων στο DataFrame."""
    filt_df = df.copy()
    filt_df = filt_df[
        (filt_df['best_price'] >= price[0]) &
        (filt_df['best_price'] <= price[1])
        ]
    if cats:
        filt_df = filt_df[filt_df['category'].isin(cats)]
    if search:
        filt_df = filt_df[filt_df['wine_name'].str.contains(search, case=False)]

    if sort_option == "VfM Score":
        filt_df = filt_df.sort_values(by="VfM_Score", ascending=False)
    elif sort_option == "Τιμή (Αύξουσα)":
        filt_df = filt_df.sort_values(by="best_price", ascending=True)
    elif sort_option == "Rating":
        filt_df = filt_df.sort_values(by="score", ascending=False)

    return filt_df


def render_metrics(df):
    """Εμφάνιση των Top 4 καρτών."""
    st.markdown("### 🔥 Οι Top 4 Ευκαιρίες Τώρα")
    top_4 = df.head(4)
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


def render_charts_and_calculator(df):
    """Εμφάνιση γραφημάτων και υπολογιστή budget."""
    with st.expander(
            "📊 Εργαλεία Ανάλυσης & Υπολογισμός Καλαθιού",
            expanded=False
    ):
        c_left, c_right = st.columns([2, 1])

        with c_left:
            st.subheader("📈 Γράφημα Value for Money")
            chart = alt.Chart(df.head(10)).mark_bar(color='#81c784').encode(
                x=alt.X('VfM_Score:Q', title='VfM Index'),
                y=alt.Y('wine_name:N', sort='-x', title=None),
                tooltip=['wine_name', 'best_price', 'score']
            ).properties(height=320)
            st.altair_chart(chart, use_container_width=True)

        with c_right:
            st.subheader("💰 Budget Optimizer")
            user_budget = st.number_input("Διαθέσιμο ποσό (€)", min_value=10, value=60)
            num_bottles = st.slider("Επιθυμητές φιάλες", 1, 8, 3)

            if st.button("Πρόταση Αγοράς"):
                opt_df = df.head(num_bottles)
                st.dataframe(opt_df[['wine_name', 'best_price']], hide_index=True)
                total_cost = opt_df['best_price'].sum()
                if total_cost <= user_budget:
                    st.success(f"✅ Σύνολο: {total_cost:.2f}€")
                else:
                    st.error(f"❌ Σύνολο: {total_cost:.2f}€")
    st.write("---")


def main():
    """Κύρια ροή εφαρμογής."""
    apply_custom_css()

    # ΚΑΛΟΥΜΕ ΤΟ SIDEBAR ΜΙΑ ΜΟΝΟ ΦΟΡΑ
    search_term, cat_filter, price_range, sort_option, is_admin = render_sidebar()

    render_hero_section()

    # Data Handling
    df_main = get_wine_data()
    if df_main.empty:
        st.error("⚠️ Η βάση δεδομένων είναι κενή ή δεν φορτώθηκε.")
        return

    # Filtering
    filt_df = filter_data(df_main, search_term, cat_filter, price_range, sort_option)

    # Dashboard
    render_metrics(filt_df)
    render_charts_and_calculator(filt_df)

    # --- EDITOR ---
    st.markdown("### 🍷 Διαχείριση Ετικετών")

    # Διαμόρφωση στηλών
    col_config = {
        "live_check": st.column_config.LinkColumn("🛒 Skroutz", display_text="Link"),
        "best_price": st.column_config.NumberColumn("Τιμή (€)", format="%.2f €"),
        "VfM_Score": st.column_config.NumberColumn("VfM", format="%.1f", disabled=True),
        "score": st.column_config.ProgressColumn("Rating", min_value=80, max_value=100),
    }

    cols_to_show = [
        "wine_name", "live_check", "best_price",
        "VfM_Score", "score", "category", "region"
    ]
    if is_admin:
        cols_to_show.insert(5, "notes")

    # Αν δεν είναι admin, ο πίνακας είναι μόνο για ανάγνωση (disabled)
    edited_df = st.data_editor(
        filt_df,
        use_container_width=True,
        num_rows="dynamic",
        column_config=col_config,
        column_order=cols_to_show,
        disabled=not is_admin,
        key="wine_editor"
    )

    st.write("---")

    # --- ACTIONS ---
    btn1, btn2, btn3 = st.columns([1, 1, 1])

    with btn1:
        if is_admin:
            if st.button("💾 ΑΠΟΘΗΚΕΥΣΗ"):
                services.save_wine_data(edited_df)
                clear_app_cache()
                st.success("✅ Ενημερώθηκε επιτυχώς!")
                st.rerun()
        else:
            st.info("🔒 Admin Access Required for Saving")

    with btn2:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            filt_df.to_excel(writer, index=False)
        st.download_button(
            "📥 EXCEL", output.getvalue(),
            "Wine_Strategy.xlsx", "application/vnd.ms-excel"
        )

    with btn3:
        if st.button("🔄 ΑΝΑΝΕΩΣΗ"):
            clear_app_cache()
            st.rerun()


if __name__ == "__main__":
    main()
