import os
<<<<<<< HEAD
=======
import re
>>>>>>> bc5e872 (Initial import from local workspace)
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
<<<<<<< HEAD
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
=======
    ("Samsung Galaxy S24", "SGS24", "Premium smartphone featuring 256GB storage, Dynamic AMOLED 2X display, Snapdragon processor, AI-powered camera system, and 5G connectivity. High-performance smartphone for professionals and everyday users.", 79999.00, 24, 18),

    ("Apple iPhone 15", "AIP15", "Premium smartphone powered by the A16 Bionic chip with 128GB storage, Super Retina XDR display, advanced dual-camera system, Face ID, and long battery life. Ideal smartphone for photography and productivity.", 79999.00, 18, 18),

    ("OnePlus 12", "OP12", "Flagship Android smartphone with Snapdragon 8 Gen 3 processor, 256GB storage, AMOLED display, ultra-fast charging, and smooth gaming performance. Premium smartphone for power users.", 64999.00, 20, 18),

    ("Xiaomi 14", "XM14", "Android smartphone featuring 512GB storage, Leica camera technology, AMOLED display, Snapdragon processor, and fast charging support. Premium smartphone designed for photography and entertainment.", 59999.00, 22, 18),

    ("Google Pixel 8", "GPX8", "Google smartphone with Tensor processor, AI-enhanced camera, OLED display, Android updates, and 5G connectivity. Smart smartphone for photography, productivity, and everyday communication.", 54999.00, 16, 18),

    ("Samsung Galaxy Z Fold6", "SGZF6", "Foldable smartphone featuring 12GB RAM, large AMOLED foldable display, Snapdragon processor, multitasking capabilities, and premium build quality. Innovative smartphone for business users.", 149999.00, 10, 18),

    ("Apple Watch Series 10", "AW10", "Premium smartwatch with advanced health monitoring, ECG support, GPS tracking, Retina display, fitness tracking, and seamless Apple ecosystem integration. Smartwatch for health and productivity.", 45999.00, 15, 18),

    ("Samsung Galaxy Watch7", "SGW7", "Android smartwatch featuring AMOLED display, ECG monitoring, GPS, sleep tracking, Bluetooth connectivity, and comprehensive fitness monitoring. Premium smartwatch for Android users.", 32999.00, 18, 18),

    ("Noise ColorFit Pro 5", "NCP5", "Affordable smartwatch with AMOLED display, Bluetooth calling, heart-rate monitoring, SpO2 tracking, fitness modes, and long-lasting battery life. Fitness smartwatch for daily use.", 4999.00, 30, 18),

    ("Boat Storm", "BSTM", "Budget smartwatch featuring water-resistant design, Bluetooth connectivity, heart-rate monitoring, activity tracking, smart notifications, and extended battery life. Reliable smartwatch for everyday fitness.", 3499.00, 26, 18),

    ("Dell Inspiron 15", "DLIN15", "Professional laptop powered by Intel Core i7 processor, 16GB RAM, SSD storage, Full HD display, and Windows operating system. Reliable laptop for office work, education, and productivity.", 68999.00, 14, 18),

    ("HP Pavilion 14", "HPP14", "Lightweight laptop featuring AMD Ryzen 5 processor, SSD storage, Full HD display, fast performance, and modern design. Versatile laptop suitable for students and professionals.", 54999.00, 16, 18),

    ("Lenovo ThinkPad E14", "LTPE14", "Business laptop with Intel processor, 512GB SSD, Full HD display, fingerprint security, durable ThinkPad build, and excellent keyboard. Professional laptop for enterprise use.", 61999.00, 12, 18),

    ("Acer Aspire 7", "ACA7", "Gaming laptop featuring RTX 3050 graphics, Intel processor, Full HD display, SSD storage, advanced cooling system, and smooth gaming performance. Powerful laptop for gaming and creative work.", 75999.00, 11, 18),

    ("Asus Vivobook 15", "ASV15", "Portable laptop with Intel processor, 8GB RAM, SSD storage, Full HD display, lightweight design, and long battery life. Everyday laptop for students, professionals, and home users.", 49999.00, 17, 18),
    ("Apple MacBook Air M2", "MBAIRM2", "Premium Apple laptop powered by the M2 chip, featuring a 13.6-inch Liquid Retina display, lightweight aluminum design, silent fanless cooling, and all-day battery life. Professional laptop for productivity and creativity.", 119999.00, 9, 18),

("Samsung 27-inch 4K Monitor", "SM27K", "Professional 4K monitor with a 27-inch UHD display, IPS panel, HDR support, vibrant color accuracy, and multiple connectivity options. Ideal monitor for creators and office professionals.", 34999.00, 14, 18),

("LG 32-inch OLED TV", "LG32O", "Premium smart TV featuring a 32-inch OLED display, 4K Ultra HD resolution, HDR support, webOS platform, and immersive surround sound. Smart television for home entertainment.", 89999.00, 8, 18),

("Sony Bravia 55-inch TV", "SB55", "Smart television with a 55-inch 4K LED display, Dolby Atmos audio, HDR support, Google TV platform, and advanced picture processing. Premium TV for movies and gaming.", 79999.00, 7, 18),

("Bose SoundLink Mini", "BSM", "Portable Bluetooth speaker featuring premium audio quality, deep bass, wireless connectivity, compact design, and rechargeable battery. High-quality speaker for indoor and outdoor entertainment.", 19999.00, 20, 18),

("JBL Flip 6", "JBLF6", "Portable Bluetooth speaker with waterproof IP67 design, powerful stereo sound, long battery life, USB-C charging, and rugged construction. Durable speaker for travel and outdoor use.", 12999.00, 23, 18),

("Sony WH-1000XM5", "SWHM5", "Wireless headphones with industry-leading noise cancellation, premium audio quality, Bluetooth connectivity, long battery life, and comfortable over-ear design. Flagship headphones for music lovers.", 29999.00, 13, 18),

("Boat Rockerz 560", "BR560", "Wireless over-ear headphones featuring Bluetooth connectivity, powerful bass, comfortable ear cushions, built-in microphone, and extended battery backup. Affordable headphones for entertainment.", 4999.00, 28, 18),

("OnePlus Buds Pro 2", "OPBP2", "Premium true wireless earbuds with active noise cancellation, Hi-Res audio, Bluetooth 5.3, fast charging, and immersive sound quality. Wireless earbuds for music and calls.", 8999.00, 25, 18),

("Canon EOS R50", "CNR50", "Mirrorless camera with a 24.2MP APS-C sensor, 4K video recording, Dual Pixel autofocus, lightweight body, and interchangeable lenses. Professional camera for photography and videography.", 79999.00, 6, 18),

("Nikon Z50", "NKZ50", "Compact mirrorless camera featuring a 20.9MP sensor, 4K UHD video, fast autofocus, ergonomic grip, and interchangeable lens support. Reliable camera for creators and travelers.", 74999.00, 6, 18),

("GoPro Hero 12", "GPH12", "Action camera with 5.3K video recording, HyperSmooth stabilization, waterproof design, compact body, and advanced image processing. Rugged camera for adventure and sports.", 44999.00, 9, 18),

("Sony PlayStation 5", "SPS5", "Next-generation gaming console with a custom SSD, ray tracing support, 4K gaming, DualSense controller compatibility, and ultra-fast loading performance. Premium gaming console.", 54999.00, 7, 18),

