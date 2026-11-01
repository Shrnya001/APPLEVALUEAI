"""
AppleValue AI - Automated Test Suite
Verifies:
1. Deterministic revenue and cost calculations across all 5 strategies.
2. Quality percentage sum validation (must total 100%).
3. AI Recommendation & Advisory Engine (Rule-based matching & biosecurity enforcement).
4. Flask web routes, templates rendering, database persistence, and CSV export.
"""

import unittest
import csv
import io
from app import app
from database import init_db, seed_demo_data, get_db
from revenue_engine import calculate_strategy_returns, calculate_harvest_breakdown
from recommendation_engine import run_rule_based_advisor, generate_advisor_report


class TestRevenueEngine(unittest.TestCase):

    def setUp(self):
        init_db()
        seed_demo_data()

    def test_harvest_breakdown_math(self):
        """Test exact kilogram calculation across 4 tiers."""
        bk = calculate_harvest_breakdown(
            total_kg=2000.0,
            premium_pct=70.0,
            lower_grade_pct=15.0,
            bruised_pct=10.0,
            rotten_pct=5.0
        )
        self.assertEqual(bk["total_kg"], 2000.0)
        self.assertEqual(bk["premium_kg"], 1400.0)
        self.assertEqual(bk["lower_grade_kg"], 300.0)
        self.assertEqual(bk["bruised_kg"], 200.0)
        self.assertEqual(bk["rotten_kg"], 100.0)

    def test_validation_percentages_sum(self):
        """Test percentage validation rejects sum != 100%."""
        res_invalid = calculate_strategy_returns(
            total_kg=1000.0,
            premium_pct=50.0,
            lower_grade_pct=20.0,
            bruised_pct=10.0,
            rotten_pct=10.0 # sums to 90%
        )
        self.assertFalse(res_invalid["is_valid"])
        self.assertIn("must total exactly 100%", res_invalid["error"])

        res_zero = calculate_strategy_returns(
            total_kg=0.0,
            premium_pct=50.0,
            lower_grade_pct=20.0,
            bruised_pct=20.0,
            rotten_pct=10.0
        )
        self.assertFalse(res_zero["is_valid"])

    def test_five_strategies_calculated(self):
        """Verify all 5 strategies are calculated with deterministic net returns."""
        calc = calculate_strategy_returns(
            total_kg=1200.0,
            premium_pct=55.0,
            lower_grade_pct=25.0,
            bruised_pct=15.0,
            rotten_pct=5.0
        )
        self.assertTrue(calc["is_valid"])
        self.assertEqual(len(calc["strategies"]), 5)

        s1 = calc["strategies"][0] # Solo mandi
        s4 = calc["strategies"][3] # Pooled transport

        # Strategy 4 must beat Strategy 1 in net return due to freight savings (₹5.50 vs ₹2.30)
        self.assertGreater(s4["net_return"], s1["net_return"])
        self.assertGreater(calc["freight_savings"], 0)
        self.assertGreater(calc["net_gain_vs_baseline"], 0)

        # Check rotten fruit yields 0 in food mandi
        self.assertEqual(s1["revenue_breakdown"]["Rotten/Mouldy (60.0 kg - Rejected at gate)"], 0.0)


class TestRecommendationEngine(unittest.TestCase):

    def setUp(self):
        init_db()
        seed_demo_data()

    def test_rule_based_advisor(self):
        """Test rule-based advisory generation for Ramesh Thakur's batch."""
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM harvest_batches WHERE batch_code = 'BATCH-KTK-101'")
        batch = dict(cursor.fetchone())
        conn.close()

        report = generate_advisor_report(batch)
        self.assertTrue(report["is_valid"])
        self.assertEqual(report["grower_name"], "Ramesh Thakur")
        self.assertEqual(len(report["allocations"]), 4)

        # Verify transport match found Sunita Sharma's truck
        self.assertTrue(len(report["transport_matches"]) > 0)
        top_match = report["transport_matches"][0]
        self.assertEqual(top_match["provider_name"], "Sunita Sharma")
        self.assertIn("Rohru", top_match["region"])

        # Check next steps checklist exists
        self.assertTrue(len(report["next_steps"]) >= 4)


