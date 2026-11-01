"""
AppleValue AI - Flask Web Application
One Apple Community. Smarter Automation. More Revenue.
A platform for apple growers in Himachal Pradesh, India.
"""

import csv
import io
import os
import sqlite3
from datetime import datetime
from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    Response,
    url_for,
)

from database import get_db, init_db, seed_demo_data
from recommendation_engine import generate_advisor_report
from revenue_engine import calculate_strategy_returns
from vision_engine import validate_and_save_image, analyze_apple_image

app = Flask(__name__)
app.secret_key = os.environ.get(
    "SECRET_KEY", "applevalue-ai-himachal-hackathon-secret-key-2026"
)
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB max upload size


@app.errorhandler(413)
def request_entity_too_large(error):
    flash("The uploaded file exceeds the 8 MB upload size limit. Please choose a smaller photo.", "danger")
    return redirect(url_for("vision_page"))

# Initialize database on startup
init_db()


# -----------------------------------------------------------------------------
# Context Processors & Template Helpers
# -----------------------------------------------------------------------------
@app.context_processor
def inject_global_data():
    """Inject common metadata into all templates."""
    return {
        "app_name": "AppleValue AI",
        "tagline": "One Apple Community. Smarter Automation. More Revenue.",
        "current_year": datetime.now().year,
        "is_demo_mode": True,
    }


# -----------------------------------------------------------------------------
# Dashboard Route
# -----------------------------------------------------------------------------
@app.route("/")
def index():
    """Main dashboard displaying high-level stats, selling strategy comparison, and recent activity."""
    conn = get_db()
    cursor = conn.cursor()

    # 1. High-level metric counts
    cursor.execute("SELECT COUNT(*) FROM growers")
    demo_growers_count = cursor.fetchone()[0]

    cursor.execute("SELECT COALESCE(SUM(total_quantity_kg), 0) FROM harvest_batches")
    total_harvest_kg = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM resource_requests WHERE status = 'Open'"
    )
    open_requests_count = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM resource_offers WHERE status = 'Available'"
    )
    available_offers_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM harvest_batches")
    batches_count = cursor.fetchone()[0]

    # 2. Aggregated harvest batch records
    cursor.execute(
        "SELECT * FROM harvest_batches ORDER BY created_at DESC LIMIT 5"
    )
    recent_batches = [dict(row) for row in cursor.fetchall()]

    # 3. Community posts
    cursor.execute(
        "SELECT * FROM community_posts ORDER BY created_at DESC LIMIT 4"
    )
    recent_posts = [dict(row) for row in cursor.fetchall()]

    # 4. Illustrative strategy comparison for representative 2,000 kg harvest
    illustrative_calc = calculate_strategy_returns(
        total_kg=2000.0,
        premium_pct=70.0,
        lower_grade_pct=18.0,
        bruised_pct=8.0,
        rotten_pct=4.0,
    )

    # 5. Potential community savings calculation across all batches
    cursor.execute("SELECT * FROM harvest_batches")
    all_batches = [dict(row) for row in cursor.fetchall()]
    total_potential_savings = 0.0
    for batch in all_batches:
        b_calc = calculate_strategy_returns(
            float(batch["total_quantity_kg"]),
            float(batch["premium_pct"]),
            float(batch["lower_grade_pct"]),
            float(batch["bruised_pct"]),
            float(batch["rotten_pct"]),
        )
        if b_calc.get("is_valid", False):
            total_potential_savings += b_calc.get("net_gain_vs_baseline", 0.0)

    conn.close()

    return render_template(
        "index.html",
        demo_growers_count=demo_growers_count,
        total_harvest_kg=total_harvest_kg,
        open_requests_count=open_requests_count,
        available_offers_count=available_offers_count,
        batches_count=batches_count,
        recent_batches=recent_batches,
        recent_posts=recent_posts,
        illustrative_calc=illustrative_calc,
        total_potential_savings=round(total_potential_savings, 2),
    )


# -----------------------------------------------------------------------------
# Community Routes
# -----------------------------------------------------------------------------
@app.route("/community")
def community():
    """Growers community directory and discussion feed."""
    conn = get_db()
    cursor = conn.cursor()

    # Query params for filters
    grower_type = request.args.get("type", "All")
    region_filter = request.args.get("region", "All")
    search_query = request.args.get("q", "").strip()

    # Build growers query
    query = "SELECT * FROM growers WHERE 1=1"
    params = []

    if grower_type and grower_type != "All":
        query += " AND grower_type = ?"
        params.append(grower_type)

    if region_filter and region_filter != "All":
        query += " AND region LIKE ?"
        params.append(f"%{region_filter}%")

    if search_query:
        query += (
            " AND (name LIKE ? OR primary_apple_varieties LIKE ? OR bio LIKE ?)"
        )
        params.extend(
            [f"%{search_query}%", f"%{search_query}%", f"%{search_query}%"]
        )

    query += " ORDER BY id ASC"
    cursor.execute(query, params)
    growers = [dict(row) for row in cursor.fetchall()]

    # Community posts feed
    cursor.execute(
        "SELECT * FROM community_posts ORDER BY created_at DESC, id DESC"
    )
    posts = [dict(row) for row in cursor.fetchall()]

    # Distinct regions for filter dropdown
    cursor.execute("SELECT DISTINCT region FROM growers")
    regions = [row[0] for row in cursor.fetchall()]

    conn.close()

    return render_template(
        "community.html",
        growers=growers,
        posts=posts,
        regions=regions,
        selected_type=grower_type,
        selected_region=region_filter,
        search_query=search_query,
    )