("Microsoft Xbox Series X", "MSXBX", "High-performance gaming console featuring a custom AMD processor, 1TB SSD storage, 4K gaming support, ray tracing, and Xbox Game Pass compatibility. Powerful gaming console.", 49999.00, 7, 18),

("Nintendo Switch OLED", "NSSW", "Hybrid gaming console with a vibrant OLED display, detachable Joy-Con controllers, handheld and docked gaming modes, and long battery life. Portable gaming console for all ages.", 29999.00, 10, 18),
("Logitech G Pro X", "LGGX", "Professional gaming headset featuring 7.1 surround sound, detachable Blue VO!CE microphone, comfortable memory foam ear cushions, durable aluminum frame, and crystal-clear communication. Premium gaming headset for competitive gamers.", 10999.00, 15, 18),

("Razer DeathAdder V3", "RDV3", "Gaming mouse with 26K DPI optical sensor, ergonomic lightweight design, customizable buttons, ultra-fast response time, and RGB-ready performance. Precision gaming mouse for esports and professional gaming.", 6999.00, 18, 18),

("Corsair K70 Keyboard", "CRK70", "Mechanical gaming keyboard featuring RGB backlighting, Cherry MX mechanical switches, aluminum frame, multimedia controls, and anti-ghosting technology. Premium keyboard for gaming and productivity.", 11999.00, 16, 18),

("TP-Link Archer AX73", "TPAX73", "Wi-Fi 6 router offering high-speed wireless connectivity, dual-band performance, multiple Gigabit LAN ports, advanced security, and reliable network coverage. High-performance router for homes and offices.", 12999.00, 12, 18),

("Netgear Nighthawk RAX50", "NGRX50", "Dual-band Wi-Fi 6 router featuring Gigabit Ethernet ports, advanced security features, high-speed wireless connectivity, and wide network coverage. Premium router for high-performance networking.", 15999.00, 11, 18),

("Amazon Echo Dot 5", "AED5", "Smart speaker with Alexa voice assistant, high-quality audio, smart home control, Bluetooth connectivity, Wi-Fi support, and voice command functionality. Smart speaker for home automation.", 4999.00, 22, 18),

("Google Nest Hub 2", "GNH2", "Smart display featuring Google Assistant, touchscreen display, smart home control, multimedia streaming, sleep tracking, and voice commands. Smart display for connected homes.", 8999.00, 13, 18),

("Philips Hue Bulb", "PHHB", "Smart LED bulb supporting Wi-Fi connectivity, customizable brightness, multiple color options, energy-efficient lighting, and smart home integration. Smart lighting solution for modern homes.", 3499.00, 20, 18),

("Mi Smart Band 8", "MSB8", "Fitness tracker featuring AMOLED display, heart-rate monitoring, SpO2 tracking, multiple workout modes, sleep tracking, and extended battery life. Wearable fitness tracker for active lifestyles.", 2999.00, 25, 18),

("Realme Buds Air 6", "RBA6", "True wireless earbuds with active noise cancellation, Bluetooth connectivity, immersive sound quality, low-latency gaming mode, and fast charging. Wireless earbuds for music and calls.", 2999.00, 26, 18),

("Samsung Tab S9", "STS9", "Premium Android tablet featuring a high-resolution AMOLED display, Snapdragon processor, S Pen support, long battery life, and powerful multitasking capabilities. Tablet for work, creativity, and entertainment.", 69999.00, 9, 18),

("Apple iPad Air", "AIPA", "Apple tablet powered by the M1 chip, featuring a 10.9-inch Liquid Retina display, Apple Pencil support, lightweight design, and long battery life. Premium tablet for professionals and students.", 59999.00, 8, 18),

("Lenovo Tab P12", "LTP12", "Android tablet with a 12.7-inch display, powerful processor, long battery life, multimedia speakers, and productivity features. Versatile tablet for entertainment and office work.", 32999.00, 10, 18),

("Dell UltraSharp 27", "DU27", "Professional monitor featuring a 27-inch IPS display, Full HD resolution, accurate color reproduction, ergonomic stand, and multiple connectivity ports. Office monitor for business and creative professionals.", 27999.00, 12, 18),

("Canon Pixma G3000", "CPG30", "All-in-one printer with Wi-Fi connectivity, high-yield ink tank system, color printing, scanning, copying, and cost-effective operation. Reliable printer for home and office use.", 14999.00, 10, 18),
("Epson EcoTank L3250", "EEL325", "Ink tank printer featuring Wi-Fi connectivity, high-capacity refillable ink system, color printing, scanning, copying, and low-cost printing. Efficient printer for home offices and businesses.", 16999.00, 10, 18),

("Brother DCP-T420W", "BDT420", "Compact all-in-one printer with wireless connectivity, refillable ink tank system, color printing, scanning, copying, and energy-efficient operation. Reliable printer for everyday office tasks.", 13999.00, 9, 18),

("Anker 735 Charger", "ANK735", "GaN fast charger featuring multiple USB-C ports, high-speed charging, compact portable design, intelligent power distribution, and universal device compatibility. Premium charger for smartphones and laptops.", 4999.00, 21, 18),

("Belkin 3-Port Hub", "BLKHUB", "USB-C hub with three high-speed ports, plug-and-play connectivity, compact aluminum design, data transfer support, and compatibility with laptops and tablets. Essential USB hub for productivity.", 4499.00, 17, 18),

("SanDisk 1TB SSD", "SDSD1", "Portable SSD offering 1TB storage capacity, high-speed data transfer, USB-C connectivity, durable shock-resistant design, and reliable performance. External SSD for backups and file storage.", 8999.00, 15, 18),

("Seagate 2TB HDD", "SG2TB", "External hard disk featuring 2TB storage, USB 3.0 connectivity, portable design, reliable backup performance, and plug-and-play compatibility. External HDD for secure data storage.", 6999.00, 14, 18),

("Zebronics Keyboard", "ZBKB", "Compact USB keyboard with full-size keys, plug-and-play functionality, durable construction, comfortable typing experience, and wide compatibility. Budget keyboard for home and office use.", 1499.00, 28, 18),

("Logitech M350 Mouse", "LGM350", "Wireless mouse featuring silent clicks, Bluetooth connectivity, ergonomic compact design, precise optical tracking, and long battery life. Portable mouse for productivity and travel.", 1299.00, 31, 18),

("Acer Predator Monitor", "APM27", "Gaming monitor with 144Hz refresh rate, Full HD display, low response time, vibrant color accuracy, and adaptive sync technology. High-performance monitor for competitive gaming.", 24999.00, 8, 18),

("BenQ GW2780", "BQGW27", "Office monitor featuring a 27-inch IPS display, eye-care technology, Full HD resolution, slim bezel design, and multiple connectivity options. Professional monitor for work and study.", 12999.00, 10, 18),

("Sennheiser CX 400BT", "SENCX", "True wireless earbuds with premium sound quality, Bluetooth connectivity, touch controls, long battery life, and comfortable in-ear fit. Wireless earbuds for immersive audio experiences.", 7999.00, 18, 18),

("Marshall Emberton", "MEB", "Portable Bluetooth speaker featuring signature Marshall sound, IPX7 water resistance, compact design, long battery life, and wireless music streaming. Premium speaker for indoor and outdoor entertainment.", 17999.00, 12, 18),

("Vivo V30", "VV30", "Android smartphone with advanced camera system, AMOLED display, fast charging, 5G connectivity, and sleek premium design. Mid-range smartphone for photography and everyday performance.", 37999.00, 15, 18),