class TestFlaskWebRoutes(unittest.TestCase):

    def setUp(self):
        self.app = app
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        init_db()
        seed_demo_data()

    def test_dashboard_route(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        html = response.data.decode("utf-8")
        self.assertIn("AppleValue AI", html)
        self.assertIn("DEMO DATA", html)
        self.assertIn("One Apple Community", html)

    def test_community_route_and_post(self):
        response = self.client.get("/community")
        self.assertEqual(response.status_code, 200)
        html = response.data.decode("utf-8")
        self.assertIn("Ramesh Thakur", html)
        self.assertIn("Sunita Sharma", html)

        # Post new thought
        post_resp = self.client.post("/community/post", data={
            "title": "Kullu Apple Crate Exchange Test",
            "content": "Sharing 50 plastic crates in Manali area.",
            "grower_name": "Test Grower",
            "grower_type": "Lease Farmer",
            "region": "Kullu - Manali",
            "category": "Announcement"
        }, follow_redirects=True)
        self.assertEqual(post_resp.status_code, 200)
        self.assertIn("Kullu Apple Crate Exchange Test", post_resp.data.decode("utf-8"))

    def test_harvest_crud(self):
        # 1. List
        resp = self.client.get("/harvest")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("BATCH-KTK-101", resp.data.decode("utf-8"))

        # 2. Add New Valid
        add_resp = self.client.post("/harvest/new", data={
            "batch_code": "BATCH-TEST-999",
            "grower_name": "Kewal Ram",
            "location": "Theog",
            "variety": "Gala",
            "harvest_date": "2026-10-31",
            "total_quantity_kg": "1800",
            "premium_pct": "60",
            "lower_grade_pct": "20",
            "bruised_pct": "15",
            "rotten_pct": "5",
            "sale_urgency": "Immediate (1-2 days)",
            "transport_storage_status": "Needs Transport & Storage",
            "notes": "Automated test consignment"
        }, follow_redirects=True)
        self.assertEqual(add_resp.status_code, 200)
        self.assertIn("BATCH-TEST-999", add_resp.data.decode("utf-8"))

        # Verify persisted in SQLite
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM harvest_batches WHERE batch_code = 'BATCH-TEST-999'")
        record = cursor.fetchone()
        self.assertIsNotNone(record)
        self.assertEqual(record["total_quantity_kg"], 1800.0)
        conn.close()

        # 3. Add Invalid (% sum != 100)
        invalid_resp = self.client.post("/harvest/new", data={
            "batch_code": "BATCH-FAIL-001",
            "grower_name": "Test",
            "location": "Theog",
            "total_quantity_kg": "1000",
            "premium_pct": "50",
            "lower_grade_pct": "20",
            "bruised_pct": "10",
            "rotten_pct": "10" # 90%
        }, follow_redirects=True)
        self.assertIn("Quality percentages must sum to exactly 100.0%", invalid_resp.data.decode("utf-8"))

    def test_revenue_calculator_route(self):
        resp = self.client.get("/revenue?batch_id=1")
        self.assertEqual(resp.status_code, 200)
        html = resp.data.decode("utf-8")
        self.assertIn("5-Way Selling Strategy", html)
        self.assertIn("AppleValue AI Shared Transport &amp; Pooling", html)
        self.assertIn("Estimated Net Return", html)

    def test_advisor_route(self):
        resp = self.client.get("/advisor/batch/1")
        self.assertEqual(resp.status_code, 200)
        html = resp.data.decode("utf-8")
        self.assertIn("AI Revenue &amp; Logistics Advisor", html)
        self.assertIn("Sunita Sharma", html)

    def test_resources_and_interest(self):
        resp = self.client.get("/resources")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Shared Resource Pooling", resp.data.decode("utf-8"))

        # Test expressing interest
        interest_resp = self.client.post("/resources/interest", data={
            "item_type": "offer",
            "target_id": "1",
            "interested_grower_name": "Ramesh Thakur",
            "grower_contact": "DEMO: 98160-XXXXX",
            "message": "Let us pool our freight to Parwanoo"
        }, follow_redirects=True)
        self.assertEqual(interest_resp.status_code, 200)
        self.assertIn("Interest registered successfully", interest_resp.data.decode("utf-8"))

    def test_buyer_directory_and_value_recovery(self):
        resp = self.client.get("/buyers")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("DEMO PARTNER", resp.data.decode("utf-8"))

        val_resp = self.client.get("/value-recovery")
        self.assertEqual(val_resp.status_code, 200)
        self.assertIn("Mandatory Food Safety", val_resp.data.decode("utf-8"))

    def test_reports_and_csv_export(self):
        # 1. Reports page
        resp = self.client.get("/reports")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Cumulative Freight Savings", resp.data.decode("utf-8"))

        # 2. CSV Export
        csv_resp = self.client.get("/reports/export-csv")
        self.assertEqual(csv_resp.status_code, 200)
        self.assertEqual(csv_resp.mimetype, "text/csv")
        csv_text = csv_resp.data.decode("utf-8")
        reader = csv.reader(io.StringIO(csv_text))
        rows = list(reader)
        self.assertGreater(len(rows), 2)
        header = rows[0]
        self.assertIn("Batch Code", header)
        self.assertIn("Pooled Transport Net Return (INR)", header)
        self.assertIn("Community Net Gain (INR)", header)


class TestAppleVisionAI(unittest.TestCase):

    def setUp(self):
        self.app = app
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        init_db()
        seed_demo_data()

    def _create_dummy_image(self, color=(190, 40, 40), size=(120, 120), format="JPEG"):
        """Helper to create an in-memory test image using Pillow."""
        from PIL import Image
        img = Image.new("RGB", size, color=color)
        buf = io.BytesIO()
        img.save(buf, format=format)
        buf.seek(0)
        return buf

    def test_vision_page_get(self):
        """Test GET /vision loads the upload interface with disclosures."""
        resp = self.client.get("/vision")
        self.assertEqual(resp.status_code, 200)
        html = resp.data.decode("utf-8")
        self.assertIn("AppleVision AI", html)
        self.assertIn("Upload Apple Photograph", html)
        self.assertIn("Analysis Methodology &amp; Engineering Disclosure", html)
        self.assertIn("Food Safety &amp; Non-Food Policy", html)

    def test_valid_image_upload_and_analysis(self):
        """Test uploading a valid image returns optical analysis results."""
        img_buf = self._create_dummy_image(color=(210, 35, 35))
        data = {
            "apple_image": (img_buf, "test_red_apple.jpg"),
            "batch_id": "1"
        }
        resp = self.client.post("/vision/analyze", data=data, content_type="multipart/form-data", follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        html = resp.data.decode("utf-8")
        self.assertIn("Apple Visual Quality Assessment Report", html)
        self.assertIn("Predominant Surface Color Composition", html)
        self.assertIn("Red Blush", html)
        self.assertIn("BATCH-KTK-101", html)
        self.assertIn("Modular Visual Feature Extractor", html)

    def test_invalid_extension_rejected(self):
        """Test that non-image file extensions are rejected."""
        fake_file = io.BytesIO(b"Not an image text data")
        data = {
            "apple_image": (fake_file, "script.py")
        }
        resp = self.client.post("/vision/analyze", data=data, content_type="multipart/form-data", follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        html = resp.data.decode("utf-8")
        self.assertIn("Unsupported file format", html)

    def test_corrupt_image_rejected(self):
        """Test that corrupted image bytes with image extension are rejected."""
        corrupt_buf = io.BytesIO(b"\xFF\xD8\xFF\xE0corruptpayloadnotreallyanimage12345")
        data = {
            "apple_image": (corrupt_buf, "corrupt.jpg")
        }
        resp = self.client.post("/vision/analyze", data=data, content_type="multipart/form-data", follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        html = resp.data.decode("utf-8")
        self.assertIn("could not be parsed as a valid image", html)

    def test_batch_association_preserves_existing_percentages(self):
        """Test that visual assessment linking does not automatically overwrite batch percentages."""
        # 1. Check current batch 1 percentages
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT premium_pct, lower_grade_pct, bruised_pct, rotten_pct FROM harvest_batches WHERE id = 1")
        b_orig = dict(cursor.fetchone())
        conn.close()

        # 2. Upload image associated with batch 1
        img_buf = self._create_dummy_image(color=(180, 50, 40))
        data = {
            "apple_image": (img_buf, "specimen_sample.png"),
            "batch_id": "1"
        }
        resp = self.client.post("/vision/analyze", data=data, content_type="multipart/form-data", follow_redirects=True)
        self.assertEqual(resp.status_code, 200)

        # 3. Verify batch percentages in SQLite were NOT modified automatically
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT premium_pct, lower_grade_pct, bruised_pct, rotten_pct FROM harvest_batches WHERE id = 1")
        b_after = dict(cursor.fetchone())
        conn.close()

        self.assertEqual(b_orig["premium_pct"], b_after["premium_pct"])
        self.assertEqual(b_orig["lower_grade_pct"], b_after["lower_grade_pct"])
        self.assertEqual(b_orig["bruised_pct"], b_after["bruised_pct"])
        self.assertEqual(b_orig["rotten_pct"], b_after["rotten_pct"])

    def test_explicit_grower_confirmation_updates_batch(self):
        """Test that proposed allocation is applied ONLY when explicitly confirmed."""
        # 1. Create standalone assessment
        img_buf = self._create_dummy_image(color=(220, 25, 25))
        data = {
            "apple_image": (img_buf, "batch_specimen.jpg"),
            "batch_id": "1"
        }
        resp = self.client.post("/vision/analyze", data=data, content_type="multipart/form-data", follow_redirects=True)
        self.assertEqual(resp.status_code, 200)

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, suggested_premium_pct FROM vision_assessments ORDER BY id DESC LIMIT 1")
        assessment = dict(cursor.fetchone())
        conn.close()

        # 2. Explicitly apply to batch
        apply_resp = self.client.post(f"/vision/apply-to-batch/{assessment['id']}", follow_redirects=True)
        self.assertEqual(apply_resp.status_code, 200)
        self.assertIn("quality percentages successfully updated following your review", apply_resp.data.decode("utf-8"))

        # 3. Verify batch in SQLite was updated
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT premium_pct FROM harvest_batches WHERE id = 1")
        updated_prem = cursor.fetchone()["premium_pct"]
        conn.close()
        self.assertEqual(updated_prem, assessment["suggested_premium_pct"])

    def test_decay_safety_warning(self):
        """Test that dark necrotic apple features trigger strict food-safety warning."""
        from PIL import Image, ImageDraw
        # Create image with dark black/brown necrotic patch
        img = Image.new("RGB", (160, 160), color=(180, 40, 40))
        draw = ImageDraw.Draw(img)
        draw.ellipse([40, 40, 120, 120], fill=(20, 10, 10)) # large dark decay lesion
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        buf.seek(0)

        data = {
            "apple_image": (buf, "decayed_apple.jpg")
        }
        resp = self.client.post("/vision/analyze", data=data, content_type="multipart/form-data", follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        html = resp.data.decode("utf-8")
        self.assertIn("CRITICAL FOOD SAFETY WARNING", html)
        self.assertIn("MUST NEVER be recommended for human consumption", html)


if __name__ == "__main__":
    unittest.main()
