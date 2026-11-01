"""
AppleValue AI - Database Layer
SQLite database setup, schema initialization, and demo data seeders.
All queries use parameterized SQL (? placeholders) for security.
"""

import os
import sqlite3
from datetime import datetime, timedelta

DB_DIR = os.path.join(os.path.dirname(__file__), "instance")
DB_PATH = os.path.join(DB_DIR, "applevalue.db")


def ensure_db_dir():
    """Ensure instance directory exists."""
    os.makedirs(DB_DIR, exist_ok=True)


def get_db():
    """Return a database connection with Row factory."""
    ensure_db_dir()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create all required tables if they don't already exist."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS growers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        grower_type TEXT NOT NULL, -- 'Orchard Owner' or 'Lease Farmer'
        region TEXT NOT NULL,
        village_orchard TEXT,
        contact_info TEXT,
        orchard_size_acres REAL,
        primary_apple_varieties TEXT,
        bio TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS harvest_batches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        grower_id INTEGER,
        batch_code TEXT NOT NULL UNIQUE,
        grower_name TEXT NOT NULL,
        location TEXT NOT NULL,
        variety TEXT DEFAULT 'Royal Delicious',
        total_quantity_kg REAL NOT NULL,
        premium_pct REAL NOT NULL,
        lower_grade_pct REAL NOT NULL,
        bruised_pct REAL NOT NULL,
        rotten_pct REAL NOT NULL,
        harvest_date TEXT NOT NULL,
        sale_urgency TEXT NOT NULL,
        transport_storage_status TEXT NOT NULL,
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (grower_id) REFERENCES growers (id) ON DELETE SET NULL
    );

    CREATE TABLE IF NOT EXISTS buyer_offers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        buyer_name TEXT NOT NULL,
        buyer_type TEXT NOT NULL,
        location TEXT NOT NULL,
        accepted_categories TEXT NOT NULL,
        offered_price_per_kg REAL NOT NULL,
        min_quantity_kg REAL NOT NULL,
        estimated_transport_cost_per_kg REAL DEFAULT 0.0,
        payment_terms TEXT,
        contact_info TEXT,
        is_demo INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS resource_offers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        grower_id INTEGER,
        grower_name TEXT NOT NULL,
        region TEXT NOT NULL,
        resource_type TEXT NOT NULL,
        available_capacity TEXT NOT NULL,
        capacity_num REAL DEFAULT 0.0,
        destination_route TEXT,
        available_from TEXT,
        available_until TEXT,
        cost_sharing_rate TEXT,
        status TEXT DEFAULT 'Available',
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (grower_id) REFERENCES growers (id) ON DELETE SET NULL
    );

    CREATE TABLE IF NOT EXISTS resource_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        grower_id INTEGER,
        grower_name TEXT NOT NULL,
        region TEXT NOT NULL,
        resource_type TEXT NOT NULL,
        quantity_needed TEXT NOT NULL,
        quantity_num REAL DEFAULT 0.0,
        destination TEXT,
        needed_by_date TEXT,
        urgency TEXT DEFAULT 'High',
        status TEXT DEFAULT 'Open',
        notes TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (grower_id) REFERENCES growers (id) ON DELETE SET NULL
    );

    CREATE TABLE IF NOT EXISTS community_posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        grower_id INTEGER,
        grower_name TEXT NOT NULL,
        grower_type TEXT NOT NULL,
        region TEXT NOT NULL,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        category TEXT DEFAULT 'General',
        likes INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (grower_id) REFERENCES growers (id) ON DELETE SET NULL
    );

    CREATE TABLE IF NOT EXISTS interest_expressions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_type TEXT NOT NULL, -- 'offer' or 'request'
        target_id INTEGER NOT NULL,
        interested_grower_name TEXT NOT NULL,
        grower_contact TEXT,
        message TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS vision_assessments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        batch_id INTEGER,
        batch_code TEXT,
        image_filename TEXT NOT NULL,
        original_filename TEXT,
        analysis_method TEXT NOT NULL,
        model_name TEXT DEFAULT 'Visual Feature Extractor v1.0',
        red_coverage_pct REAL DEFAULT 0.0,
        green_yellow_pct REAL DEFAULT 0.0,
        dark_blemish_pct REAL DEFAULT 0.0,
        decay_risk_level TEXT DEFAULT 'Low',
        decay_risk_score REAL DEFAULT 0.0,
        sharpness_score REAL DEFAULT 0.0,
        sharpness_label TEXT DEFAULT 'Adequate',
        observations TEXT,
        safety_advisory TEXT,
        suggested_premium_pct REAL,
        suggested_lower_pct REAL,
        suggested_bruised_pct REAL,
        suggested_rotten_pct REAL,
        is_confirmed_by_grower INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (batch_id) REFERENCES harvest_batches (id) ON DELETE SET NULL
    );
    """)

    conn.commit()

    # Backward-compatible schema migrations: add columns added after initial release
    try:
        conn2 = get_db()
        conn2.execute("ALTER TABLE vision_assessments ADD COLUMN preliminary_grade TEXT DEFAULT NULL")
        conn2.commit()
        conn2.close()
    except Exception:
        pass  # Column already exists — safe to ignore

    conn.close()


def seed_demo_data():
    """
    Reset and seed demonstration data including:
    - 3 key demonstration growers (Ramesh Thakur, Sunita Sharma, Vikram Negi)
    - Additional representative orchard growers across Himachal Pradesh
    - Active harvest records representing diverse quality splits
    - Demonstrated buyer partners across fresh mandis, juice plants, and compost units
    - Shared resource offers and requests matching the 3-minute hackathon demo
    - Active community discussion posts
    """
    conn = get_db()
    cursor = conn.cursor()

    # Clear existing tables safely
    cursor.execute("DELETE FROM vision_assessments")
    cursor.execute("DELETE FROM interest_expressions")
    cursor.execute("DELETE FROM community_posts")
    cursor.execute("DELETE FROM resource_requests")
    cursor.execute("DELETE FROM resource_offers")
    cursor.execute("DELETE FROM buyer_offers")
    cursor.execute("DELETE FROM harvest_batches")
    cursor.execute("DELETE FROM growers")

    # 1. Growers
    growers_data = [
        (
            1,
            "Ramesh Thakur",
            "Lease Farmer",
            "Shimla - Kotkhai",
            "Giri Valley Orchards",
            "DEMO: In-App Message / Kotkhai Cluster",
            3.5,
            "Royal Delicious, Golden Delicious",
            "Lease farmer cultivating 3.5 acres on annual contract. High crop urgency, seeking cost-effective pooled transport to avoid high individual freight.",
        ),
        (
            2,
            "Sunita Sharma",
            "Orchard Owner",
            "Shimla - Rohru",
            "Chanshal View Orchard",
            "DEMO: In-App Message / Rohru Association",
            7.0,
            "Royal Delicious, Red Chief, Gala",
            "3rd generation orchard owner. Regular large consignments to Parwanoo and Chandigarh; frequently has surplus truck space to share.",
        ),
        (
            3,
            "Vikram Negi",
            "Orchard Owner",
            "Kinnaur - Kalpa",
            "Kinner Kailash Organic Slopes",
            "DEMO: In-App Message / Kalpa Valley",
            4.2,
            "Kinnaur Royal, Vance Delicious",
            "High-elevation crisp apples with extended shelf life. Exploring shared cold CA storage and direct institutional buyers.",
        ),
        (
            4,
            "Pooja Chandel",
            "Lease Farmer",
            "Kullu - Manali",
            "Beas River Apple Block",
            "DEMO: In-App Message / Manali Cooperative",
            2.8,
            "Red Delicious, Granny Smith",
            "Young agri-entrepreneur leasing 2.8 acres. Focuses on sorted culinary grades and local artisanal cider partnerships.",
        ),
        (
            5,
            "Mohinder Verma",
            "Orchard Owner",
            "Mandi - Karsog",
            "Karsog Valley Heights",
            "DEMO: In-App Message / Karsog Cluster",
            5.5,
            "Golden Delicious, Early Sun",
            "Owner experimenting with bio-composting damaged windfall apples and sharing bulk plastic crate inventory.",
        ),
    ]

    cursor.executemany(
        """
        INSERT INTO growers (id, name, grower_type, region, village_orchard, contact_info, orchard_size_acres, primary_apple_varieties, bio)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        growers_data,
    )

    # 2. Harvest Batches
    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    two_days_ago = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")

    harvest_data = [
        (
            1,
            1,
            "BATCH-KTK-101",
            "Ramesh Thakur",
            "Kotkhai (Upper Shimla)",
            "Royal Delicious",
            1200.0,
            55.0,  # Premium (660 kg)
            25.0,  # Lower-grade (300 kg)
            15.0,  # Bruised (180 kg)
            5.0,  # Mouldy / Rotten (60 kg)
            today,
            "Immediate (1-2 days)",
            "Needs Transport & Storage",
            "Harvested in damp weather; needs swift transit to Parwanoo mandi or local collection point. Seeking shared transport with Rohru/Theog growers.",
        ),
        (
            2,
            2,
            "BATCH-RHR-202",
            "Sunita Sharma",
            "Rohru Valley",
            "Royal Delicious & Red Chief",
            3500.0,
            75.0,  # Premium (2625 kg)
            15.0,  # Lower-grade (525 kg)
            8.0,  # Bruised (280 kg)
            2.0,  # Mouldy (70 kg)
            yesterday,
            "Moderate (3-5 days)",
            "Self-Sufficient Transport",
            "Hired 6-tonne covered truck heading to Parwanoo Mandi on Nov 2. Has 2,500 kg spare payload available for co-loading along Theog/Solan highway.",
        ),
        (
            3,
            3,
            "BATCH-KNR-303",
            "Vikram Negi",
            "Kalpa, Kinnaur",
            "Kinnaur Royal",
            2000.0,
            80.0,  # Premium (1600 kg)
            12.0,  # Lower-grade (240 kg)
            5.0,  # Bruised (100 kg)
            3.0,  # Mouldy (60 kg)
            two_days_ago,
            "Flexible (1-2 weeks)",
            "Has Transport, Needs Storage",
            "High quality fruit with strong firmness. Target is CA cold storage rental or Delhi premium direct sales.",
        ),
        (
            4,
            4,
            "BATCH-KLU-404",
            "Pooja Chandel",
            "Kullu Valley",
            "Granny Smith & Red Delicious",
            1500.0,
            60.0,  # Premium (900 kg)
            25.0,  # Lower-grade (375 kg)
            12.0,  # Bruised (180 kg)
            3.0,  # Mouldy (45 kg)
            yesterday,
            "Moderate (3-5 days)",
            "Seeking Pool Partner",
            "Exploring local juice & vinegar processors for grade C and bruised volume.",
        ),
    ]

    cursor.executemany(
        """
        INSERT INTO harvest_batches (
            id, grower_id, batch_code, grower_name, location, variety,
            total_quantity_kg, premium_pct, lower_grade_pct, bruised_pct, rotten_pct,
            harvest_date, sale_urgency, transport_storage_status, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        harvest_data,
    )

    # 3. Buyer Offers (Demonstration Partners)
    buyer_data = [
        (
            1,
            "Parwanoo APMC Commission Wholesale",
            "APMC Commission Agent",
            "Parwanoo Mandi, Solan",
            "Premium Fresh (Grade A/B)",
            82.0,  # ₹82/kg
            500.0,  # min 500kg
            3.20,  # ₹3.20/kg transport benchmark from Shimla belt
            "Direct auction settlement, 24-hr payment",
            "DEMO PARTNER - Gate 4 Parwanoo Terminal",
            1,
        ),
        (
            2,
            "HPMC Parala Fruit Processing Plant",
            "Processing & Juice Plant",
            "Parala, Theog, Shimla",
            "Lower Grade Sound (Grade C), Bruised Usable",
            26.0,  # ₹26/kg
            200.0,  # min 200kg
            1.20,  # Lower local transport cost
            "Government MIS support rate, verified receipt",
            "DEMO PARTNER - HPMC Sub-divisional Collection Hub",
            1,
        ),
        (
            3,
            "Shivalik Artisanal Apple Cider & Vinegar Co.",
            "Organic Apple Cider Co.",
            "Solan Industrial Area",
            "Lower Grade Sound (Grade C), Bruised Usable",
            32.0,  # ₹32/kg for sound/sweet juice grade
            400.0,
            2.50,
            "Weekly batch procurement, cashless bank transfer",
            "DEMO PARTNER - Quality Inspec Hub Solan",
            1,
        ),
        (
            4,
            "Azadpur Terminal Fresh Buyers Consortium",
            "APMC Commission Agent",
            "Azadpur Mandi, Delhi",
            "Premium Fresh (Grade A/B)",
            96.0,  # ₹96/kg (higher price at central metro mandi)
            1500.0,  # requires larger consignment
            5.80,  # higher individual long-distance freight
            "Auction clearance within 48 hours",
            "DEMO PARTNER - Delhi APMC Fruit Shed 8",
            1,
        ),
        (
            5,
            "Himalayan Soil Organic Bio-Compost Facility",
            "Non-Food Composting / Bio-Fertilizer",
            "Dhalli Agro Hub, Shimla",
            "Rotten / Compost Only",
            4.5,  # ₹4.50/kg recovery value for organic biomass
            100.0,
            0.80,
            "On-spot weighment receipt; safe agricultural compost recycling",
            "DEMO PARTNER - Non-Food Agro Waste Cell",
            1,
        ),
    ]

    cursor.executemany(
        """
        INSERT INTO buyer_offers (
            id, buyer_name, buyer_type, location, accepted_categories,
            offered_price_per_kg, min_quantity_kg, estimated_transport_cost_per_kg,
            payment_terms, contact_info, is_demo
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        buyer_data,
    )

    # 4. Resource Offers
    resource_offers_data = [
        (
            1,
            2,
            "Sunita Sharma",
            "Shimla - Rohru",
            "Transport Capacity",
            "2,500 kg spare capacity in 6-tonne covered truck",
            2500.0,
            "Rohru -> Kotkhai -> Theog -> Parwanoo Mandi",
            today,
            (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"),
            "₹2.30 / kg (Cooperative fuel and toll share)",
            "Available",
            "Truck departs Rohru at 4:00 AM on Nov 2, passes Kotkhai by 6:30 AM. Can pick up crates along main highway.",
        ),
        (
            2,
            5,
            "Mohinder Verma",
            "Mandi - Karsog",
            "Spare Crates (Plastic/Wooden)",
            "200 Heavy-Duty Standard 20kg Plastic Crates",
            200.0,
            "Karsog & Sundernagar areas",
            today,
            (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d"),
            "₹4.00 / crate / 10 days",
            "Available",
            "Clean sanitized food-grade plastic crates ready for harvest packing. Minimizes fruit bruising compared to damaged wooden boxes.",
        ),
        (
            3,
            2,
            "Sunita Sharma",
            "Shimla - Rohru",
            "Harvesting / Pruning Labour",
            "Trained 4-person experienced grading & packing crew",
            4.0,
            "Rohru - Jubbal - Kotkhai belt",
            (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d"),
            (datetime.now() + timedelta(days=8)).strftime("%Y-%m-%d"),
            "Standard Mandi board day wage rate",
            "Available",
            "Experienced with export-standard 3-tier apple sorting (Color, Size, Skin blemish).",
        ),
    ]

    cursor.executemany(
        """
        INSERT INTO resource_offers (
            id, grower_id, grower_name, region, resource_type,
            available_capacity, capacity_num, destination_route,
            available_from, available_until, cost_sharing_rate, status, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        resource_offers_data,
    )

    # 5. Resource Requests
    resource_requests_data = [
        (
            1,
            1,
            "Ramesh Thakur",
            "Shimla - Kotkhai",
            "Transport / Freight Pooling",
            "1,200 kg apple freight space",
            1200.0,
            "Parwanoo Mandi or Theog HPMC Collection",
            today,
            "High",
            "Open",
            "Lease harvest completed yesterday. Urgently looking to share truck heading down to Solan/Parwanoo to halve individual pickup rental.",
        ),
        (
            2,
            3,
            "Vikram Negi",
            "Kinnaur - Kalpa",
            "Cold Storage Space",
            "1,500 kg Controlled Atmosphere (CA) space",
            1500.0,
            "Rampur or Shimla CA facility",
            (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d"),
            "Moderate",
            "Open",
            "Looking to co-book cold storage pallet space for 4-6 weeks to capture post-harvest festival pricing.",
        ),
        (
            3,
            4,
            "Pooja Chandel",
            "Kullu - Manali",
            "Packaging Material",
            "100 Telescopic Corrugated Export-Grade Cartons",
            100.0,
            "Kullu Central",
            (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d"),
            "High",
            "Open",
            "Need standard tray-pack apple cartons to avoid in-transit bruising for direct buyer trial.",
        ),
    ]

    cursor.executemany(
        """
        INSERT INTO resource_requests (
            id, grower_id, grower_name, region, resource_type,
            quantity_needed, quantity_num, destination, needed_by_date,
            urgency, status, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        resource_requests_data,
    )

    # 6. Community Posts
    community_posts_data = [
        (
            1,
            1,
            "Ramesh Thakur",
            "Lease Farmer",
            "Shimla - Kotkhai",
            "Pooled transport saves lease farmers from distress mandi rates",
            "As a tenant farmer in Kotkhai paying ₹1.8 lakh annual orchard lease, paying ₹5.50/kg for a standalone pickup truck erodes almost 40% of our net margins. Last year we pooled 4 small harvests into a single 10-tonne truck to Parwanoo, and freight dropped to ₹2.10/kg. Let us connect Kotkhai growers on this platform to do this every harvest cycle!",
            "Discussion",
            14,
            yesterday,
        ),
        (
            2,
            2,
            "Sunita Sharma",
            "Orchard Owner",
            "Shimla - Rohru",
            "Space available in 6-tonne truck heading to Parwanoo on Nov 2",
            "Hello Rohru and Kotkhai neighbors! We are moving 3,500 kg of Royal Delicious on Thursday morning. We still have 2,500 kg capacity open in our covered container truck. If anyone along the Rohru-Kharapathar-Kotkhai highway has 500-2000 kg ready, reach out on the Resources tab to co-load!",
            "Announcement",
            21,
            today,
        ),
        (
            3,
            5,
            "Mohinder Verma",
            "Orchard Owner",
            "Mandi - Karsog",
            "Do not dump mouldy or fallen apples in the orchard streams!",
            "Fallen apples with brown rot or scab spore spread fungal infections to healthy trees next spring. We routed 600 kg of non-edible culls to the Dhalli bio-composting unit. It gives a small recovery value (₹4.5/kg) and preserves orchard soil biosecurity.",
            "Advisory",
            19,
            two_days_ago,
        ),
        (
            4,
            4,
            "Pooja Chandel",
            "Lease Farmer",
            "Kullu - Manali",
            "Alternative value for Grade-C apples: Don't give up!",
            "Many commission agents reject Grade-C apples or pay less than ₹12/kg at mandi gates. By partnering directly with local cider pressers and juice units in Kullu, we secured ₹28-32/kg for clean lower-grade fruit. Segregate early on the sorting table!",
            "Success Story",
            28,
            yesterday,
        ),
    ]

    cursor.executemany(
        """
        INSERT INTO community_posts (
            id, grower_id, grower_name, grower_type, region, title, content, category, likes, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        community_posts_data,
    )

    conn.commit()

    # Backward-compatible schema migrations: add columns added after initial release
    try:
        conn2 = get_db()
        conn2.execute("ALTER TABLE vision_assessments ADD COLUMN preliminary_grade TEXT DEFAULT NULL")
        conn2.commit()
        conn2.close()
    except Exception:
        pass  # Column already exists — safe to ignore

    conn.close()


if __name__ == "__main__":
    init_db()
    seed_demo_data()
    print("Database initialized and demo data seeded successfully.")