("Realme GT 6", "RGT6", "Performance smartphone featuring a powerful Snapdragon processor, AMOLED display, ultra-fast charging, advanced cooling system, and 5G connectivity. Gaming smartphone for high-performance users.", 35999.00, 14, 18),

("Nothing Phone 2", "NTH2", "Android smartphone with Glyph Interface, OLED display, Snapdragon processor, dual-camera system, and clean Android experience. Premium smartphone with a unique transparent design.", 39999.00, 12, 18),
("Redmi Note 13 Pro", "RDN13", "Android smartphone featuring a 200MP camera, AMOLED display, Snapdragon processor, fast charging, and 5G connectivity. Value-for-money smartphone for photography, gaming, and daily productivity.", 24999.00, 17, 18),

("Motorola Edge 50", "MTE50", "Premium Android smartphone with pOLED display, Snapdragon processor, advanced camera system, 5G connectivity, and fast charging. Stylish smartphone for entertainment and professional use.", 29999.00, 13, 18),

("iQOO Neo 10", "IQN10", "Gaming smartphone powered by a Snapdragon processor, high refresh-rate AMOLED display, ultra-fast charging, advanced cooling system, and 5G support. High-performance smartphone for gamers.", 34999.00, 18, 18),

("Oppo Reno 13", "OPR13", "AI-powered smartphone featuring an advanced camera system, AMOLED display, fast charging, sleek design, and 5G connectivity. Premium smartphone for photography and multimedia.", 32999.00, 20, 18),

("Honor 200 Pro", "HN200P", "Flagship smartphone with a professional-grade camera, OLED display, Snapdragon processor, AI photography features, and fast charging. Premium smartphone for creators and professionals.", 44999.00, 14, 18),

("Poco X7 Pro", "PCX7P", "Performance smartphone with a flagship processor, AMOLED display, high refresh rate, fast charging, and 5G connectivity. Gaming smartphone designed for speed and efficiency.", 27999.00, 22, 18),

("Infinix GT 20 Pro", "IFGT20", "Gaming smartphone featuring an AMOLED display, powerful processor, advanced cooling technology, high refresh rate, and 5G support. Affordable smartphone for gaming enthusiasts.", 24999.00, 16, 18),

("Xiaomi Pad 7", "XMP7", "Android tablet powered by a Snapdragon processor, high-resolution display, large battery, quad speakers, and multitasking support. Premium tablet for work, learning, and entertainment.", 34999.00, 12, 18),

("OnePlus Pad 2", "OPPAD2", "Premium Android tablet with a high-refresh-rate display, flagship processor, long battery life, Dolby Atmos speakers, and fast charging. Productivity tablet for professionals and students.", 42999.00, 10, 18),

("Samsung Galaxy Tab A9+", "SGTA9", "Affordable Android tablet featuring a large display, long-lasting battery, expandable storage, stereo speakers, and smooth multitasking performance. Tablet for education and entertainment.", 22999.00, 18, 18),

("MSI Katana 15", "MSIK15", "Gaming laptop featuring Intel Core processor, NVIDIA RTX 4060 graphics, 15.6-inch Full HD display, high-speed SSD storage, and advanced cooling system. Powerful laptop for gaming and content creation.", 104999.00, 9, 18),

("Lenovo LOQ 15", "LOQ15", "Gaming laptop with Intel Core i7 processor, RTX graphics, Full HD display, SSD storage, and efficient thermal cooling. High-performance laptop for gaming and professional workloads.", 89999.00, 10, 18),

("HP Victus 15", "HPV15", "Gaming laptop equipped with RTX graphics, AMD/Intel processor, Full HD display, fast SSD storage, and enhanced cooling technology. Reliable laptop for gaming and creative applications.", 79999.00, 12, 18),

("Asus ROG Zephyrus G14", "ROGG14", "Premium gaming laptop featuring RTX graphics, AMD Ryzen processor, high-refresh-rate display, lightweight design, and advanced cooling. Flagship laptop for gaming and professional creators.", 154999.00, 7, 18),

("MacBook Pro M3", "MBPM3", "Professional Apple laptop powered by the M3 chip, Liquid Retina XDR display, all-day battery life, premium aluminum build, and exceptional performance. High-end laptop for software development, design, and video editing.", 179999.00, 6, 18),
("LG UltraGear 27", "LGUG27", "Gaming monitor featuring a 27-inch QHD display, 165Hz refresh rate, 1ms response time, IPS panel, and NVIDIA G-SYNC compatibility. Premium monitor for competitive gaming and immersive visuals.", 28999.00, 11, 18),

("Samsung Odyssey G5", "SOG5", "Curved gaming monitor with a 27-inch QHD display, 144Hz refresh rate, 1ms response time, HDR support, and AMD FreeSync Premium. High-performance monitor for smooth gaming.", 25999.00, 10, 18),

("MSI Modern Monitor", "MSIMM", "Office monitor featuring a Full HD IPS display, slim bezel design, eye-care technology, wide viewing angles, and multiple connectivity options. Professional monitor for office productivity.", 14999.00, 14, 18),

("Keychron K2", "KCK2", "Wireless mechanical keyboard with Bluetooth connectivity, hot-swappable mechanical switches, RGB backlighting, compact layout, and long battery life. Premium keyboard for programmers and professionals.", 8999.00, 18, 18),

("Redragon K552", "RDK552", "Mechanical gaming keyboard featuring RGB lighting, durable mechanical switches, anti-ghosting keys, compact tenkeyless design, and USB connectivity. Gaming keyboard for fast and accurate typing.", 3999.00, 22, 18),

("HyperX Alloy Origins", "HXAO", "Mechanical gaming keyboard with RGB backlighting, HyperX mechanical switches, aircraft-grade aluminum body, customizable lighting effects, and anti-ghosting technology. Premium gaming keyboard.", 9999.00, 16, 18),

("Logitech MX Master 3S", "MX3S", "Professional wireless mouse featuring an ergonomic design, ultra-precise optical sensor, silent clicks, USB-C charging, and multi-device connectivity. Premium mouse for productivity and creative professionals.", 9999.00, 14, 18),

("Razer Basilisk V3", "RBV3", "Gaming mouse equipped with a high-precision optical sensor, customizable RGB lighting, programmable buttons, ergonomic design, and ultra-fast response time. High-performance mouse for gamers.", 6999.00, 18, 18),

("SteelSeries Rival 3", "SSR3", "Gaming mouse featuring a TrueMove optical sensor, lightweight ergonomic design, programmable buttons, durable switches, and precise cursor control. Reliable mouse for gaming and everyday use.", 3999.00, 20, 18),

("Samsung T9 SSD 2TB", "SMT9", "Portable SSD offering 2TB storage capacity, ultra-fast USB-C data transfer, shock-resistant metal design, hardware encryption, and reliable performance. External SSD for professionals and creators.", 18999.00, 10, 18),

("WD My Passport 2TB", "WDMP2", "Portable external hard drive with 2TB storage, USB 3.2 connectivity, password protection, compact design, and automatic backup support. Reliable HDD for secure data storage.", 7999.00, 14, 18),

("Kingston NV2 1TB", "KNV2", "NVMe SSD featuring 1TB storage, PCIe Gen4 interface, high-speed read/write performance, energy-efficient design, and reliable storage technology. Internal SSD for laptops and desktops.", 6499.00, 25, 18),

