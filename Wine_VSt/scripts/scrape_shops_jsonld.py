import argparse
from Wine_VSt.app.scrapers.shops.jsonld_crawler import crawl_categories
from Wine_VSt.app.core.paths import CONFIG_DIR, DATA_OUT, ensure_dirs
from Wine_VSt.app.core.logging_setup import get_logger

log = get_logger(__name__)

def parse_args():
    p = argparse.ArgumentParser(
        prog="scrape_shops_jsonld",
        description="Σκανάρει vendors με JSON-LD/fallback και γράφει Excel."
    )
    p.add_argument("--config", default=str(CONFIG_DIR / "shop_categories.txt"),
                   help="μονοπάτι σε shop_categories.txt")
    p.add_argument("--out", default=str(DATA_OUT / "shops_all.xlsx"),
                   help="μονοπάτι εξόδου .xlsx")
    p.add_argument("--max-pages", type=int, default=1,
                   help="σελίδες ανά κατηγορία (default: 1)")
    p.add_argument("--max-links-per-page", type=int, default=6,
                   help="μέγιστοι product links ανά σελίδα (default: 6)")
    p.add_argument("--delay", type=float, default=0.3,
                   help="καθυστέρηση ανά αίτημα (sec)")
    p.add_argument("--deep", action="store_true",
                   help="ακολούθησε product links αν λείπει JSON-LD στο listing")

    # ΝΕΑ FLAGS για φίλτρο τιμής
    p.add_argument("--price-max", type=float, default=20.0,
                   help="ανώτατη τιμή (€). Θέσε π.χ. 35 για 35€")
    p.add_argument("--no-price-filter", action="store_true",
                   help="μην εφαρμόσεις κανένα φίλτρο τιμής")

    return p.parse_args()

if __name__ == "__main__":
    ensure_dirs()
    args = parse_args()
    eff_price = None if args.no_price_filter else args.price_max

    log.info(
        "RUN scrape_shops_jsonld | cfg=%s | out=%s | pages=%s | links=%s | delay=%.2f | deep=%s | price_max=%s",
        args.config, args.out, args.max_pages, args.max_links_per_page, args.delay, args.deep, eff_price
    )

    n, path = crawl_categories(
        args.config,
        args.out,
        max_pages=args.max_pages,
        delay=args.delay,
        deep=args.deep,
        max_links_per_page=args.max_links_per_page,
        price_max=eff_price,
    )

    log.info("DONE scrape_shops_jsonld | rows=%s | xlsx=%s", n, path)
    print("OK - rows:", n)
    print("XLSX:", path)