@app.route("/community/post", methods=["POST"])
def add_community_post():
    """Create a new community discussion or announcement post."""
    title = request.form.get("title", "").strip()
    content = request.form.get("content", "").strip()
    grower_name = request.form.get("grower_name", "").strip()
    grower_type = request.form.get("grower_type", "Lease Farmer")
    region = request.form.get("region", "Shimla - Kotkhai")
    category = request.form.get("category", "General")

    if not title or not content or not grower_name:
        flash(
            "Please provide a title, content, and your grower name to post.",
            "danger",
        )
        return redirect(url_for("community"))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO community_posts (grower_name, grower_type, region, title, content, category, likes)
        VALUES (?, ?, ?, ?, ?, ?, 0)
    """,
        (grower_name, grower_type, region, title, content, category),
    )
    conn.commit()
    conn.close()

    flash(
        "Your community post has been published! Growers can now view your insights.",
        "success",
    )
    return redirect(url_for("community"))


@app.route("/community/post/<int:post_id>/like", methods=["POST"])
def like_post(post_id):
    """Increment like count for a community post."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE community_posts SET likes = likes + 1 WHERE id = ?", (post_id,)
    )
    conn.commit()
    conn.close()
    flash("Thank you for supporting this grower's contribution!", "info")
    return redirect(url_for("community"))


# -----------------------------------------------------------------------------
# Harvest Management Routes (CRUD)
# -----------------------------------------------------------------------------
@app.route("/harvest")
def harvest_list():
    """List all harvest batches with status indicators and search/filter options."""
    conn = get_db()
    cursor = conn.cursor()

    urgency_filter = request.args.get("urgency", "All")
    search_query = request.args.get("q", "").strip()

    query = "SELECT * FROM harvest_batches WHERE 1=1"
    params = []

    if urgency_filter and urgency_filter != "All":
        query += " AND sale_urgency LIKE ?"
        params.append(f"%{urgency_filter}%")

    if search_query:
        query += " AND (batch_code LIKE ? OR grower_name LIKE ? OR location LIKE ? OR variety LIKE ?)"
        params.extend(
            [
                f"%{search_query}%",
                f"%{search_query}%",
                f"%{search_query}%",
                f"%{search_query}%",
            ]
        )

    query += " ORDER BY id DESC"
    cursor.execute(query, params)
    batches = [dict(row) for row in cursor.fetchall()]

    conn.close()
    return render_template(
        "harvest.html",
        batches=batches,
        urgency_filter=urgency_filter,
        search_query=search_query,
    )