("Asus RT-AX58U", "ART58", "Wi-Fi 6 router with dual-band wireless connectivity, Gigabit Ethernet ports, advanced security features, high-speed networking, and stable home coverage. Premium router for fast internet performance.", 14999.00, 12, 18),

("TP-Link Deco X20", "TPDX20", "Mesh Wi-Fi system featuring Wi-Fi 6 technology, seamless whole-home coverage, intelligent roaming, Gigabit Ethernet ports, and advanced network security. Mesh router for uninterrupted connectivity.", 18999.00, 8, 18),

("Samsung Galaxy Buds3 Pro", "SGBP3", "Premium true wireless earbuds featuring active noise cancellation, Hi-Fi sound quality, Bluetooth 5.4 connectivity, intelligent voice controls, and long battery life. Wireless earbuds for music and professional calls.", 17999.00, 12, 18),
("Nothing Ear", "NTEAR", "Premium true wireless earbuds featuring active noise cancellation, Hi-Res audio, Bluetooth 5.3 connectivity, clear voice calls, and ergonomic in-ear design. Wireless earbuds for immersive music and everyday communication.", 10999.00, 14, 18),

("Sony WF-1000XM5", "SWFXM5", "Flagship true wireless earbuds with industry-leading noise cancellation, premium audio quality, Bluetooth connectivity, adaptive sound control, and extended battery life. Professional wireless earbuds for music enthusiasts.", 22999.00, 10, 18),

("Sony SRS-XB100", "SRSXB", "Portable Bluetooth speaker featuring Extra Bass technology, IP67 water resistance, compact design, long battery life, and wireless music streaming. Rugged speaker for travel and outdoor entertainment.", 5999.00, 20, 18),

("JBL Charge 5", "JBLC5", "Portable Bluetooth speaker with powerful JBL Pro Sound, waterproof IP67 design, USB charging capability, long battery life, and durable construction. Premium speaker for indoor and outdoor use.", 14999.00, 14, 18),

("Ultimate Ears Boom 3", "UEB3", "Portable Bluetooth speaker featuring 360-degree immersive sound, waterproof and dustproof design, long battery life, wireless connectivity, and rugged durability. Premium speaker for outdoor adventures.", 12999.00, 10, 18),

("Sony Alpha A6700", "SAA67", "Mirrorless camera with APS-C sensor, advanced autofocus, 4K video recording, interchangeable lenses, and professional image quality. Premium camera for photography and content creation.", 134999.00, 5, 18),

("Canon EOS R8", "CER8", "Full-frame mirrorless camera featuring high-resolution imaging, advanced autofocus, 4K video recording, interchangeable lens support, and lightweight design. Professional camera for photographers and videographers.", 149999.00, 4, 18),

("DJI Osmo Pocket 3", "DJIOP3", "Portable vlog camera featuring 4K video recording, 3-axis gimbal stabilization, intelligent tracking, compact pocket-sized design, and touchscreen controls. Professional camera for content creators.", 54999.00, 8, 18),

("Google Chromecast 4K", "GCC4K", "Streaming media device supporting 4K HDR content, Google TV interface, Wi-Fi connectivity, voice control, and seamless media streaming. Smart streaming device for home entertainment.", 6999.00, 20, 18),

("Amazon Fire TV Stick 4K", "FTS4K", "Streaming media device featuring 4K Ultra HD playback, Alexa Voice Remote, Dolby Vision support, Wi-Fi connectivity, and access to popular streaming services. Smart streaming device for televisions.", 5999.00, 24, 18),

("Philips Smart Plug", "PSPLG", "Wi-Fi smart plug enabling remote appliance control, voice assistant compatibility, scheduling automation, energy-efficient operation, and smart home integration. Smart plug for home automation.", 2499.00, 30, 18),

("Apple MagSafe Charger", "MSAFE", "Wireless charger featuring MagSafe magnetic alignment, fast charging support, USB-C connectivity, compact design, and seamless compatibility with Apple devices. Premium wireless charger.", 4499.00, 22, 18),

("Spigen Power Bank 20000", "SPPB20", "Power bank with 20000mAh battery capacity, fast charging technology, USB-C input/output, multiple charging ports, and compact portable design. High-capacity power bank for smartphones and tablets.", 4999.00, 18, 18),

("Anker PowerCore 10000", "ANKPC", "Compact power bank featuring 10000mAh battery capacity, PowerIQ fast charging technology, lightweight portable design, USB output, and reliable charging performance. Portable power bank for everyday use.", 3499.00, 24, 18),

("DualSense Controller", "DSCTRL", "Wireless gaming controller featuring adaptive triggers, haptic feedback, ergonomic design, USB-C charging, and precise analog controls. Premium gaming controller for PlayStation gaming.", 6499.00, 20, 18),

("Xbox Wireless Controller", "XBXCTR", "Wireless gaming controller with ergonomic grip, Bluetooth connectivity, textured triggers, precise thumbsticks, and cross-platform compatibility. Premium gaming controller for Xbox and PC.", 5999.00, 18, 18),

("Nintendo Pro Controller", "NPRO", "Wireless gaming controller featuring motion controls, ergonomic grip, long battery life, Bluetooth connectivity, and responsive buttons. Premium gaming controller for Nintendo Switch.", 6999.00, 12, 18),

("HP Smart Tank 580", "HP580", "Ink tank printer featuring wireless printing, refillable ink system, high-volume color printing, scanning, copying, and low printing costs. Reliable printer for home and office productivity.", 18999.00, 9, 18),

("Canon ImageClass MF3010", "CIM3010", "Laser printer with high-speed monochrome printing, scanning, copying, compact design, and energy-efficient operation. Professional printer for office and business environments.", 16999.00, 8, 18),

("Fitbit Charge 6", "FBC6", "Fitness tracker featuring heart-rate monitoring, built-in GPS, sleep tracking, AMOLED display, activity tracking, and long battery life. Wearable fitness tracker for health-conscious users.", 15999.00, 12, 18),

("Garmin Forerunner 165", "GAR165", "GPS running watch with advanced fitness tracking, heart-rate monitoring, AMOLED display, training analytics, and long battery life. Smart sports watch for runners and athletes.", 28999.00, 8, 18),

("Huawei Watch GT5", "HWGT5", "Premium smartwatch featuring AMOLED display, comprehensive health monitoring, GPS navigation, fitness tracking, Bluetooth calling, and extended battery life. Smartwatch for fitness and everyday use.", 22999.00, 10, 18),

("D-Link 8-Port Switch", "DL8SW", "Gigabit network switch featuring eight high-speed Ethernet ports, plug-and-play setup, energy-efficient operation, durable metal housing, and reliable network performance. Network switch for offices and businesses.", 2999.00, 25, 18),

("Cisco Small Business Switch", "CSSBS", "Managed network switch with advanced network management, Gigabit Ethernet connectivity, VLAN support, enterprise-grade security, and reliable business networking performance. Professional network switch for organizations.", 15999.00, 8, 18),
]
>>>>>>> bc5e872 (Initial import from local workspace)
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
<<<<<<< HEAD
=======


