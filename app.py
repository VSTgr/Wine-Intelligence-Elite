"""
Wine Intelligence Elite App.
Optimized for Pylint 10/10 score.
"""

import os
import io
import re  # Moved to top level
import pandas as pd
import altair as alt
import streamlit as st
import services

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
    """Καθαρίζει την cache."""
    st.cache_data.clear()

# --- HELPER: ΔΥΝΑΜΙΚΑ TAGS ---
def get_unique_food_tags(df):
    """Διαβάζει τη βάση και βρίσκει όλα τα ξεχωριστά φαγητά."""
    if df.empty or 'food_pairing' not in df.columns:
        return []

    unique_tags = set()
    all_text = df['food_pairing'].dropna().unique()

    for text in all_text:
        if text:
            parts = text.split(',')
            for part in parts:
                clean_tag = part.strip()
                if clean_tag:
                    unique_tags.add(clean_tag)
    return sorted(list(unique_tags))

# --- UI COMPONENTS ---
def apply_custom_css():
    """CSS μόνο για κουμπιά και layout (ΟΧΙ για την μπάρα)."""
    st.markdown("""
        <style>
        .main { background-color: #f8f9fa; }
        @media (max-width: 768px) {
            .block-container { padding: 1rem 0.7rem !important; }
            h1 { font-size: 1.6rem !important; }
        }
        /* Κουμπιά - Πράσινο Style */
        .stButton>button, .stDownloadButton>button {
            width: 100% !important; border-radius: 6px !important; height: 3.5em !important;
            background-color: transparent !important; color: #2e7d32 !important;
            border: 1px solid #2e7d32 !important; font-weight: bold !important;
        }
        .stButton>button:hover { background-color: #e8f5e9 !important; }
        </style>
        """, unsafe_allow_html=True)

def render_sidebar(df):
    """Sidebar με διορθωμένο Budget και Κείμενα."""
    with st.sidebar:
        if os.path.exists("logo.png"):
            # Χρησιμοποιούμε _ για τις μεταβλητές που δεν θέλουμε (col1, col3)
            _, col2, _ = st.columns([1, 2, 1])
            with col2:
                st.image("logo.png", width=130)

        st.markdown(
            "<h3 style='text-align: center; color: #444;'>Wine Selection</h3>",
            unsafe_allow_html=True
        )

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

        # --- ΔΥΝΑΜΙΚΟ ΦΙΛΤΡΟ ΦΑΓΗΤΟΥ ---
        available_foods = get_unique_food_tags(df)
        selected_food = st.multiselect(
            "Τι θα φάτε σήμερα;",
            options=available_foods,
            placeholder="Επιλέξτε (π.χ. Sushi, Κρέας...)"
        )
        st.caption("ℹ️ Επιλέξτε φαγητό για να δείτε προτάσεις.")
        st.markdown("---")

        search = st.text_input("Αναζήτηση", placeholder="π.χ. Μαλαγουζιά")
        cats = st.multiselect(
            "🍷 Χρώμα / Τύπος",
            ["Λευκό", "Ερυθρό", "Ροζέ", "Επιδόρπιος", "Αφρώδης"],
            default=[]
        )

        # Budget 5-20 default
        price = st.slider("Εύρος Τιμής (€)", 5.0, 60.0, (5.0, 20.0))

        sort = st.selectbox("📊 Ταξινόμηση", ["VfM Score", "Τιμή (Αύξουσα)", "Rating"])

        st.markdown("<br><br>", unsafe_allow_html=True)
        st.divider()

        # Admin
        with st.expander("⚙️ Διαχείριση"):
            input_pass = st.text_input("Admin Key", type="password")
            # Απλοποίηση χωρίς παρενθέσεις
            is_admin = input_pass == "lara"

    return search, cats, price, sort, selected_food, is_admin

def render_hero_section():
    """Εμφανίζει την κεντρική εικόνα και τον τίτλο."""
    st.image(
        "https://images.unsplash.com/photo-1506377247377-2a5b3b417ebb"
        "?auto=format&fit=crop&w=2070",
        use_container_width=True
    )
    st.markdown("""
        <div style='text-align: center; padding: 10px 0 20px 0;'>
            <h1 style='color: #1b5e20; margin:0;'>🍷 Wine Intelligence Elite</h1>
            <p style='color: #555;'>Ο έξυπνος τρόπος να ανακαλύπτεις διαμάντια.</p>
        </div>
        <hr>
    """, unsafe_allow_html=True)

# pylint: disable=too-many-arguments
def filter_data(df, search, cats, price, sort_option, food_pairing):
    """Φιλτράρει τα δεδομένα με βάση τις επιλογές του χρήστη."""
    filt_df = df.copy()
    filt_df = filt_df[
        (filt_df['best_price'] >= price[0]) &
        (filt_df['best_price'] <= price[1])
    ]

    if cats:
        filt_df = filt_df[filt_df['category'].isin(cats)]

    if search:
        filt_df = filt_df[filt_df['wine_name'].str.contains(search, case=False)]

    if food_pairing:
        safe_tags = [re.escape(tag) for tag in food_pairing]
        pattern = '|'.join(safe_tags)
        filt_df = filt_df[
            filt_df['food_pairing'].str.contains(pattern, case=False, na=False)
        ]

    if sort_option == "VfM Score":
        filt_df = filt_df.sort_values(by="VfM_Score", ascending=False)
    elif sort_option == "Τιμή (Αύξουσα)":
        filt_df = filt_df.sort_values(by="best_price", ascending=True)
    elif sort_option == "Rating":
        filt_df = filt_df.sort_values(by="score", ascending=False)

    return filt_df

