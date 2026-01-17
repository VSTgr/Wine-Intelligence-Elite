# Wine_VSt/app/scrapers/shops/jsonld_crawler.py
from __future__ import annotations
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import json
import re
import time, random
import os
import sys
import logging
from pathlib import Path
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# --- ΡΥΘΜΙΣΗ LOGGING & DB ---
log = logging.getLogger(__name__)
current_file = Path(__file__).resolve()
found_db = False
for i in range(5):
    parent = current_file.parents[i]
    if (parent / "db_manager.py").exists():
        sys.path.append(str(parent))
        found_db = True
        break
if not found_db:
    sys.path.append(r"C:\python\Wine_VSt")

try:
    from db_manager import WineDatabase

    db = WineDatabase()
    print("✅ Σύνδεση με db_manager επιτυχής!")
except ImportError:
    class DummyDB:
        def save_wine(self, data): pass


    db = DummyDB()

# --- CONSTANTS ---
BAD_HREF = re.compile(
    r"(javascript:|mailto:|tel:|#|twitter\.com|facebook\.com|instagram\.com|youtube\.com|linkedin\.com)", re.IGNORECASE)
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "el-GR,el;q=0.9,en;q=0.8",
    "Cache-Control": "max-age=0",
}


def get_session():
    s = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    s.mount("https://", HTTPAdapter(max_retries=retries))
    s.headers.update(DEFAULT_HEADERS)
    return s


def clean_text(s):
    if not s: return ""
    return " ".join(s.split())


def is_category_like_url(url: str) -> bool:
    u = url.lower()
    if "page=" in u: return True
    if "/category/" in u: return True
    if u.endswith("/krasia") or u.endswith("/krasia.html"): return True
    return False


def product_links_from_listing(soup: BeautifulSoup, base: str, max_links: int = 50) -> list[str]:
    links: set[str] = set()
    # ΕΔΩ ΕΙΝΑΙ Η ΑΝΑΒΑΘΜΙΣΗ: Προσθέσαμε πολλά νέα "κλειδιά"
    selectors = [
        ".product-thumb .image a",  # Greece & Grapes
        ".image a",
        "a.product-image",  # Kylix
        ".product-item-photo",
        "li.product a.woocommerce-LoopProduct-link",  # Cava Rokos (WooCommerce)
        ".box-image a",  # Cava Rokos style
        ".product-image-container a",  # Cava Vegera
        ".product-grid a",
        "h2.product-title a",
        ".product-title a",
        ".item-product a",
        ".product-block a.product-image"
    ]
    for sel in selectors:
        elements = soup.select(sel)
        for el in elements:
            href = el.get("href")
            if href and not BAD_HREF.search(href):
                full_url = urljoin(base, href)
                if "/blog/" not in full_url and "/wineries/" not in full_url:
                    links.add(full_url)
            if len(links) >= max_links: break
        if len(links) >= max_links: break

    if len(links) < 5:
        all_a = soup.find_all("a", href=True)
        for a in all_a:
            href = a['href']
            if BAD_HREF.search(href): continue
            if "/product/" in href or "/item/" in href or (href.endswith(".html") and len(href) > 35):
                full_url = urljoin(base, href)
                if not is_category_like_url(full_url):
                    links.add(full_url)
            if len(links) >= max_links: break
    return list(links)


def parse_product_page_html(html, url, vendor):
    soup = BeautifulSoup(html, "html.parser")
    data = {"url": url, "vendor": vendor, "name": "", "price": 0.0, "image_url": ""}
    scripts = soup.find_all("script", type="application/ld+json")
    for s in scripts:
        try:
            js = json.loads(s.string)
            if isinstance(js, list): js = js[0]
            if js.get("@type") == "Product":
                data["name"] = js.get("name")
                data["image_url"] = js.get("image")
                offers = js.get("offers")
                if isinstance(offers, dict):
                    data["price"] = offers.get("price")
                elif isinstance(offers, list) and offers:
                    data["price"] = offers[0].get("price")
                if data["name"] and data["price"]:
                    print(f"INFO: JSON-LD found: ['{data['name']}']")
                    return data
        except:
            continue

    if not data["name"]:
        h1 = soup.find("h1")
        if h1: data["name"] = clean_text(h1.text)
    if not data["price"]:
        price_selectors = [".price", ".special-price", ".regular-price", "span.amount", ".product-price",
                           ".current-price"]
        for sel in price_selectors:
            el = soup.select_one(sel)
            if el:
                txt = el.text.replace("€", "").replace(",", ".").strip()
                try:
                    clean_p = re.findall(r"\d+\.?\d*", txt)
                    if clean_p:
                        data["price"] = float(clean_p[0])
                        break
                except:
                    continue
    return data


def crawl_category(start_url, max_pages=1):
    session = get_session()
    domain = urlparse(start_url).netloc
    vendor = domain.replace("www.", "")
    print(f"INFO: → parsing category: {start_url}")
    try:
        r = session.get(start_url, timeout=15, verify=False)
        if r.status_code != 200:
            print(f"ERROR: Failed {start_url}: {r.status_code}")
            return []
        soup = BeautifulSoup(r.text, "html.parser")
        links = product_links_from_listing(soup, start_url)
        print(f"INFO: candidate product links = {len(links)}")
        all_products = []
        for link in links:
            try:
                time.sleep(random.uniform(0.5, 1.0))
                rp = session.get(link, timeout=10, verify=False)
                if rp.status_code == 200:
                    p_data = parse_product_page_html(rp.text, link, vendor)
                    p_data["shop_name"] = domain
                    if p_data["name"] and p_data["price"]:
                        all_products.append(p_data)
                        if db: db.save_wine(p_data)
            except Exception:
                pass
        return all_products
    except Exception as e:
        print(f"Critical Error: {e}")
        return []


def crawl_categories(categories_file, **kwargs):
    if not os.path.exists(categories_file):
        print(f"File not found: {categories_file}")
        return 0, ""

    with open(categories_file, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    print(f"INFO: categories loaded: {len(urls)} from {categories_file}")

    total_products = 0
    for i, url in enumerate(urls, 1):
        print(f"INFO: → processing list item {i}/{len(urls)}")
        products = crawl_category(url)
        total_products += len(products)

    print(f"\n--- Η ΑΠΟΣΤΟΛΗ ΟΛΟΚΛΗΡΩΘΗΚΕ ---")
    print(f"Βρέθηκαν και αποθηκεύτηκαν {total_products} κρασιά στη βάση δεδομένων!")
    return total_products, "wine_data.db"


if __name__ == "__main__":
    pass