BRAND_RULES = [
    ("Ultimate Ears", ["ultimate ears"]),
    ("TP-Link", ["tp-link"]),
    ("D-Link", ["d-link"]),
    ("Logitech", ["logitech"]),
    ("Samsung", ["samsung"]),
    ("Apple", ["apple"]),
    ("OnePlus", ["oneplus"]),
    ("Xiaomi", ["xiaomi"]),
    ("Google", ["google"]),
    ("Dell", ["dell"]),
    ("HP", ["hp ", "hp-", "hp"]),
    ("Lenovo", ["lenovo"]),
    ("Acer", ["acer"]),
    ("Asus", ["asus"]),
    ("Bose", ["bose"]),
    ("JBL", ["jbl"]),
    ("Sony", ["sony"]),
    ("Boat", ["boat"]),
    ("Noise", ["noise"]),
    ("Canon", ["canon"]),
    ("Nikon", ["nikon"]),
    ("GoPro", ["gopro"]),
    ("Microsoft", ["microsoft", "xbox"]),
    ("Nintendo", ["nintendo"]),
    ("Razer", ["razer"]),
    ("Corsair", ["corsair"]),
    ("Netgear", ["netgear"]),
    ("Amazon", ["amazon"]),
    ("Philips", ["philips"]),
    ("Mi", ["mi ", "mi-", "mi"]),
    ("Realme", ["realme"]),
    ("Vivo", ["vivo"]),
    ("Nothing", ["nothing"]),
    ("Redmi", ["redmi"]),
    ("Motorola", ["motorola"]),
    ("iQOO", ["iqoo"]),
    ("Oppo", ["oppo"]),
    ("Honor", ["honor"]),
    ("Poco", ["poco"]),
    ("Infinix", ["infinix"]),
    ("MSI", ["msi"]),
    ("Marshall", ["marshall"]),
    ("Belkin", ["belkin"]),
    ("SanDisk", ["sandisk"]),
    ("Seagate", ["seagate"]),
    ("Anker", ["anker"]),
    ("Spigen", ["spigen"]),
    ("Fitbit", ["fitbit"]),
    ("Garmin", ["garmin"]),
    ("Huawei", ["huawei"]),
    ("Xbox", ["xbox"]),
    ("WD", ["wd ", "wd-"]),
    ("Kingston", ["kingston"]),
    ("SteelSeries", ["steelseries"]),
    ("Keychron", ["keychron"]),
    ("Redragon", ["redragon"]),
    ("HyperX", ["hyperx"]),
    ("DJI", ["dji"]),
    ("LG", ["lg"]),
    ("BenQ", ["benq"]),
    ("Epson", ["epson"]),
    ("Brother", ["brother"]),
    ("Cisco", ["cisco"]),
]

CATEGORY_RULES = [
    ("Smartwatch", ["smartwatch", "watch series", "watch7", "watch gt", "apple watch", "galaxy watch"]),
    ("Fitness Tracker", ["fitness tracker", "smart band", "band 8", "charge 6", "forerunner"]),
    ("Laptop", ["laptop", "macbook", "thinkpad", "vivobook", "pavilion", "inspiron", "aspire", "victus", "katana", "zephyrus", "loq", "modern monitor"]),
    ("Tablet", ["tablet", "ipad", "tab s", "pad 7", "pad 2", "tab p12", "tab a9"]),
    ("Smartphone", ["smartphone", "iphone", "pixel", "galaxy s", "galaxy z", "oneplus ", "xiaomi ", "vivo ", "realme ", "nothing phone", "redmi ", "motorola ", "iqoo ", "oppo ", "honor ", "poco ", "infinix "] ),
    ("Monitor", ["monitor", "ultrasharp", "odyssey g5", "ultragear", "predator monitor", "gw2780", "modern monitor", "4k monitor"]),
    ("TV", [" tv", "television", "smart tv", "oled tv", "bravia"]),
    ("Headphones", ["headphones", "wh-1000", "boatrockerz", "rockerz"]),
    ("Earbuds", ["earbuds", "buds pro", "buds air", "wf-1000", "cx 400bt", "nothing ear", "samsung galaxy buds"]),
    ("Speaker", ["speaker", "soundlink", "flip 6", "emberton", "xb100", "charge 5", "boom 3", "echo dot", "nest hub"]),
    ("Camera", ["camera", "gopro", "alpha a6700", "eos r8", "eos r50", "z50", "osmo pocket"]),
    ("Gaming Console", ["playstation", "xbox series", "switch oled", "gaming console"]),
    ("Gaming Controller", ["controller", "dualsense", "wireless controller", "pro controller"]),
    ("Gaming Headset", ["gaming headset", "g pro x", "logitech g pro x"]),
    ("Gaming Keyboard", ["gaming keyboard", "k70", "k552", "alloy origins"]),
    ("Gaming Mouse", ["gaming mouse", "deathadder", "rival 3", "basilisk", "predator monitor"]),
    ("Keyboard", ["keyboard", "zebronics keyboard", "keychron"]),
    ("Mouse", ["mouse", "m350", "mx master"]),
    ("Printer", ["printer", "pixma", "ecotank", "dcp-t420w", "smart tank", "imageclass"]),
    ("Storage Device", ["portable hard drive", "external hard drive", "external hdd", "portable ssd", "nvme ssd", "storage"]),
    ("SSD", ["ssd", "nvme"]),
    ("HDD", ["hdd", "hard disk", "hard drive"]),
    ("Router", ["router", "mesh wi-fi", "wifi 6", "deco x20", "archer ax73", "nighthawk"]),
    ("Network Switch", ["switch", "network switch"]),
    ("Smart Home Device", ["smart home", "echo dot", "nest hub", "smart plug", "smart bulb", "chromecast"]),
    ("Streaming Device", ["chromecast", "fire tv", "streaming device", "media streaming"]),
    ("Power Bank", ["power bank", "powercore", "spigen power bank"]),
    ("Charger", ["charger", "magsafe", "gaN", "wireless charger"]),
    ("USB Hub", ["hub", "usb-c hub", "3-port hub"]),
    ("Accessory", []),
]

STOPWORDS = {
    "with", "and", "the", "for", "use", "from", "into", "this", "that", "its", "your", "high",
    "premium", "professional", "smart", "device", "featuring", "featur", "feature", "system",
    "support", "supports", "offering", "equipped", "designed", "built", "best", "ideal", "reliable",
    "portable", "wireless", "fast", "advanced", "compact", "durable", "powerful", "versatile",
}