@app.route("/harvest/new", methods=["GET", "POST"])
def harvest_create():
    """Create a new harvest batch with strict input validation."""
    conn = get_db()
    cursor = conn.cursor()

    if request.method == "POST":
        batch_code = request.form.get("batch_code", "").strip().upper()
        grower_name = request.form.get("grower_name", "").strip()
        location = request.form.get("location", "").strip()
        variety = request.form.get("variety", "Royal Delicious").strip()
        harvest_date = request.form.get(
            "harvest_date", datetime.now().strftime("%Y-%m-%d")
        )
        sale_urgency = request.form.get("sale_urgency", "Moderate (3-5 days)")
        transport_storage_status = request.form.get(
            "transport_storage_status", "Needs Transport & Storage"
        )
        notes = request.form.get("notes", "").strip()

        # Parse and validate numbers
        try:
            total_quantity_kg = float(request.form.get("total_quantity_kg", 0))
            premium_pct = float(request.form.get("premium_pct", 0))
            lower_grade_pct = float(request.form.get("lower_grade_pct", 0))
            bruised_pct = float(request.form.get("bruised_pct", 0))
            rotten_pct = float(request.form.get("rotten_pct", 0))
        except ValueError:
            flash(
                "Please enter valid numerical values for quantity and percentages.",
                "danger",
            )
            return render_template("harvest_form.html", action="Create")

        # Validation: positive quantity
        if total_quantity_kg <= 0:
            flash(
                "Harvest quantity must be a positive number greater than 0 kg.",
                "danger",
            )
            return render_template(
                "harvest_form.html", action="Create", form_data=request.form
            )

        # Validation: percentages must sum to 100%
        total_pct = round(
            premium_pct + lower_grade_pct + bruised_pct + rotten_pct, 2
        )
        if abs(total_pct - 100.0) > 0.05:
            flash(
                f"Quality percentages must sum to exactly 100.0%. Current sum is {total_pct}% "
                f"(Premium: {premium_pct}%, Lower: {lower_grade_pct}%, Bruised: {bruised_pct}%, Mouldy: {rotten_pct}%).",
                "danger",
            )
            return render_template(
                "harvest_form.html", action="Create", form_data=request.form
            )

        # Validation: batch code uniqueness
        cursor.execute(
            "SELECT id FROM harvest_batches WHERE batch_code = ?",
            (batch_code,),
        )
        if cursor.fetchone():
            flash(
                f"Batch code '{batch_code}' is already registered. Please use a unique identifier.",
                "danger",
            )
            return render_template(
                "harvest_form.html", action="Create", form_data=request.form
            )

        # Insert record safely with parameters
        cursor.execute(
            """
            INSERT INTO harvest_batches (
                batch_code, grower_name, location, variety,
                total_quantity_kg, premium_pct, lower_grade_pct, bruised_pct, rotten_pct,
                harvest_date, sale_urgency, transport_storage_status, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                batch_code,
                grower_name,
                location,
                variety,
                total_quantity_kg,
                premium_pct,
                lower_grade_pct,
                bruised_pct,
                rotten_pct,
                harvest_date,
                sale_urgency,
                transport_storage_status,
                notes,
            ),
        )
        conn.commit()
        conn.close()

        flash(
            f"Harvest batch {batch_code} ({total_quantity_kg:,.0f} kg) successfully recorded in database!",
            "success",
        )
        return redirect(url_for("harvest_list"))

    # GET request - load demo growers for convenience dropdown
    cursor.execute("SELECT id, name, region FROM growers ORDER BY name ASC")
    growers = [dict(row) for row in cursor.fetchall()]
    conn.close()

    # Generate a suggested batch code
    auto_code = f"BATCH-HP-{int(datetime.now().timestamp()) % 10000:04d}"

    return render_template(
        "harvest_form.html",
        action="Create",
        growers=growers,
        auto_code=auto_code,
        today=datetime.now().strftime("%Y-%m-%d"),
    )


@app.route("/harvest/<int:batch_id>/edit", methods=["GET", "POST"])
def harvest_edit(batch_id):
    """Edit an existing harvest batch record."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM harvest_batches WHERE id = ?", (batch_id,))
    batch = cursor.fetchone()
    if not batch:
        conn.close()
        flash("Harvest batch not found.", "warning")
        return redirect(url_for("harvest_list"))

    batch = dict(batch)

    if request.method == "POST":
        grower_name = request.form.get("grower_name", "").strip()
        location = request.form.get("location", "").strip()
        variety = request.form.get("variety", "Royal Delicious").strip()
        harvest_date = request.form.get("harvest_date", batch["harvest_date"])
        sale_urgency = request.form.get("sale_urgency", batch["sale_urgency"])
        transport_storage_status = request.form.get(
            "transport_storage_status", batch["transport_storage_status"]
        )
        notes = request.form.get("notes", "").strip()

        try:
            total_quantity_kg = float(
                request.form.get(
                    "total_quantity_kg", batch["total_quantity_kg"]
                )
            )
            premium_pct = float(
                request.form.get("premium_pct", batch["premium_pct"])
            )
            lower_grade_pct = float(
                request.form.get("lower_grade_pct", batch["lower_grade_pct"])
            )
            bruised_pct = float(
                request.form.get("bruised_pct", batch["bruised_pct"])
            )
            rotten_pct = float(
                request.form.get("rotten_pct", batch["rotten_pct"])
            )
        except ValueError:
            flash("Invalid numerical values provided.", "danger")
            conn.close()
            return render_template(
                "harvest_form.html", action="Edit", batch=batch
            )

        if total_quantity_kg <= 0:
            flash("Harvest quantity must be greater than 0 kg.", "danger")
            conn.close()
            return render_template(
                "harvest_form.html", action="Edit", batch=batch
            )

        total_pct = round(
            premium_pct + lower_grade_pct + bruised_pct + rotten_pct, 2
        )
        if abs(total_pct - 100.0) > 0.05:
            flash(
                f"Quality percentages must total 100.0%. Current sum: {total_pct}%.",
                "danger",
            )
            conn.close()
            return render_template(
                "harvest_form.html", action="Edit", batch=batch
            )

        cursor.execute(
            """
            UPDATE harvest_batches SET
                grower_name = ?, location = ?, variety = ?,
                total_quantity_kg = ?, premium_pct = ?, lower_grade_pct = ?,
                bruised_pct = ?, rotten_pct = ?, harvest_date = ?,
                sale_urgency = ?, transport_storage_status = ?, notes = ?
            WHERE id = ?
        """,
            (
                grower_name,
                location,
                variety,
                total_quantity_kg,
                premium_pct,
                lower_grade_pct,
                bruised_pct,
                rotten_pct,
                harvest_date,
                sale_urgency,
                transport_storage_status,
                notes,
                batch_id,
            ),
        )
        conn.commit()
        conn.close()

        flash(
            f"Batch {batch['batch_code']} has been updated successfully.",
            "success",
        )
        return redirect(url_for("harvest_list"))

    conn.close()
    return render_template("harvest_form.html", action="Edit", batch=batch)


