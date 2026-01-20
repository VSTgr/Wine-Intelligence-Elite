"""
Ultimate Tagging Script.
Handles Greek AND English names (e.g., Xinomavro & Ξινόμαυρο).
"""

import sqlite3

DB_NAME = 'wines.db'


def ultimate_tagging():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Λίστα με κανόνες: (Tags που θέλουμε, [Λίστα λέξεων για αναζήτηση])
    rules = [
        # --- ΕΡΥΘΡΑ ---
        ("🐗 Αγριογούρουνο, 🍄 Ριζότο, 🍖 Κυνήγι", ["Ξινόμαυρο", "Xinomavro", "Naoussa", "Νάουσα", "Ramnista"]),
        ("🥘 Κοκκινιστό, 🍔 Burger, 🍝 Κιμάς", ["Αγιωργίτικο", "Agiorgitiko", "Nemea", "Νεμέα"]),
        ("🍖 BBQ, 🥓 Αλλαντικά, 🥩 Ribeye", ["Syrah", "Shiraz"]),
        ("🍗 Κοτόπουλο, 🍝 Ζυμαρικά, 🧀 Ελαφριά Τυριά", ["Merlot"]),
        ("🥩 Μπριζόλα, 🍖 Αρνί, 🧀 Παλαιωμένα Τυριά", ["Cabernet", "Cab"]),

        # --- ΛΕΥΚΑ ---
        ("🐟 Ψάρι Σχάρας, 🍋 Λεμονάτο, 🐙 Χταπόδι", ["Ασύρτικο", "Assyrtiko", "Santorini", "Σαντορίνη"]),
        ("🥗 Σαλάτες, 🍝 Pesto, 🥧 Πίτες", ["Μαλαγουζιά", "Malagousia", "Malagouzia"]),
        ("🍣 Sushi, 🥢 Ασιατικά, 🍏 Φρούτα", ["Μοσχοφίλερο", "Moschofilero", "Mantineia"]),
        ("🦞 Αστακός, 🍗 Ψητό Κοτόπουλο, 🍝 Καρμπονάρα", ["Chardonnay", "Chablis"]),
        ("🥒 Σπαράγγια, 🧀 Κατσικίσιο, 🥗 Σαλάτες", ["Sauvignon"]),
        ("🐟 Ψάρι, 🍖 Λευκό Κρέας, 🍝 Κριθαρότο", ["Vidiano", "Βιδιανό"]),
    ]

    print("🧠 Starting ULTIMATE Tagging...")
    total_updates = 0

    for tags, keywords in rules:
        # Φτιάχνουμε το SQL query δυναμικά για να ψάξει ΟΛΕΣ τις λέξεις
        # Π.χ. LIKE '%Xinomavro%' OR LIKE '%Ξινόμαυρο%'
        query_parts = [f"wine_name LIKE '%{kw}%'" for kw in keywords]
        where_clause = " OR ".join(query_parts)

        sql = f"UPDATE wine_intelligence SET food_pairing = ? WHERE {where_clause}"

        cursor.execute(sql, (tags,))
        count = cursor.rowcount

        if count > 0:
            print(f"   ✅ Updated {count} wines for keywords: {keywords}")
            total_updates += count

    conn.commit()
    conn.close()

    print("------------------------------------------------")
    print(f"🚀 ΤΕΛΟΣ! Ενημερώθηκαν συνολικά {total_updates} ετικέτες.")


if __name__ == "__main__":
    ultimate_tagging()