CATEGORY_GENERIC_KEYWORDS = {
    "Laptop": ["laptop", "notebook", "windows laptop", "student laptop", "office laptop", "gaming laptop", "business laptop", "professional laptop", "ssd laptop", "full hd laptop"],
    "Smartphone": ["smartphone", "android phone", "5g phone", "camera phone", "flagship phone", "premium phone", "mobile phone"],
    "Tablet": ["tablet", "android tablet", "ipad", "stylus tablet", "media tablet", "productivity tablet"],
    "Smartwatch": ["smartwatch", "fitness smartwatch", "health watch", "bluetooth calling watch", "sports watch"],
    "Fitness Tracker": ["fitness tracker", "activity band", "health tracker", "smart band", "heart rate band"],
    "Monitor": ["monitor", "gaming monitor", "office monitor", "4k monitor", "ips monitor", "creator monitor"],
    "TV": ["tv", "smart tv", "oled tv", "4k tv", "home entertainment"],
    "Speaker": ["speaker", "bluetooth speaker", "portable speaker", "outdoor speaker"],
    "Headphones": ["headphones", "noise cancelling headphones", "wireless headphones"],
    "Earbuds": ["earbuds", "wireless earbuds", "anc earbuds", "true wireless earbuds"],
    "Camera": ["camera", "mirrorless camera", "action camera", "vlog camera", "content creation camera"],
    "Gaming Console": ["gaming console", "home console", "4k gaming", "ray tracing"],
    "Gaming Controller": ["gaming controller", "wireless controller", "console controller"],
    "Gaming Headset": ["gaming headset", "esports headset", "competitive headset"],
    "Gaming Keyboard": ["gaming keyboard", "mechanical keyboard", "rgb keyboard"],
    "Gaming Mouse": ["gaming mouse", "precision mouse", "esports mouse"],
    "Keyboard": ["keyboard", "mechanical keyboard", "usb keyboard"],
    "Mouse": ["mouse", "wireless mouse", "bluetooth mouse"],
    "Printer": ["printer", "ink tank printer", "laser printer", "all in one printer"],
    "SSD": ["ssd", "nvme ssd", "portable ssd", "external ssd"],
    "HDD": ["hdd", "portable hdd", "external hard drive"],
    "Router": ["router", "wifi 6 router", "mesh router", "dual band router"],
    "Network Switch": ["network switch", "gigabit switch", "managed switch"],
    "Smart Home Device": ["smart home", "smart speaker", "smart display", "smart bulb", "smart plug"],
    "Streaming Device": ["streaming device", "4k streaming", "media streamer"],
    "Power Bank": ["power bank", "fast charging power bank"],
    "Charger": ["charger", "fast charger", "wireless charger"],
    "USB Hub": ["usb hub", "usb-c hub"],
    "Accessory": ["accessory"],
}


def _text(value):
    return (value or "").strip()


def _lower(value):
    return _text(value).lower()


def _contains(text, phrases):
    return any(phrase in text for phrase in phrases)


def _pick_first(text, patterns, default=""):
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.I)
        if match:
            if match.groups():
                return _text(match.group(1))
            return _text(match.group(0))
    return default


def _unique(items):
    seen = set()
    output = []
    for item in items:
        normalized = item.lower() if isinstance(item, str) else item
        if normalized not in seen and item != "":
            seen.add(normalized)
            output.append(item)
    return output


def infer_brand(name):
    lowered = _lower(name)
    for brand, phrases in BRAND_RULES:
        if _contains(lowered, phrases):
            return brand
    return _text(name).split()[0] if _text(name) else ""


def infer_model(name, brand):
    name_text = _text(name)
    brand_text = _text(brand)
    if brand_text and _lower(name_text).startswith(_lower(brand_text)):
        return _text(name_text[len(brand_text):]).lstrip(" -")
    return name_text


def infer_category(name, description):
    text = _lower(f"{name} {description}")
    for category, phrases in CATEGORY_RULES:
        if _contains(text, phrases):
            return category
    return "Accessory"


def infer_usage(text):
    text = _lower(text)
    usage_rules = [
        ("gaming", ["gaming", "esports", "performance", "ray tracing"]),
        ("photography", ["camera", "photography", "video recording", "creator"]),
        ("office", ["office", "productivity", "enterprise", "business", "work"]),
        ("student", ["student", "education", "study"]),
        ("travel", ["travel", "portable", "compact", "outdoor"]),
        ("home", ["home", "household", "living room"]),
        ("professional", ["professional", "pro ", "enterprise", "creator"]),
    ]
    for usage, phrases in usage_rules:
        if _contains(text, phrases):
            return usage
    return ""


def infer_subcategory(category, name, description):
    text = _lower(f"{name} {description}")
    if category == "Laptop":
        if _contains(text, ["gaming", "rtx", "rog", "victus", "katana", "loq", "predator", "gaming laptop"]):
            return "Gaming Laptop"
        if _contains(text, ["thinkpad", "business", "enterprise"]):
            return "Business Laptop"
        if _contains(text, ["macbook", "apple laptop", "m3", "m2", "fanless"]):
            return "Premium Laptop"
        if _contains(text, ["student", "vivobook", "pavilion", "inspiron", "everyday"]):
            return "Everyday Laptop"
        return "Laptop"
    if category == "Smartphone":
        if "fold" in text:
            return "Foldable Smartphone"
        if _contains(text, ["gaming", "performance"]):
            return "Gaming Smartphone"
        if _contains(text, ["camera", "photography", "ai camera", "leica"]):
            return "Camera Smartphone"
        if _contains(text, ["flagship", "premium"]):
            return "Flagship Smartphone"
        return "Smartphone"
    if category == "Tablet":
        if "ipad" in text:
            return "Tablet"
        if "android" in text:
            return "Android Tablet"
        return "Tablet"
    if category == "Smartwatch":
        if _contains(text, ["fitness", "health", "tracking"]):
            return "Fitness Smartwatch"
        if _contains(text, ["sports", "running", "gps"]):
            return "Sports Smartwatch"
        return "Smartwatch"
    if category == "Fitness Tracker":
        return "Fitness Tracker"
    if category == "Monitor":
        if _contains(text, ["gaming", "144hz", "165hz", "1ms", "g-sync", "freesync"]):
            return "Gaming Monitor"
        if _contains(text, ["office", "productivity", "eye-care"]):
            return "Office Monitor"
        if _contains(text, ["creator", "color accuracy", "professional"]):
            return "Professional Monitor"
        return "Monitor"
    if category == "TV":
        return "Smart TV"
    if category == "Headphones":
        if _contains(text, ["noise cancellation", "noise cancelling", "anc"]):
            return "Noise Cancelling Headphones"
        return "Wireless Headphones"
    if category == "Earbuds":
        if _contains(text, ["noise cancellation", "active noise cancellation", "anc"]):
            return "ANC Earbuds"
        return "True Wireless Earbuds"
    if category == "Speaker":
        if _contains(text, ["smart speaker", "voice assistant", "alexa", "google assistant"]):
            return "Smart Speaker"
        return "Portable Bluetooth Speaker"
    if category == "Camera":
        if "action camera" in text:
            return "Action Camera"
        if "vlog" in text:
            return "Vlog Camera"
        if "mirrorless" in text:
            return "Mirrorless Camera"
        return "Camera"
    if category == "Gaming Console":
        return "Home Gaming Console"
    if category == "Gaming Controller":
        return "Wireless Gaming Controller"
    if category == "Gaming Headset":
        return "Gaming Headset"
    if category == "Gaming Keyboard":
        return "Mechanical Gaming Keyboard"
    if category == "Gaming Mouse":
        return "Gaming Mouse"
    if category == "Keyboard":
        if _contains(text, ["mechanical", "rgb", "hot-swappable", "gaming"]):
            return "Mechanical Keyboard"
        return "USB Keyboard"
    if category == "Mouse":
        if _contains(text, ["wireless", "bluetooth", "silent"]):
            return "Wireless Mouse"
        return "Mouse"
    if category == "Printer":
        if _contains(text, ["ink tank", "eco tank", "smart tank"]):
            return "Ink Tank Printer"
        if "laser" in text:
            return "Laser Printer"
        if _contains(text, ["all-in-one", "scan", "copy"]):
            return "All-in-One Printer"
        return "Printer"
    if category == "Storage Device":
        if "ssd" in text:
            return "Portable SSD"
        return "External HDD"
    if category == "SSD":
        if _contains(text, ["nvme", "pcie", "internal"]):
            return "NVMe SSD"
        return "Portable SSD"
    if category == "HDD":
        return "External HDD"
    if category == "Router":
        if _contains(text, ["mesh"]):
            return "Mesh Wi-Fi Router"
        if _contains(text, ["wifi 6", "wi-fi 6"]):
            return "Wi-Fi 6 Router"
        return "Dual-Band Router"
    if category == "Network Switch":
        if "managed" in text:
            return "Managed Network Switch"
        return "Gigabit Network Switch"
    if category == "Smart Home Device":
        if _contains(text, ["bulb"]):
            return "Smart Lighting"
        if _contains(text, ["plug"]):
            return "Smart Plug"
        if _contains(text, ["display"]):
            return "Smart Display"
        if _contains(text, ["speaker", "dot"]):
            return "Smart Speaker"
        return "Smart Home Device"
    if category == "Streaming Device":
        return "4K Streaming Device"
    if category == "Power Bank":
        return "Fast Charging Power Bank"
    if category == "Charger":
        if "wireless" in text or "magsafe" in text:
            return "Wireless Charger"
        return "Fast Charger"
    if category == "USB Hub":
        return "USB-C Hub"
    return category