@app.route("/harvest/<int:batch_id>/delete", methods=["POST"])
def harvest_delete(batch_id):
    """Delete a harvest batch record."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM harvest_batches WHERE id = ?", (batch_id,)
    )
    conn.commit()
    conn.close()
    flash("Harvest batch record deleted.", "info")
    return redirect(url_for("harvest_list"))


# -----------------------------------------------------------------------------
# Revenue Calculator Routes
# -----------------------------------------------------------------------------
@app.route("/revenue", methods=["GET", "POST"])
def revenue_calculator():
    """Interactive revenue calculator comparing 5 selling and handling strategies."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM harvest_batches ORDER BY id DESC")
    batches = [dict(row) for row in cursor.fetchall()]
    conn.close()

    # Default parameters based on first batch or custom inputs
    selected_batch_id = request.args.get("batch_id")
    current_batch = None

    if selected_batch_id:
        for b in batches:
            if str(b["id"]) == str(selected_batch_id):
                current_batch = b
                break

    if not current_batch and batches:
        current_batch = batches[0]

    # Handle parameters (from form POST or current_batch)
    if request.method == "POST":
        try:
            total_kg = float(request.form.get("total_quantity_kg", 2000.0))
            premium_pct = float(request.form.get("premium_pct", 65.0))
            lower_grade_pct = float(request.form.get("lower_grade_pct", 20.0))
            bruised_pct = float(request.form.get("bruised_pct", 10.0))
            rotten_pct = float(request.form.get("rotten_pct", 5.0))
            custom_premium_price = float(
                request.form.get("custom_premium_price", 82.0)
            )
            custom_solo_freight = float(
                request.form.get("custom_solo_freight", 5.50)
            )
            custom_pooled_freight = float(
                request.form.get("custom_pooled_freight", 2.30)
            )
        except ValueError:
            flash("Invalid numerical input in calculator.", "danger")
            total_kg, premium_pct, lower_grade_pct, bruised_pct, rotten_pct = (
                2000.0,
                65.0,
                20.0,
                10.0,
                5.0,
            )
            custom_premium_price, custom_solo_freight, custom_pooled_freight = (
                82.0,
                5.50,
                2.30,
            )
    elif current_batch:
        total_kg = float(current_batch["total_quantity_kg"])
        premium_pct = float(current_batch["premium_pct"])
        lower_grade_pct = float(current_batch["lower_grade_pct"])
        bruised_pct = float(current_batch["bruised_pct"])
        rotten_pct = float(current_batch["rotten_pct"])
        custom_premium_price = 82.0
        custom_solo_freight = 5.50
        custom_pooled_freight = 2.30
    else:
        total_kg = 2000.0
        premium_pct = 65.0
        lower_grade_pct = 20.0
        bruised_pct = 10.0
        rotten_pct = 5.0
        custom_premium_price = 82.0
        custom_solo_freight = 5.50
        custom_pooled_freight = 2.30

    calc_result = calculate_strategy_returns(
        total_kg=total_kg,
        premium_pct=premium_pct,
        lower_grade_pct=lower_grade_pct,
        bruised_pct=bruised_pct,
        rotten_pct=rotten_pct,
        custom_premium_price=custom_premium_price,
        custom_individual_freight=custom_solo_freight,
        custom_pooled_freight=custom_pooled_freight,
    )

    return render_template(
        "revenue.html",
        batches=batches,
        current_batch=current_batch,
        selected_batch_id=selected_batch_id,
        calc_result=calc_result,
        total_kg=total_kg,
        premium_pct=premium_pct,
        lower_grade_pct=lower_grade_pct,
        bruised_pct=bruised_pct,
        rotten_pct=rotten_pct,
        custom_premium_price=custom_premium_price,
        custom_solo_freight=custom_solo_freight,
        custom_pooled_freight=custom_pooled_freight,
    )


# -----------------------------------------------------------------------------
# AI Revenue Advisor Routes
# -----------------------------------------------------------------------------
@app.route("/advisor")
@app.route("/advisor/batch/<int:batch_id>")
def advisor(batch_id=None):
    """AI Revenue Advisor providing actionable strategy recommendations and matching pooled freight."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM harvest_batches ORDER BY id DESC")
    batches = [dict(row) for row in cursor.fetchall()]

    selected_batch = None
    if batch_id:
        for b in batches:
            if b["id"] == batch_id:
                selected_batch = b
                break

    if not selected_batch and batches:
        selected_batch = batches[0]

    conn.close()

    if not selected_batch:
        flash("No harvest batches available. Please add a batch first.", "info")
        return redirect(url_for("harvest_create"))

    report = generate_advisor_report(selected_batch)

    return render_template(
        "advisor.html",
        batches=batches,
        selected_batch=selected_batch,
        report=report,
    )


# -----------------------------------------------------------------------------
# Shared Resource Pooling Routes
# -----------------------------------------------------------------------------
@app.route("/resources")
def resources():
    """Directory of transport, crate, labour, and storage sharing offers and requests."""
    conn = get_db()
    cursor = conn.cursor()

    res_type = request.args.get("type", "All")

    # Offers
    o_query = "SELECT * FROM resource_offers WHERE 1=1"
    o_params = []
    if res_type != "All":
        o_query += " AND resource_type LIKE ?"
        o_params.append(f"%{res_type}%")
    o_query += " ORDER BY id DESC"
    cursor.execute(o_query, o_params)
    offers = [dict(row) for row in cursor.fetchall()]

    # Requests
    r_query = "SELECT * FROM resource_requests WHERE 1=1"
    r_params = []
    if res_type != "All":
        r_query += " AND resource_type LIKE ?"
        r_params.append(f"%{res_type}%")
    r_query += " ORDER BY id DESC"
    cursor.execute(r_query, r_params)
    requests_list = [dict(row) for row in cursor.fetchall()]

    # Registered demo growers for modal dropdowns
    cursor.execute("SELECT id, name, region FROM growers ORDER BY name ASC")
    growers = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return render_template(
        "resources.html",
        offers=offers,
        requests_list=requests_list,
        growers=growers,
        selected_type=res_type,
    )


@app.route("/resources/offer/new", methods=["POST"])
def create_resource_offer():
    """Create a new resource offer (e.g. spare truck space, extra crates)."""
    grower_name = request.form.get("grower_name", "").strip()
    region = request.form.get("region", "Shimla - Kotkhai").strip()
    resource_type = request.form.get("resource_type", "Transport Capacity")
    available_capacity = request.form.get("available_capacity", "").strip()
    destination_route = request.form.get("destination_route", "").strip()
    cost_sharing_rate = request.form.get("cost_sharing_rate", "").strip()
    notes = request.form.get("notes", "").strip()
    available_until = request.form.get(
        "available_until", datetime.now().strftime("%Y-%m-%d")
    )

    try:
        capacity_num = float(request.form.get("capacity_num", 0))
    except ValueError:
        capacity_num = 0.0

    if not grower_name or not available_capacity:
        flash(
            "Please provide grower name and available capacity details.",
            "danger",
        )
        return redirect(url_for("resources"))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO resource_offers (
            grower_name, region, resource_type, available_capacity, capacity_num,
            destination_route, available_from, available_until, cost_sharing_rate, status, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Available', ?)
    """,
        (
            grower_name,
            region,
            resource_type,
            available_capacity,
            capacity_num,
            destination_route,
            datetime.now().strftime("%Y-%m-%d"),
            available_until,
            cost_sharing_rate,
            notes,
        ),
    )
    conn.commit()
    conn.close()

    flash(
        "Your resource offer has been published for community growers to discover!",
        "success",
    )
    return redirect(url_for("resources"))


