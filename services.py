"""
Backend services for Wine Intelligence Elite.
Handles database connections, data processing, and business logic.
Created by VST & AI.
"""

import sqlite3
import pandas as pd

DB_NAME = 'wines.db'


def load_wine_data():
    """
    Φορτώνει τα δεδομένα από τη βάση SQLite και υπολογίζει τα KPIs.

    Returns:
        pd.DataFrame: Το dataframe με τα κρασιά και το υπολογισμένο VfM.
    """
    try:
        # Χρήση context manager για ασφαλές κλείσιμο της σύνδεσης
        with sqlite3.connect(DB_NAME) as conn:
            data = pd.read_sql("SELECT * FROM wine_intelligence", conn)

        # 1. Καθαρισμός των "None" στις σημειώσεις
        if 'notes' not in data.columns:
            data['notes'] = ""
        else:
            data['notes'] = data['notes'].fillna("")

        # 2. Καθαρισμός Food Pairing (ΝΕΟ)
        if 'food_pairing' not in data.columns:
            data['food_pairing'] = ""
        else:
            data['food_pairing'] = data['food_pairing'].fillna("")

        # 3. Δημιουργία Link Skroutz (Vectorized operation για ταχύτητα)
        base_url = "https://www.skroutz.gr/search?keyphrase="
        data['live_check'] = base_url + data['wine_name'].str.replace(' ', '+')

        # 4. Υπολογισμός VfM Score
        data['VfM_Score'] = data.apply(
            lambda row: (row['score'] / row['best_price'] * 10)
            if row['best_price'] > 0 else 0,
            axis=1
        )

        return data

    except Exception as error:  # pylint: disable=broad-exception-caught
        print(f"Error loading data: {error}")
        return pd.DataFrame()


def save_wine_data(dataframe):
    """
    Αποθηκεύει το επεξεργασμένο dataframe πίσω στη βάση.

    Args:
        dataframe (pd.DataFrame): Το dataframe προς αποθήκευση.
    """
    if dataframe.empty:
        return

    # Αφαιρούμε τις υπολογιζόμενες στήλες (δεν αποθηκεύονται στη βάση)
    cols_to_drop = ['VfM_Score', 'live_check']
    existing_cols_to_drop = [c for c in cols_to_drop if c in dataframe.columns]

    to_save = dataframe.drop(columns=existing_cols_to_drop)

    try:
        with sqlite3.connect(DB_NAME) as conn:
            to_save.to_sql(
                'wine_intelligence', conn,
                if_exists='replace', index=False
            )
    except Exception as error:  # pylint: disable=broad-exception-caught
        print(f"Error saving data: {error}")