def infer_processor(text):
    patterns = [
        r"\b(Intel Core i[3579](?:-\w+)?)\b",
        r"\b(AMD Ryzen [3579](?:\s*[0-9A-Za-z-]+)?)\b",
        r"\b(Ryzen [3579](?:\s*[0-9A-Za-z-]+)?)\b",
        r"\b(Snapdragon [0-9A-Za-z ]+?)\b",
        r"\b(Tensor(?: [0-9A-Za-z]+)?)\b",
        r"\b(A16 Bionic)\b",
        r"\b(M1|M2|M3)\b",
        r"\b(Intel processor)\b",
        r"\b(AMD processor)\b",
    ]
    return _pick_first(text, patterns, "")


def infer_ram(text):
    return _pick_first(text, [r"\b(\d+\s*GB\s*RAM)\b", r"\b(\d+\s*GB)\s*RAM\b", r"\b(\d+\s*GB)\b"], "")


def infer_storage(text):
    return _pick_first(
        text,
        [
            r"\b(\d+\s*TB\s*(?:SSD|HDD|storage|drive)?)\b",
            r"\b(\d+\s*GB\s*(?:SSD|HDD|storage|drive)?)\b",
            r"\b(512GB SSD)\b",
            r"\b(256GB storage)\b",
            r"\b(128GB storage)\b",
            r"\b(1TB SSD)\b",
            r"\b(2TB SSD)\b",
            r"\b(2TB HDD)\b",
            r"\b(1TB HDD)\b",
            r"\b(SSD storage)\b",
            r"\b(HDD storage)\b",
        ],
        "",
    )


def infer_graphics(text):
    return _pick_first(
        text,
        [
            r"\b((?:NVIDIA|AMD)?\s*RTX\s*\d{3,4})\b",
            r"\b(Integrated Graphics)\b",
            r"\b(Radeon Graphics)\b",
            r"\b(Adreno)\b",
        ],
        "",
    )


def infer_display_size(text):
    return _pick_first(text, [r"\b(\d+(?:\.\d+)?\s*(?:-\s*inch|inch|inches))\b"], "")


def infer_display_type(text):
    display_types = [
        "Dynamic AMOLED 2X",
        "AMOLED",
        "OLED",
        "Liquid Retina XDR",
        "Liquid Retina",
        "Retina",
        "IPS",
        "pOLED",
        "QLED",
        "LCD",
        "LED",
    ]
    for item in display_types:
        if item.lower() in text.lower():
            return item
    return ""


def infer_resolution(text):
    resolutions = ["5.3K", "5K", "4K UHD", "4K Ultra HD", "4K", "QHD", "UHD", "FHD", "Full HD", "1080p"]
    for item in resolutions:
        if item.lower() in text.lower():
            return item
    return ""


def infer_refresh_rate(text):
    return _pick_first(text, [r"\b(\d{2,3}\s*Hz)\b"], "")


def infer_camera(text):
    return _pick_first(
        text,
        [
            r"\b(\d+(?:\.\d+)?MP(?:\s*[A-Za-z0-9.-]+)?)\b",
            r"\b(dual-camera system)\b",
            r"\b(advanced camera system)\b",
            r"\b(AI-powered camera system)\b",
            r"\b(AI-enhanced camera)\b",
            r"\b(4K video recording)\b",
            r"\b(5.3K video recording)\b",
            r"\b(24\.2MP APS-C sensor)\b",
            r"\b(20\.9MP sensor)\b",
        ],
        "",
    )


def infer_battery(text):
    return _pick_first(
        text,
        [
            r"\b(\d+\s*mAh)\b",
            r"\b(all-day battery life)\b",
            r"\b(long battery life)\b",
            r"\b(extended battery life)\b",
            r"\b(rechargeable battery)\b",
            r"\b(ultra-fast charging)\b",
            r"\b(fast charging)\b",
        ],
        "",
    )


def infer_operating_system(text):
    os_rules = [
        "Windows",
        "macOS",
        "Android",
        "iOS",
        "iPadOS",
        "Wear OS",
        "webOS",
        "Google TV",
        "Fire OS",
    ]
    for item in os_rules:
        if item.lower() in text.lower():
            return item
    return ""


def infer_connectivity(text):
    text = text.lower()
    rules = [
        ("WiFi 6", ["wi-fi 6", "wifi 6"]),
        ("Wi-Fi", ["wi-fi", "wifi"]),
        ("Bluetooth 5.4", ["bluetooth 5.4"]),
        ("Bluetooth 5.3", ["bluetooth 5.3"]),
        ("Bluetooth 5.0", ["bluetooth 5.0"]),
        ("Bluetooth", ["bluetooth"]),
        ("USB-C", ["usb-c"]),
        ("USB 3.2", ["usb 3.2"]),
        ("USB 3.0", ["usb 3.0"]),
        ("HDMI", ["hdmi"]),
        ("Ethernet", ["ethernet", "gigabit ethernet"]),
        ("5G", ["5g"]),
        ("GPS", ["gps"]),
    ]
    result = []
    for label, phrases in rules:
        if _contains(text, phrases):
            result.append(label)
    return _unique(result)


def infer_voice_assistant(text):
    for item in ["Alexa", "Google Assistant", "Siri"]:
        if item.lower() in text.lower():
            return item
    return ""


def infer_features(category, text):
    text = text.lower()
    features = []
    feature_rules = [
        ("AI Camera", ["ai-powered camera", "ai-enhanced camera", "ai camera", "ai photography"]),
        ("Fast Charging", ["fast charging", "ultra-fast charging"]),
        ("Wireless Charging", ["wireless charging", "magsafe"]),
        ("Bluetooth Calling", ["bluetooth calling"]),
        ("Bluetooth 5.4", ["bluetooth 5.4"]),
        ("Bluetooth 5.3", ["bluetooth 5.3"]),
        ("WiFi 6", ["wi-fi 6", "wifi 6"]),
        ("5G", ["5g"]),
        ("HDR", ["hdr"]),
        ("RGB", ["rgb"]),
        ("Mechanical", ["mechanical"]),
        ("Backlit", ["backlit", "backlighting"]),
        ("ANC", ["active noise cancellation", "noise cancellation", "anc"]),
        ("Touch Control", ["touch control", "touch controls"]),
        ("GPS", ["gps"]),
        ("Heart Rate", ["heart-rate", "heart rate"]),
        ("Sleep Tracking", ["sleep tracking"]),
        ("Water Resistant", ["water-resistant", "waterproof", "ip67", "ipx7"]),
        ("Face ID", ["face id"]),
        ("Dolby Atmos", ["dolby atmos"]),
        ("Google Assistant", ["google assistant"]),
        ("Alexa", ["alexa"]),
        ("S Pen Support", ["s pen support"]),
        ("Portability", ["portable", "compact"]),
        ("Gaming", ["gaming", "esports", "performance"]),
        ("Color Printing", ["color printing"]),
        ("Scan", ["scanning"]),
        ("Copy", ["copying"]),
        ("Print", ["printing"]),
    ]
    for label, phrases in feature_rules:
        if _contains(text, phrases):
            features.append(label)
    if category == "Gaming Console" and "ray tracing" in text:
        features.append("Ray Tracing")
    if category == "Monitor" and "144hz" in text:
        features.append("144Hz")
    if category == "Monitor" and "165hz" in text:
        features.append("165Hz")
    if category == "Monitor" and "1ms" in text:
        features.append("1ms Response Time")
    if category == "TV" and "dolby atmos" in text:
        features.append("Dolby Atmos")
    return _unique(features)