@app.route("/resources/request/new", methods=["POST"])
def create_resource_request():
    """Create a new resource request (e.g. seeking transport pooling)."""
    grower_name = request.form.get("grower_name", "").strip()
    region = request.form.get("region", "Shimla - Kotkhai").strip()
    resource_type = request.form.get(
        "resource_type", "Transport / Freight Pooling"
    )
    quantity_needed = request.form.get("quantity_needed", "").strip()
    destination = request.form.get("destination", "").strip()
    urgency = request.form.get("urgency", "High")
    notes = request.form.get("notes", "").strip()
    needed_by_date = request.form.get(
        "needed_by_date", datetime.now().strftime("%Y-%m-%d")
    )

    try:
        quantity_num = float(request.form.get("quantity_num", 0))
    except ValueError:
        quantity_num = 0.0

    if not grower_name or not quantity_needed:
        flash(
            "Please provide grower name and needed quantity details.", "danger"
        )
        return redirect(url_for("resources"))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO resource_requests (
            grower_name, region, resource_type, quantity_needed, quantity_num,
            destination, needed_by_date, urgency, status, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Open', ?)
    """,
        (
            grower_name,
            region,
            resource_type,
            quantity_needed,
            quantity_num,
            destination,
            needed_by_date,
            urgency,
            notes,
        ),
    )
    conn.commit()
    conn.close()

    flash(
        "Your resource request is now active. Nearby growers can view and respond.",
        "success",
    )
    return redirect(url_for("resources"))


@app.route("/resources/interest", methods=["POST"])
def express_interest():
    """Express interest in a resource offer or request."""
    item_type = request.form.get("item_type", "offer")
    target_id = request.form.get("target_id", 0)
    grower_name = request.form.get("interested_grower_name", "").strip()
    grower_contact = request.form.get("grower_contact", "").strip()
    message = request.form.get("message", "").strip()

    if not grower_name:
        flash("Please enter your name to connect with this grower.", "warning")
        return redirect(url_for("resources"))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO interest_expressions (item_type, target_id, interested_grower_name, grower_contact, message)
        VALUES (?, ?, ?, ?, ?)
    """,
        (item_type, target_id, grower_name, grower_contact, message),
    )
    conn.commit()
    conn.close()

    flash(
        f"Interest registered successfully! {grower_name} is now connected for this resource coordination (DEMO).",
        "success",
    )
    return redirect(url_for("resources"))


# -----------------------------------------------------------------------------
# Apple Value Recovery Guide
# -----------------------------------------------------------------------------
@app.route("/value-recovery")
def value_recovery():
    """Educational & interactive guide on value recovery for all 4 apple grades."""
    return render_template("value_recovery.html")


# -----------------------------------------------------------------------------
# Buyer Directory Routes
# -----------------------------------------------------------------------------
@app.route("/buyers")
def buyers_directory():
    """Directory of certified DEMO PARTNERS across wholesale mandis, juice plants, and compost hubs."""
    conn = get_db()
    cursor = conn.cursor()

    category_filter = request.args.get("category", "All")
    query = "SELECT * FROM buyer_offers WHERE 1=1"
    params = []

    if category_filter != "All":
        query += " AND accepted_categories LIKE ?"
        params.append(f"%{category_filter}%")

    query += " ORDER BY offered_price_per_kg DESC"
    cursor.execute(query, params)
    buyers = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return render_template(
        "buyers.html", buyers=buyers, category_filter=category_filter
    )


