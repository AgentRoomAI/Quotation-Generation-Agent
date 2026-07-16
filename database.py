import os
import sqlite3
from typing import List, Optional

from models import Product

DB_PATH = os.path.join(os.path.dirname(__file__), "products.db")


class DatabaseManager:
    """Manage the SQLite database for products and sample seed data."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self) -> None:
        with self.get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    sku TEXT NOT NULL UNIQUE,
                    description TEXT NOT NULL,
                    price REAL NOT NULL,
                    stock INTEGER NOT NULL,
                    gst REAL NOT NULL
                )
                """
            )
            conn.commit()
            self.seed_products()

    def seed_products(self) -> None:
        with self.get_connection() as conn:
            count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
            sample_products = [
                ("Samsung Galaxy S24", "SGS24", "Flagship Android phone with 256GB storage", 79999.00, 24, 18),
                ("Apple iPhone 15", "AIP15", "A16 chip, 128GB, dual camera", 79999.00, 18, 18),
                ("OnePlus 12", "OP12", "Snapdragon 8 Gen 3, 256GB", 64999.00, 20, 18),
                ("Xiaomi 14", "XM14", "Premium AMOLED display, 512GB", 59999.00, 22, 18),
                ("Google Pixel 8", "GPX8", "AI camera and 5G connectivity", 54999.00, 16, 18),
                ("Samsung Galaxy Z Fold6", "SGZF6", "Foldable smartphone with 12GB RAM", 149999.00, 10, 18),
                ("Apple Watch Series 10", "AW10", "Advanced health tracking smartwatch", 45999.00, 15, 18),
                ("Samsung Galaxy Watch7", "SGW7", "Bluetooth smartwatch with ECG", 32999.00, 18, 18),
                ("Noise ColorFit Pro 5", "NCP5", "Fitness smartwatch with AMOLED", 4999.00, 30, 18),
                ("Boat Storm", "BSTM", "Water-resistant Bluetooth smartwatch", 3499.00, 26, 18),
                ("Dell Inspiron 15", "DLIN15", "Core i7 laptop with 16GB RAM", 68999.00, 14, 18),
                ("HP Pavilion 14", "HPP14", "Slim laptop with Ryzen 5", 54999.00, 16, 18),
                ("Lenovo ThinkPad E14", "LTPE14", "Business laptop with 512GB SSD", 61999.00, 12, 18),
                ("Acer Aspire 7", "ACA7", "Gaming laptop with RTX 3050", 75999.00, 11, 18),
                ("Asus Vivobook 15", "ASV15", "Lightweight laptop with 8GB RAM", 49999.00, 17, 18),
                ("Apple MacBook Air M2", "MBAIRM2", "Thin and light laptop", 119999.00, 9, 18),
                ("Samsung 27-inch 4K Monitor", "SM27K", "Ultra HD monitor for creators", 34999.00, 14, 18),
                ("LG 32-inch OLED TV", "LG32O", "4K smart television", 89999.00, 8, 18),
                ("Sony Bravia 55-inch TV", "SB55", "Smart LED TV with Dolby Atmos", 79999.00, 7, 18),
                ("Bose SoundLink Mini", "BSM", "Portable Bluetooth speaker", 19999.00, 20, 18),
                ("JBL Flip 6", "JBLF6", "Waterproof portable speaker", 12999.00, 23, 18),
                ("Sony WH-1000XM5", "SWHM5", "Noise cancelling headphones", 29999.00, 13, 18),
                ("Boat Rockerz 560", "BR560", "Over-ear wireless headphones", 4999.00, 28, 18),
                ("OnePlus Buds Pro 2", "OPBP2", "TWS earbuds with ANC", 8999.00, 25, 18),
                ("Canon EOS R50", "CNR50", "Mirrorless camera with 24.2MP", 79999.00, 6, 18),
                ("Nikon Z50", "NKZ50", "Compact mirrorless camera", 74999.00, 6, 18),
                ("GoPro Hero 12", "GPH12", "Action camera with stabilization", 44999.00, 9, 18),
                ("Sony PlayStation 5", "SPS5", "Gaming console with 1TB SSD", 54999.00, 7, 18),
                ("Microsoft Xbox Series X", "MSXBX", "High-performance gaming console", 49999.00, 7, 18),
                ("Nintendo Switch OLED", "NSSW", "Hybrid gaming console", 29999.00, 10, 18),
                ("Logitech G Pro X", "LGGX", "Wired gaming headset", 10999.00, 15, 18),
                ("Razer DeathAdder V3", "RDV3", "Gaming mouse with 26K DPI", 6999.00, 18, 18),
                ("Corsair K70 Keyboard", "CRK70", "Mechanical RGB keyboard", 11999.00, 16, 18),
                ("TP-Link Archer AX73", "TPAX73", "Wi-Fi 6 router", 12999.00, 12, 18),
                ("Netgear Nighthawk RAX50", "NGRX50", "Dual-band wireless router", 15999.00, 11, 18),
                ("Amazon Echo Dot 5", "AED5", "Smart speaker with Alexa", 4999.00, 22, 18),
                ("Google Nest Hub 2", "GNH2", "Smart display with Google Assistant", 8999.00, 13, 18),
                ("Philips Hue Bulb", "PHHB", "Smart LED bulb pack", 3499.00, 20, 18),
                ("Mi Smart Band 8", "MSB8", "Fitness tracker with AMOLED", 2999.00, 25, 18),
                ("Realme Buds Air 6", "RBA6", "True wireless earbuds", 2999.00, 26, 18),
                ("Samsung Tab S9", "STS9", "Premium Android tablet", 69999.00, 9, 18),
                ("Apple iPad Air", "AIPA", "M1 chip tablet with 10.9 display", 59999.00, 8, 18),
                ("Lenovo Tab P12", "LTP12", "Media tablet with 12.7 display", 32999.00, 10, 18),
                ("Dell UltraSharp 27", "DU27", "Professional monitor for office", 27999.00, 12, 18),
                ("Canon Pixma G3000", "CPG30", "Wi-Fi all-in-one printer", 14999.00, 10, 18),
                ("Epson EcoTank L3250", "EEL325", "Ink tank printer", 16999.00, 10, 18),
                ("Brother DCP-T420W", "BDT420", "Compact multi-function printer", 13999.00, 9, 18),
                ("Anker 735 Charger", "ANK735", "GaN charger with USB-C", 4999.00, 21, 18),
                ("Belkin 3-Port Hub", "BLKHUB", "USB-C hub for laptops", 4499.00, 17, 18),
                ("SanDisk 1TB SSD", "SDSD1", "Portable SSD drive", 8999.00, 15, 18),
                ("Seagate 2TB HDD", "SG2TB", "External hard disk", 6999.00, 14, 18),
                ("Zebronics Keyboard", "ZBKB", "Compact USB keyboard", 1499.00, 28, 18),
                ("Logitech M350 Mouse", "LGM350", "Wireless mouse", 1299.00, 31, 18),
                ("Acer Predator Monitor", "APM27", "144Hz gaming monitor", 24999.00, 8, 18),
                ("BenQ GW2780", "BQGW27", "Eye-care office monitor", 12999.00, 10, 18),
                ("Sennheiser CX 400BT", "SENCX", "True wireless earbuds", 7999.00, 18, 18),
                ("Marshall Emberton", "MEB", "Portable Bluetooth speaker", 17999.00, 12, 18),
                ("Vivo V30", "VV30", "Camera-focused smartphone", 37999.00, 15, 18),
                ("Realme GT 6", "RGT6", "Performance smartphone", 35999.00, 14, 18),
                ("Nothing Phone 2", "NTH2", "Minimal smartphone design", 39999.00, 12, 18),
                ("Redmi Note 13 Pro", "RDN13", "High-value 5G phone", 24999.00, 17, 18),
                ("Motorola Edge 50", "MTE50", "Premium Android phone", 29999.00, 13, 18),
            ]
            if count >= len(sample_products):
                return
            conn.executemany(
                """
                INSERT OR IGNORE INTO products (name, sku, description, price, stock, gst)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                sample_products,
            )
            conn.commit()

    def search_products(self, query: str) -> List[Product]:
        with self.get_connection() as conn:
            rows = conn.execute(
                """
                SELECT id, name, sku, description, price, stock, gst
                FROM products
                WHERE lower(name) LIKE ? OR lower(sku) LIKE ? OR lower(description) LIKE ?
                ORDER BY name
                """,
                (f"%{query.lower()}%", f"%{query.lower()}%", f"%{query.lower()}%"),
            ).fetchall()
            return [Product(**dict(row)) for row in rows]

    def get_product_by_id(self, product_id: int) -> Optional[Product]:
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT id, name, sku, description, price, stock, gst FROM products WHERE id = ?",
                (product_id,),
            ).fetchone()
            return Product(**dict(row)) if row else None

    def list_products(self) -> List[Product]:
        with self.get_connection() as conn:
            rows = conn.execute(
                "SELECT id, name, sku, description, price, stock, gst FROM products ORDER BY name"
            ).fetchall()
            return [Product(**dict(row)) for row in rows]