def infer_boolean_flags(text, category):
    lower = text.lower()
    wireless = any(key in lower for key in ["wireless", "bluetooth", "wi-fi", "wifi"]) or category in {
        "Speaker", "Headphones", "Earbuds", "Mouse", "Keyboard", "Gaming Controller", "Smart Home Device", "Streaming Device", "Power Bank", "Charger", "Router", "Tablet", "Laptop", "Smartphone", "Smartwatch", "Fitness Tracker"
    }
    noise_cancellation = any(key in lower for key in ["noise cancellation", "noise cancelling", "active noise cancellation", "anc"])
    waterproof = any(key in lower for key in ["waterproof", "water-resistant", "ip67", "ipx7"])
    return wireless, noise_cancellation, waterproof


def infer_keywords(name, code, category, subcategory, brand, model, description, attrs, features):
    base = [
        category,
        subcategory,
        brand,
        model,
        name,
        code,
        category.lower(),
        subcategory.lower(),
        brand.lower(),
        model.lower(),
    ]
    base.extend(CATEGORY_GENERIC_KEYWORDS.get(category, []))
    for key in ["processor", "ram", "storage", "graphics", "display_size", "display_type", "resolution", "refresh_rate", "camera", "battery", "operating_system", "voice_assistant"]:
        value = attrs.get(key, "")
        if value:
            base.append(str(value))
    base.extend(attrs.get("connectivity", []))
    base.extend(features)
    base.extend([
        "quotation system",
        "product search",
        "inventory",
        "sku",
        "price",
        "stock",
        "gst",
        "online catalog",
        "retail",
        "enterprise",
    ])
    tokens = re.findall(r"[a-z0-9]+", f"{name} {description}".lower())
    for token in tokens:
        if len(token) > 2 and token not in STOPWORDS:
            base.append(token)
    keywords = []
    for item in base:
        item_text = _text(item)
        if item_text:
            keywords.append(item_text.lower())
        if len(keywords) >= 30:
            break
    return _unique(keywords)[:30]


def trim_words(text, minimum=25, maximum=40):
    words = _text(text).split()
    if len(words) > maximum:
        words = words[:maximum]
    return " ".join(words)


def build_description(name, category, brand, subcategory, attrs, original_description):
    parts = [f"{brand} {subcategory.lower()} {name}".strip()]
    key_specs = []
    for key in ["processor", "ram", "storage", "graphics", "display_size", "display_type", "resolution", "refresh_rate", "camera", "battery", "operating_system"]:
        value = attrs.get(key, "")
        if value:
            key_specs.append(str(value))
    if key_specs:
        parts.append("with " + ", ".join(key_specs[:5]))
    usage = attrs.get("usage", "")
    if usage:
        parts.append(f"built for {usage} use")
    elif category in {"Laptop", "Tablet", "Smartphone"}:
        parts.append("built for everyday productivity")
    elif category in {"Monitor", "TV", "Speaker", "Headphones", "Earbuds"}:
        parts.append("for entertainment and daily use")
    elif category in {"Printer", "Router", "Network Switch", "Storage Device", "SSD", "HDD"}:
        parts.append("for home and office workflows")
    elif category in {"Gaming Console", "Gaming Controller", "Gaming Headset", "Gaming Keyboard", "Gaming Mouse"}:
        parts.append("for gaming performance")
    elif category in {"Smart Home Device", "Streaming Device"}:
        parts.append("for connected home use")
    tail = _text(original_description)
    if tail:
        tail = tail[:250].rstrip(" .")
        parts.append(tail)
    description = ". ".join([p.strip(" .") for p in parts if p]).strip()
    description = trim_words(description, 25, 40)
    if len(description.split()) < 25 and original_description:
        extra = _text(original_description)
        description = trim_words(f"{description} {extra}", 25, 40)
    return description


def build_product(product_id, item):
    name, code, original_description, price, stock, gst = item
    text = f"{name} {original_description}"
    category = infer_category(name, original_description)
    brand = infer_brand(name)
    model = infer_model(name, brand)
    subcategory = infer_subcategory(category, name, original_description)
    processor = infer_processor(text)
    ram = infer_ram(text)
    storage = infer_storage(text)
    graphics = infer_graphics(text)
    display_size = infer_display_size(text)
    display_type = infer_display_type(text)
    resolution = infer_resolution(text)
    refresh_rate = infer_refresh_rate(text)
    camera = infer_camera(text)
    battery = infer_battery(text)
    operating_system = infer_operating_system(text)
    connectivity = infer_connectivity(text)
    voice_assistant = infer_voice_assistant(text)
    features = infer_features(category, text)
    wireless, noise_cancellation, waterproof = infer_boolean_flags(text, category)
    usage = infer_usage(text)
    attrs = {
        "processor": processor,
        "ram": ram,
        "storage": storage,
        "graphics": graphics,
        "display_size": display_size,
        "display_type": display_type,
        "resolution": resolution,
        "refresh_rate": refresh_rate,
        "camera": camera,
        "battery": battery,
        "operating_system": operating_system,
        "connectivity": connectivity,
        "voice_assistant": voice_assistant,
        "noise_cancellation": noise_cancellation,
        "wireless": wireless,
        "waterproof": waterproof,
        "features": features,
    }
    if usage:
        attrs["usage"] = usage
    description = build_description(name, category, brand, subcategory, {"usage": usage, **attrs}, original_description)
    keywords = infer_keywords(name, code, category, subcategory, brand, model, description, {**attrs, "usage": usage}, features)
    return {
        "id": product_id,
        "name": name,
        "code": code,
        "category": category,
        "subcategory": subcategory,
        "brand": brand,
        "model": model,
        "description": description,
        "keywords": keywords,
        "attributes": {
            "processor": processor,
            "ram": ram,
            "storage": storage,
            "graphics": graphics,
            "display_size": display_size,
            "display_type": display_type,
            "resolution": resolution,
            "refresh_rate": refresh_rate,
            "camera": camera,
            "battery": battery,
            "operating_system": operating_system,
            "connectivity": connectivity,
            "voice_assistant": voice_assistant,
            "noise_cancellation": noise_cancellation,
            "wireless": wireless,
            "waterproof": waterproof,
            "features": features,
        },
        "price": price,
        "stock": stock,
        "gst": gst,
    }


def build_structured_products(sample_products):
    return [build_product(i + 1, item) for i, item in enumerate(sample_products)]
>>>>>>> bc5e872 (Initial import from local workspace)