@app.route("/buyers/new", methods=["POST"])
def add_buyer():
    """Add a new demonstration buyer offer."""
    buyer_name = request.form.get("buyer_name", "").strip()
    buyer_type = request.form.get("buyer_type", "APMC Commission Agent")
    location = request.form.get("location", "").strip()
    accepted_categories = request.form.get(
        "accepted_categories", "Premium Fresh (Grade A/B)"
    )
    payment_terms = request.form.get(
        "payment_terms", "Direct settlement upon delivery"
    )
    contact_info = request.form.get("contact_info", "DEMO PARTNER - In-App")

    try:
        offered_price_per_kg = float(
            request.form.get("offered_price_per_kg", 0)
        )
        min_quantity_kg = float(request.form.get("min_quantity_kg", 100))
        estimated_transport_cost_per_kg = float(
            request.form.get("estimated_transport_cost_per_kg", 2.0)
        )
    except ValueError:
        flash("Invalid numerical values entered for buyer offer.", "danger")
        return redirect(url_for("buyers_directory"))

    if not buyer_name or not location:
        flash("Please provide buyer name and location.", "danger")
        return redirect(url_for("buyers_directory"))

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO buyer_offers (
            buyer_name, buyer_type, location, accepted_categories,
            offered_price_per_kg, min_quantity_kg, estimated_transport_cost_per_kg,
            payment_terms, contact_info, is_demo
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
    """,
        (
            buyer_name,
            buyer_type,
            location,
            accepted_categories,
            offered_price_per_kg,
            min_quantity_kg,
            estimated_transport_cost_per_kg,
            payment_terms,
            contact_info,
        ),
    )
    conn.commit()
    conn.close()

    flash(
        f"Buyer listing '{buyer_name}' created successfully (DEMO PARTNER).",
        "success",
    )
    return redirect(url_for("buyers_directory"))


# -----------------------------------------------------------------------------
# Reports & CSV Export Routes
# -----------------------------------------------------------------------------
@app.route("/reports")
def reports():
    """Summary reports of harvest volumes, category distributions, and community logistics savings."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM harvest_batches ORDER BY id ASC")
    batches = [dict(row) for row in cursor.fetchall()]

    # Aggregations
    total_kg = sum(float(b["total_quantity_kg"]) for b in batches)
    total_premium_kg = sum(
        float(b["total_quantity_kg"]) * (float(b["premium_pct"]) / 100.0)
        for b in batches
    )
    total_lower_kg = sum(
        float(b["total_quantity_kg"]) * (float(b["lower_grade_pct"]) / 100.0)
        for b in batches
    )
    total_bruised_kg = sum(
        float(b["total_quantity_kg"]) * (float(b["bruised_pct"]) / 100.0)
        for b in batches
    )
    total_rotten_kg = sum(
        float(b["total_quantity_kg"]) * (float(b["rotten_pct"]) / 100.0)
        for b in batches
    )

    batch_evaluations = []
    total_baseline_net = 0.0
    total_pooled_net = 0.0
    total_freight_savings = 0.0

    for b in batches:
        calc = calculate_strategy_returns(
            float(b["total_quantity_kg"]),
            float(b["premium_pct"]),
            float(b["lower_grade_pct"]),
            float(b["bruised_pct"]),
            float(b["rotten_pct"]),
        )
        if calc.get("is_valid", False):
            base_net = calc["baseline_strategy"]["net_return"]
            pool_net = calc["pooled_strategy"]["net_return"]
            gain = calc["net_gain_vs_baseline"]
            f_save = calc["freight_savings"]

            total_baseline_net += base_net
            total_pooled_net += pool_net
            total_freight_savings += f_save

            batch_evaluations.append(
                {
                    "batch": b,
                    "calc": calc,
                    "baseline_net": base_net,
                    "pooled_net": pool_net,
                    "gain": gain,
                    "freight_savings": f_save,
                }
            )

    conn.close()

    return render_template(
        "reports.html",
        batches_count=len(batches),
        total_kg=round(total_kg, 2),
        total_premium_kg=round(total_premium_kg, 2),
        total_lower_kg=round(total_lower_kg, 2),
        total_bruised_kg=round(total_bruised_kg, 2),
        total_rotten_kg=round(total_rotten_kg, 2),
        total_baseline_net=round(total_baseline_net, 2),
        total_pooled_net=round(total_pooled_net, 2),
        total_freight_savings=round(total_freight_savings, 2),
        batch_evaluations=batch_evaluations,
    )