def render_metrics(df):
    """Εμφανίζει τα Top 4 κρασιά."""
    st.markdown("### Προτεινόμενες Επιλογές")
    if df.empty:
        st.info("Δεν βρέθηκαν κρασιά με αυτά τα κριτήρια.")
        return

    top_4 = df.head(4)
    cols = st.columns(4)
    for i, (_, row) in enumerate(top_4.iterrows()):
        with cols[i]:
            st.metric(
                label=row['wine_name'],
                value=f"{row['best_price']}€",
                delta=f"VfM: {row['VfM_Score']:.1f}"
            )
    st.divider()

def render_charts_and_calculator(df):
    """Εμφανίζει γραφήματα και υπολογιστή καλαθιού."""
    if df.empty:
        return

    with st.expander("📊 Εργαλεία Ανάλυσης & Υπολογισμός Καλαθιού", expanded=False):
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
            st.subheader("Budget Optimizer")
            user_budget = st.number_input("Διαθέσιμο ποσό (€)", min_value=10, value=60)
            num_bottles = st.slider("Επιθυμητές φιάλες", 1, 8, 3)

            if st.button("Πρόταση Αγοράς"):
                opt_df = df.head(num_bottles)
                if not opt_df.empty:
                    st.dataframe(opt_df[['wine_name', 'best_price']], hide_index=True)
                    total_cost = opt_df['best_price'].sum()
                    if total_cost <= user_budget:
                        st.success(f"✅ Σύνολο: {total_cost:.2f}€")
                    else:
                        st.error(f"❌ Σύνολο: {total_cost:.2f}€")
                else:
                    st.warning("Δεν υπάρχουν αρκετά κρασιά.")
    st.write("---")

# pylint: disable=too-many-locals
def main():
    """Κύρια συνάρτηση εφαρμογής."""
    apply_custom_css()

    # 1. Φόρτωση
    df_main = get_wine_data()
    if df_main.empty:
        st.error("⚠️ Η βάση είναι κενή.")
        return

    # 2. Sidebar
    search, cats, price, sort, food_pairing, is_admin = render_sidebar(df_main)

    render_hero_section()

    # 3. Φίλτρα
    filt_df = filter_data(df_main, search, cats, price, sort, food_pairing)

    # 4. Dashboard
    render_metrics(filt_df)
    render_charts_and_calculator(filt_df)

    # 5. Editor
    st.markdown("### 🍷 Λίστα & Επεξεργασία")

    col_config = {
        "live_check": st.column_config.LinkColumn("🛒 Link", display_text="Skroutz"),
        "best_price": st.column_config.NumberColumn("Τιμή (€)", format="%.2f €"),
        "VfM_Score": st.column_config.NumberColumn("VfM", format="%.1f"),
        "score": st.column_config.ProgressColumn("Rating", min_value=80, max_value=100),
        "food_pairing": st.column_config.TextColumn("🍽️ Pairing Tags", width=250),
    }

    # ---------------------------------------------------------
    # ΡΥΘΜΙΣΗ ΣΕΙΡΑΣ ΣΤΗΛΩΝ
    # ---------------------------------------------------------
    cols_to_show = [
        "wine_name",      # 1. Όνομα
        "category",       # 2. Κατηγορία
        "region",         # 3. Περιοχή
        "best_price",     # 4. Τιμή
        "VfM_Score",      # 5. VfM
        "score",          # 6. Rating
        "food_pairing",   # 7. Φαγητό
        "live_check"      # 8. Link
    ]

    # Αν είσαι Admin, πρόσθεσε τις Σημειώσεις (notes)
    if is_admin:
        cols_to_show.insert(1, "notes")
    # ---------------------------------------------------------

    edited_df = st.data_editor(
        filt_df,
        use_container_width=True,
        column_config=col_config,
        column_order=cols_to_show,
        disabled=not is_admin,
        key="wine_editor",
        num_rows="dynamic"
    )

    st.divider()

    # 6. Actions
    btn1, btn2, btn3 = st.columns([1, 1, 1])

    with btn1:
        if is_admin:
            if st.button("💾 ΑΠΟΘΗΚΕΥΣΗ"):
                services.save_wine_data(edited_df)
                clear_app_cache()
                st.success("✅ Ενημερώθηκε!")
                st.rerun()
        else:
            st.info("🔒 Admin Access Required")

    with btn2:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            filt_df.to_excel(writer, index=False)
        st.download_button(
            "📥 EXCEL",
            output.getvalue(),
            "Wine_List.xlsx",
            "application/vnd.ms-excel"
        )

    with btn3:
        if st.button("🔄 ΑΝΑΝΕΩΣΗ"):
            clear_app_cache()
            st.rerun()

if __name__ == "__main__":
    main()
