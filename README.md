# 🍎 AppleValue AI

**One Apple Community. Smarter Automation. More Revenue.**

> *An AI-assisted community logistics and revenue-optimization platform designed specifically for apple growers and lease farmers in Himachal Pradesh, India.*

---

## 🌟 1. Project Vision & Problem Context

Apple cultivation in Himachal Pradesh (Shimla, Kinnaur, Kullu, Mandi) is the economic backbone for over 250,000 grower families. However, small orchard owners and tenant/lease farmers (*patta* growers) face major structural hurdles each harvest season:

1. **Crippling Freight Inefficiencies:** Small growers pay upwards of **₹5.50 to ₹6.50 per kg** to rent individual small pickups (*Mahindra Bolero / Tata Ace*) down hill highways (NH-5) to terminal mandis like Parwanoo, Solan, Chandigarh, or Delhi Azadpur. Meanwhile, larger carriers travel with half-empty containers.
2. **Distress Selling of Lower Grades:** Hail-marked, small-sized (*Grade C*), and bruised windfall apples are often dumped into mandi auction yards where distress clearance yields less than ₹12–₹16/kg after deducting the 6% APMC commission and unloading labor.
3. **Food Safety & Soil Biosecurity Hazards:** Rotten apples (*Penicillium expansum* / brown rot) left in orchards spread fungal spores to next season's crop or are occasionally unethically mixed into juice pulp streams.

### **The Solution: AppleValue AI**
AppleValue AI connects local apple growers and lease farmers on an equal footing to:
- **Pool shared transport capacity:** Co-loading onto full 6-to-16 tonne trucks slashes freight from **₹5.50/kg down to ₹2.30/kg**, saving thousands of rupees per harvest consignment.
- **Calculate deterministic net returns:** Compares 5 distinct selling pathways before dispatching a single crate.
- **Provide rule-based & AI-assisted advisory:** Recommends optimal grade allocations (fresh mandi vs. HPMC processing vs. artisanal cider vs. safe non-food bio-compost).
- **Enforce strict food safety:** Mandates 100% non-food quarantine for rotten/mouldy fruit into certified bio-compost facilities.

---

## 🛠️ 2. Technology Stack

Built strictly using lightweight, robust technologies with **zero Node.js, React, or frontend build tool bloat**:

| Layer | Technology | Details |
| :--- | :--- | :--- |
| **Backend** | Python 3.9+ & Flask | Clean MVC structure, Jinja2 templates, standard library arithmetic |
| **Database** | SQLite3 (`instance/applevalue.db`) | Local persistent storage with parameterized SQL queries (`?`) |
| **Frontend** | HTML5, CSS3, Vanilla JS | Modern responsive layout, agritech forest green & cream theme, no external UI frameworks |
| **Calculations** | Deterministic Python Engine | Exact arithmetic without rounding errors or LLM hallucinations |
| **Advisory Engine** | Rule-Based Expert System | Transparent horticultural heuristics with optional hybrid Gemini API enhancement |

---

## ⏱️ 3. Three-Minute Hackathon Demo Script

Follow this step-by-step walkthrough to experience the entire end-to-end workflow:

```
[1. View Community] ➔ [2. Inspect Harvest] ➔ [3. Explore Shared Pool] ➔ [4. 5-Way Calculator] ➔ [5. AI Advisor] ➔ [6. Reports & CSV] ➔ [7. AppleVision AI]
```

### **Step 1: Open the Platform & Load Demo Scenario**
- Navigate to `http://localhost:5050/`.
- Notice the high-level KPIs: 5 Demo Growers, 8,200 kg Listed Harvest, and ₹13,440+ Community Net Profit Gain.
- Click the top demo button: **`🚀 Load 3-Min Demo`** to populate the verified demonstration data.

### **Step 2: Inspect Ramesh Thakur's Harvest Batch**
- Click **Harvest Batches** in the navbar (or visit `/harvest`).
- Find batch **`BATCH-KTK-101`** (Grower: *Ramesh Thakur*, Kotkhai, 1,200 kg).
- Note his 4-tier quality breakdown: 55% Premium, 25% Grade C, 15% Bruised, 5% Rotten.
- Notice his urgency is **Immediate (1-2 days)** because fruit was picked in damp weather, and he lacks transport.

### **Step 3: Discover Shared Transport Pooling**
- Click **Resource Pool** in the navbar (or visit `/resources`).
- Look at the **3-Minute Demo Route Match**:
  - *Sunita Sharma* (Rohru) has booked a 6-tonne covered truck heading to Parwanoo Mandi with **2,500 kg spare capacity**.
  - Ramesh (Kotkhai) is directly on Sunita's highway route!
- Click **`🤝 Simulate Ramesh Connecting with Sunita`** to express interest. Ramesh registers his cargo space request instantly.

### **Step 4: Run the 5-Way Revenue Calculator**
- Click **Revenue Calculator** (or visit `/revenue?batch_id=1`).
- Compare all 5 selling strategies side-by-side for Ramesh's 1,200 kg:
  1. *Individual Mandi Consignment:* High freight (₹5.50/kg) & distress sale on Grade C = **₹44,058 Net Return** (₹36.72/kg).
  2. *Sorted Alternative Buyers:* Grade C to culinary buyers = **₹47,600 Net Return** (₹39.67/kg).
  3. *Processing Hub Delivery:* Bulk loose crates to HPMC = **₹46,846 Net Return** (₹39.04/kg).
  4. *AppleValue AI Shared Transport & Pooling (Best):* Freight slashed to ₹2.30/kg = **₹47,898 Net Return** (₹39.92/kg).
  5. *Bio-Secure Orchard Waste:* Safe bio-compost diversion.