@app.route("/reports/export-csv")
def export_csv():
    """Download full harvest and financial comparison data as a CSV spreadsheet."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM harvest_batches ORDER BY id ASC")
    batches = [dict(row) for row in cursor.fetchall()]
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow(
        [
            "Batch Code",
            "Grower Name",
            "Location",
            "Variety",
            "Harvest Date",
            "Urgency",
            "Total Quantity (kg)",
            "Premium %",
            "Premium (kg)",
            "Lower-Grade %",
            "Lower-Grade (kg)",
            "Bruised %",
            "Bruised (kg)",
            "Rotten/Mouldy %",
            "Rotten/Mouldy (kg)",
            "Baseline Solo Net Return (INR)",
            "Baseline Net Per Kg (INR)",
            "Pooled Transport Net Return (INR)",
            "Pooled Net Per Kg (INR)",
            "Community Net Gain (INR)",
            "Freight Savings (INR)",
            "Data Classification",
        ]
    )

    for b in batches:
        calc = calculate_strategy_returns(
            float(b["total_quantity_kg"]),
            float(b["premium_pct"]),
            float(b["lower_grade_pct"]),
            float(b["bruised_pct"]),
            float(b["rotten_pct"]),
        )
        if calc.get("is_valid", False):
            bk = calc["breakdown"]
            base = calc["baseline_strategy"]
            pool = calc["pooled_strategy"]
            writer.writerow(
                [
                    b["batch_code"],
                    b["grower_name"],
                    b["location"],
                    b["variety"],
                    b["harvest_date"],
                    b["sale_urgency"],
                    b["total_quantity_kg"],
                    b["premium_pct"],
                    bk["premium_kg"],
                    b["lower_grade_pct"],
                    bk["lower_grade_kg"],
                    b["bruised_pct"],
                    bk["bruised_kg"],
                    b["rotten_pct"],
                    bk["rotten_kg"],
                    base["net_return"],
                    base["net_return_per_kg"],
                    pool["net_return"],
                    pool["net_return_per_kg"],
                    calc["net_gain_vs_baseline"],
                    calc["freight_savings"],
                    "DEMO DATA - Illustrative Model",
                ]
            )

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=applevalue_ai_harvest_report.csv"
        },
    )


# -----------------------------------------------------------------------------
# Demo Workflow Controls
# -----------------------------------------------------------------------------
@app.route("/demo/load")
def demo_load():
    """Load the 3-minute hackathon demo scenario."""
    seed_demo_data()
    flash(
        "🚀 3-Minute Hackathon Demo Scenario Loaded! Explore the journey of Ramesh Thakur (Kotkhai lease farmer) "
        "and Sunita Sharma (Rohru truck owner) pooling logistics.",
        "success",
    )
    return redirect(url_for("index"))


@app.route("/demo/reset")
def demo_reset():
    """Reset database to clean baseline demo data."""
    seed_demo_data()
    flash("Demo database has been successfully reset to baseline.", "info")
    return redirect(url_for("index"))


# -----------------------------------------------------------------------------
# AppleVision AI - Computer Vision Routes
# -----------------------------------------------------------------------------
@app.route("/vision")
def vision_page():
    """AppleVision AI upload and visual assessment landing page."""
    conn = get_db()
    cursor = conn.cursor()

    # Fetch active harvest batches for optional association
    cursor.execute(
        "SELECT id, batch_code, grower_name, total_quantity_kg FROM harvest_batches ORDER BY id DESC"
    )
    batches = [dict(row) for row in cursor.fetchall()]

    # Fetch recent visual assessments
    cursor.execute("""
        SELECT va.*, hb.grower_name as batch_grower
        FROM vision_assessments va
        LEFT JOIN harvest_batches hb ON va.batch_id = hb.id
        ORDER BY va.id DESC LIMIT 6
    """)
    recent_assessments = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return render_template(
        "vision.html", batches=batches, recent_assessments=recent_assessments
    )


@app.route("/vision/analyze", methods=["POST"])
def vision_analyze():
    """Process uploaded apple image and run genuine visual feature analysis."""
    if "apple_image" not in request.files:
        flash("No image file was provided in the upload request.", "danger")
        return redirect(url_for("vision_page"))

    file = request.files["apple_image"]
    batch_id_raw = request.form.get("batch_id")
    batch_id = (
        int(batch_id_raw) if batch_id_raw and batch_id_raw.isdigit() else None
    )

    is_valid, msg, saved_filename = validate_and_save_image(file)
    if not is_valid:
        flash(msg, "danger")
        return redirect(url_for("vision_page"))

    # Run genuine optical analysis
    analysis = analyze_apple_image(saved_filename)
    if not analysis.get("is_valid", False):
        flash(analysis.get("error", "Visual analysis failed."), "danger")
        return redirect(url_for("vision_page"))

    # Get batch code if associated
    batch_code = None
    conn = get_db()
    cursor = conn.cursor()
    if batch_id:
        cursor.execute(
            "SELECT batch_code FROM harvest_batches WHERE id = ?", (batch_id,)
        )
        b_row = cursor.fetchone()
        if b_row:
            batch_code = b_row["batch_code"]

    # Persist assessment record in SQLite
    prop = analysis["proposed_allocation"]
    obs_text = " | ".join(analysis["visible_characteristics"])
    preliminary_grade = analysis.get("preliminary_grade", "Unable to assess reliably — manual inspection required")

    cursor.execute(
        """
        INSERT INTO vision_assessments (
            batch_id, batch_code, image_filename, original_filename,
            analysis_method, model_name, red_coverage_pct, green_yellow_pct,
            dark_blemish_pct, decay_risk_level, decay_risk_score,
            sharpness_score, sharpness_label, observations, safety_advisory,
            suggested_premium_pct, suggested_lower_pct, suggested_bruised_pct, suggested_rotten_pct,
            is_confirmed_by_grower, preliminary_grade
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
    """,
        (
            batch_id,
            batch_code,
            saved_filename,
            file.filename,
            analysis["analysis_method"],
            analysis["model_name"],
            analysis["red_coverage_pct"],
            analysis["green_yellow_pct"],
            analysis["dark_blemish_pct"],
            analysis["decay_risk_level"],
            0.0,
            analysis.get("sharpness_score", 0.0),
            analysis["sharpness_label"],
            obs_text,
            analysis["safety_advisory"],
            prop["premium_pct"],
            prop["lower_grade_pct"],
            prop["bruised_pct"],
            prop["rotten_pct"],
            preliminary_grade,
        ),
    )
    conn.commit()
    assessment_id = cursor.lastrowid
    conn.close()

    flash(
        "Apple image analyzed successfully! Visual characteristics and observations are ready.",
        "success",
    )
    return redirect(url_for("vision_result", assessment_id=assessment_id))


@app.route("/vision/result/<int:assessment_id>")
def vision_result(assessment_id):
    """View visual assessment result with batch linking and review controls."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT va.*, hb.grower_name, hb.location, hb.variety, hb.total_quantity_kg,
               hb.premium_pct as curr_premium, hb.lower_grade_pct as curr_lower,
               hb.bruised_pct as curr_bruised, hb.rotten_pct as curr_rotten
        FROM vision_assessments va
        LEFT JOIN harvest_batches hb ON va.batch_id = hb.id
        WHERE va.id = ?
    """,
        (assessment_id,),
    )
    assessment = cursor.fetchone()

    if not assessment:
        conn.close()
        flash("Assessment record not found.", "warning")
        return redirect(url_for("vision_page"))

    assessment = dict(assessment)

    # Available batches for linking
    cursor.execute(
        "SELECT id, batch_code, grower_name, total_quantity_kg FROM harvest_batches ORDER BY id DESC"
    )
    batches = [dict(row) for row in cursor.fetchall()]
    conn.close()

    # Split observations text
    observations_list = [
        o.strip()
        for o in assessment.get("observations", "").split(" | ")
        if o.strip()
    ]

    return render_template(
        "vision_result.html",
        assessment=assessment,
        batches=batches,
        observations_list=observations_list,
    )


@app.route("/vision/associate/<int:assessment_id>", methods=["POST"])
def vision_associate_batch(assessment_id):
    """Associate an existing assessment with a harvest batch without overwriting batch percentages."""
    batch_id_raw = request.form.get("batch_id")
    if not batch_id_raw or not batch_id_raw.isdigit():
        flash("Please select a valid harvest batch to associate.", "warning")
        return redirect(url_for("vision_result", assessment_id=assessment_id))

    batch_id = int(batch_id_raw)
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT batch_code FROM harvest_batches WHERE id = ?", (batch_id,)
    )
    batch = cursor.fetchone()
    if not batch:
        conn.close()
        flash("Selected harvest batch not found.", "danger")
        return redirect(url_for("vision_result", assessment_id=assessment_id))

    batch_code = batch["batch_code"]
    cursor.execute(
        "UPDATE vision_assessments SET batch_id = ?, batch_code = ? WHERE id = ?",
        (batch_id, batch_code, assessment_id),
    )
    conn.commit()
    conn.close()

    flash(
        f"Assessment linked to batch {batch_code}. Existing batch quality figures were preserved.",
        "success",
    )
    return redirect(url_for("vision_result", assessment_id=assessment_id))


@app.route("/vision/apply-to-batch/<int:assessment_id>", methods=["POST"])
def vision_apply_to_batch(assessment_id):
    """
    Explicitly apply proposed quality percentages to an associated batch upon grower's confirmation.
    Does NOT happen automatically.
    """
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM vision_assessments WHERE id = ?", (assessment_id,)
    )
    assessment = cursor.fetchone()

    if not assessment or not assessment["batch_id"]:
        conn.close()
        flash("Assessment is not associated with any harvest batch.", "warning")
        return redirect(url_for("vision_result", assessment_id=assessment_id))

    batch_id = assessment["batch_id"]
    batch_code = assessment["batch_code"]

    # Update batch percentages with proposed values
    cursor.execute(
        """
        UPDATE harvest_batches SET
            premium_pct = ?,
            lower_grade_pct = ?,
            bruised_pct = ?,
            rotten_pct = ?,
            notes = COALESCE(notes, '') || ' [Quality split updated based on AppleVision AI assessment #' || ? || ']'
        WHERE id = ?
    """,
        (
            assessment["suggested_premium_pct"],
            assessment["suggested_lower_pct"],
            assessment["suggested_bruised_pct"],
            assessment["suggested_rotten_pct"],
            assessment_id,
            batch_id,
        ),
    )
    cursor.execute(
        "UPDATE vision_assessments SET is_confirmed_by_grower = 1 WHERE id = ?",
        (assessment_id,),
    )
    conn.commit()
    conn.close()

    flash(
        f"Batch {batch_code} quality percentages successfully updated following your review and confirmation!",
        "success",
    )
    return redirect(url_for("harvest_list"))



# -----------------------------------------------------------------------------
# Main Application Runner
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    init_db()
    # Check if empty, seed demo if so
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM growers")
    if cursor.fetchone()[0] == 0:
        seed_demo_data()
    conn.close()

    port = int(os.environ.get("PORT", 5050))
    app.run(host="0.0.0.0", port=port, debug=True)