- Observe the **+₹3,840 Net Gain** and **₹3,840 Freight Savings** achieved purely through community logistics!

### **Step 5: Inspect the AI Revenue Advisor**
- Click **AI Advisor** in the top navigation (or visit `/advisor/batch/1`).
- Read the transparent disclosure: *Engineered with a deterministic rule-based horticultural expert system*.
- Review the **4-Tier Allocation Plan**:
  - 660 kg Premium ➔ Central APMC Terminal via pooled truck.
  - 300 kg Grade-C ➔ Direct culinary off-take.
  - 180 kg Bruised ➔ Rapid 48-hr local juice pressing.
  - 60 kg Rotten ➔ **Mandatory non-food bio-composting** (with food safety shield).
- Check the **Actionable Next Steps Checklist** before vehicle dispatch.

### **Step 6: Export Analytics & CSV Report**
- Click **Reports** in the navbar (or visit `/reports`).
- Review the total community freight savings (₹13,440+) across all consignments.
- Click **`📥 Download Full CSV Report`** to download `applevalue_ai_harvest_report.csv` for offline Excel auditing.

### **Step 7: Assess Fruit with AppleVision AI**
- Click **📷 AppleVision AI** in the navbar (or visit `/vision`).
- Drag-and-drop or upload an apple photograph (`.jpg`, `.jpeg`, `.png` up to 8MB).
- Select batch **`BATCH-KTK-101`** and click **`🔍 Analyse Image`**.
- Inspect genuine pixel-level optical extraction: Red blush coverage %, Green/Yellow ground color %, Surface blemish index %, Sharpness rating, and Decay Risk.
- Review the proposed quality adjustment and note that it **never automatically overwrites** harvest batch figures without explicit grower review and confirmation.

---

## 🚀 4. Quickstart Guide (Local Installation)

### Prerequisites
- Python 3.9, 3.10, 3.11, or 3.12 installed on your machine.
- No external databases, NPM, or Node.js required!

### Step 1: Clone or Navigate to the Directory
```bash
cd applevalue-ai
```

### Step 2: Create and Activate a Virtual Environment
```bash
python3 -m venv venv

# On macOS / Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### Step 3: Install Required Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Run the Application
```bash
python3 app.py
```

### Step 5: Open in Your Web Browser
Open your browser and navigate to:
```
http://127.0.0.1:5050
```

---

## 🧪 5. Running Automated Tests

To run the complete automated test suite (verifying revenue math, quality percentages sum validation, Flask routes, AppleVision AI image processing, security guards, and CSV export):

```bash
venv/bin/python3 tests.py
```

Expected output:
```
Ran 19 tests in 0.545s
OK
```

---

## 📂 6. Architecture & File Structure

```
applevalue-ai/
├── app.py                      # Flask web application, routing, and controller logic
├── database.py                 # SQLite database setup, schema DDL, and demo data seeder
├── revenue_engine.py           # Deterministic Python arithmetic for all 5 selling pathways
├── recommendation_engine.py    # Rule-based horticultural advisor & route matchmaking
├── vision_engine.py            # AppleVision AI optical feature extraction & model interface
├── requirements.txt            # Python dependencies (Flask >= 3.0.0, Pillow >= 11.0.0)
├── tests.py                    # Automated test suite (19 test cases)
├── README.md                   # Complete documentation and hackathon demo script
├── instance/
│   └── applevalue.db           # SQLite persistent database file
├── templates/
│   ├── base.html               # Master layout, navigation, demo banner, flash alerts
│   ├── index.html              # Dashboard with KPIs, visual chart, recent activity
│   ├── community.html          # Growers directory, search/filter, discussion forum
│   ├── harvest.html            # Harvest consignment table with quality bars
│   ├── harvest_form.html       # Add/Edit consignment form with live 100% validator
│   ├── revenue.html            # Interactive 5-way revenue & cost calculator
│   ├── advisor.html            # AI Revenue Advisor, category allocation, next steps
│   ├── resources.html          # Shared resource pooling directory & express interest
│   ├── buyers.html             # Verified DEMO PARTNER buyer directory
│   ├── value_recovery.html     # 4-tier value cascade guide & interactive simulator
│   ├── reports.html            # Community financial audit & CSV download
│   ├── vision.html             # AppleVision AI photo upload, drag-and-drop & dropzone
│   └── vision_result.html      # Visual assessment metrics, observations & batch review
└── static/
    ├── css/
    │   └── style.css           # Premium agritech aesthetic (forest green, cream, apple red)
    ├── js/
    │   └── app.js              # Vanilla JavaScript interactions, bar animations, modals
    └── uploads/
        └── vision/             # Validated apple upload photos with secure UUID filenames
```

---

## 🛡️ 7. Food Safety & Ethical Disclosures

1. **Zero Rotten Food-Chain Policy:** In compliance with food safety regulations, AppleValue AI explicitly prohibits rotten, decayed, or mouldy apples from being sold for human food or processed into commercial juices/ciders. Such fruit is strictly directed to non-food composting or bio-fertilizer production.
2. **Transparent Advisory Logic:** Rule-based heuristics are truthfully described as a deterministic agricultural expert system, not falsely labeled as a deep neural network. An optional Gemini LLM integration can be activated by setting `GEMINI_API_KEY` in the environment.
3. **Demo Data Notice:** All prices, grower contact details, and buyer profiles are fictional simulation benchmarks designed for hackathon evaluation.

---

*AppleValue AI — Empowering Himachal's Apple Growers Through Shared Intelligence and Community Collaboration.*
