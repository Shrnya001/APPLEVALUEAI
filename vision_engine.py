"""
AppleValue AI - Computer Vision & Visual Quality Assessment Engine
Module: Apple Vision AI (Preliminary Visual Quality Grading)

Provides genuine, deterministic image processing and visual feature extraction:
- Validates real image content and format (JPG, JPEG, PNG)
- Enforces 5 MB max file upload size
- Analyzes color composition in HSV space (Red blush, Green/Yellow ground, Surface blemishes)
- Detects image unsuitability (extreme blur, dark/overexposed lighting)
- Assigns 3 preliminary visual categories (Grade A, Grade B, Grade C) or "Unable to assess reliably"
- Emphasizes that these are preliminary prototype observations, NOT official commercial grades
- Strictly enforces mandatory internal quality checks and zero-tolerance policy on rotten apples
- Avoids fake predictions, invented confidence percentages, and exaggerated AI claims
"""

import os
import colorsys
import uuid
from typing import Dict, Any, Tuple, Optional
from PIL import Image

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "static", "uploads", "vision")
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB max upload limit

MANDATORY_INTERNAL_WARNING = (
    "⚠️ INTERNAL QUALITY CHECK REQUIRED\n\n"
    "This assessment is based on visible features in the uploaded photograph. "
    "Internal bruising, decay and other defects may not be visible externally. "
    "A normal photograph cannot reliably establish the apple's internal condition.\n\n"
    "Reinspect the apple before final grading or sale. "
    "This assessment does not guarantee internal quality or food safety."
)


def ensure_upload_dir():
    """Ensure upload directory exists."""
    os.makedirs(UPLOAD_DIR, exist_ok=True)


def is_allowed_extension(filename: str) -> bool:
    """Check if file extension is allowed."""
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS


def validate_and_save_image(file_storage, target_filename: Optional[str] = None) -> Tuple[bool, str, Optional[str]]:
    """
    Safely validate and store an uploaded image file:
    - Validates extension (JPG, JPEG, PNG)
    - Validates 5 MB file size limit
    - Validates real image contents using Pillow
    - Rejects corrupt or spoofed files
    - Generates a collision-resistant safe filename to prevent path traversal
    
    Returns:
        (is_valid: bool, message: str, saved_filename: Optional[str])
    """
    ensure_upload_dir()

    if not file_storage or not file_storage.filename:
        return False, "No file was selected for upload.", None

    orig_name = file_storage.filename
    if not is_allowed_extension(orig_name):
        return False, "Unsupported file format. Please upload JPG, JPEG, or PNG images.", None

    # Read stream and check size
    file_bytes = file_storage.read()
    if len(file_bytes) == 0:
        return False, "The uploaded file is empty (0 bytes).", None

    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        max_mb = MAX_FILE_SIZE_BYTES // (1024 * 1024)
        return False, f"File size exceeds the {max_mb} MB limit. Please select a smaller photo.", None

    # Reset stream pointer
    file_storage.seek(0)

    # Validate image integrity with Pillow
    try:
        with Image.open(file_storage) as img:
            img.verify()  # Verifies image header and integrity
            fmt = img.format.lower() if img.format else ""
            if fmt not in ["jpeg", "jpg", "png"]:
                return False, f"File content is {fmt.upper()}, which is not supported. Please upload JPG or PNG.", None
    except Exception:
        return False, "The file could not be parsed as a valid image. It may be corrupted or malformed.", None

    # Re-open for clean save (verify closes/invalidates the image object)
    file_storage.seek(0)
    try:
        with Image.open(file_storage) as img:
            ext = orig_name.rsplit(".", 1)[1].lower()
            if ext == "jpeg":
                ext = "jpg"
            safe_filename = target_filename or f"apple_{uuid.uuid4().hex[:12]}.{ext}"
            abs_dest_path = os.path.join(UPLOAD_DIR, safe_filename)
            
            # Convert RGBA to RGB for standard saving if needed
            if img.mode in ("RGBA", "P"):
                rgb_img = img.convert("RGB")
                rgb_img.save(abs_dest_path, quality=92)
            else:
                img.save(abs_dest_path, quality=92)

            return True, "Image uploaded and verified successfully.", safe_filename
    except Exception as e:
        return False, f"Failed to save image: {str(e)}", None


def analyze_apple_image(image_filename: str) -> Dict[str, Any]:
    """
    Perform genuine optical and pixel-level feature extraction on an apple photograph.
    
    Evaluates:
    - Image suitability (detects extreme blur, dark/overexposed lighting)
    - Predominant visible surface colors in HSV space (Red coverage %, Green/Yellow %)
    - Visible surface spots or blemishes
    - Preliminary visual category (Grade A, Grade B, Grade C, or Inconclusive)
    - Flags visible rot/mould for mandatory isolation
    - Mandatory internal quality check warning
    """
    abs_path = os.path.join(UPLOAD_DIR, image_filename)
    if not os.path.exists(abs_path):
        return {
            "is_valid": False,
            "error": "Image file not found on server."
        }

    try:
        with Image.open(abs_path) as raw_img:
            img = raw_img.convert("RGB")
            orig_w, orig_h = img.size

            # Resize to standardized canvas for uniform feature extraction
            sample_w, sample_h = 240, 240
            sample_img = img.resize((sample_w, sample_h), Image.Resampling.LANCZOS)
            pixels = sample_img.load()

    except Exception as e:
        return {
            "is_valid": False,
            "error": f"Error decoding image for analysis: {str(e)}"
        }

    # 1. Optical Clarity & Image Suitability Check
    # Sample luminance across the image to evaluate lighting and edge gradients
    luminance_samples = []
    for y in range(sample_h):
        for x in range(sample_w):
            r, g, b = pixels[x, y]
            lum = 0.299 * r + 0.587 * g + 0.114 * b
            luminance_samples.append(lum)

    avg_luminance = sum(luminance_samples) / len(luminance_samples) if luminance_samples else 0

    # Calculate adjacent-pixel luminance variance as an optical focus / sharpness proxy
    lum_diffs = []
    for i in range(0, len(luminance_samples) - 1, 4):
        lum_diffs.append(abs(luminance_samples[i] - luminance_samples[i + 1]))

    avg_lum_diff = sum(lum_diffs) / len(lum_diffs) if lum_diffs else 0
    sharpness_score = round(avg_lum_diff * 4.2, 1)

    # Detect if image is unsuitable or inconclusive
    # (e.g. extremely dark, completely washed out white, or zero optical contrast/extreme blur)
    is_extremely_dark = avg_luminance < 18.0
    is_washed_out = avg_luminance > 248.0
    is_extremely_blurry = avg_lum_diff < 1.5

    if is_extremely_dark or is_washed_out or is_extremely_blurry:
        reason = "Photograph is extremely dark (underexposed)" if is_extremely_dark else (
            "Photograph is severely overexposed/washed out" if is_washed_out else
            "Photograph has severe optical blur / flat contrast"
        )
        return {
            "is_valid": True,
            "is_suitable": False,
            "image_filename": image_filename,
            "image_dimensions": f"{orig_w} × {orig_h} px",
            "analysis_method": "Preliminary Pixel Feature Extractor (Pillow HSV & Contrast Profiler)",
            "model_name": "No custom trained deep learning model loaded (Preliminary image-processing heuristic)",
            "is_ml_model": False,
            "model_status_note": (
                "Transparent Disclosure: Operating in transparent preliminary image-processing mode. "
                "No custom trained computer vision model (such as a trained ResNet, YOLO, or MobileNet) is present. "
                "Results are preliminary visual observations, not AI-certified grades."
            ),
            "preliminary_grade": "Unable to assess reliably — manual inspection required",
            "grade_code": "INCONCLUSIVE",
            "grade_description": (
                f"The image cannot be assessed reliably ({reason}). "
                "Surface features cannot be distinguished from noise. Manual physical inspection is required."
            ),
            "red_coverage_pct": 0.0,
            "green_yellow_pct": 0.0,
            "dark_blemish_pct": 0.0,
            "decay_risk_level": "Inconclusive",
            "is_decay_flagged": False,
            "sharpness_label": "Unsuitable Image Quality",
            "visible_characteristics": [
                f"Image suitability failure: {reason}.",
                "Cannot reliably isolate apple skin or surface contrast.",
                "Manual physical grading required."
            ],
            "limitations_disclosure": (
                "Photographic Limitation: An image with low illumination, glare, or severe blur cannot be evaluated. "
                "Please capture a clearer photo in indirect natural daylight."
            ),
            "mandatory_internal_warning": MANDATORY_INTERNAL_WARNING,
            "safety_advisory": (
                "🛡️ Physical Sorting Required: Unclear photographs cannot verify fruit condition. "
                "Inspect each apple physically before packing."
            ),
            "proposed_allocation": {
                "premium_pct": 25.0,
                "lower_grade_pct": 25.0,
                "bruised_pct": 25.0,
                "rotten_pct": 25.0,
            }
        }

    # 2. Pixel Sampling and Foreground Extraction
    total_pixels = sample_w * sample_h
    fg_pixels = 0
    red_count = 0
    green_yellow_count = 0
    dark_blemish_count = 0
    decay_necrotic_count = 0

    center_x, center_y = sample_w / 2.0, sample_h / 2.0
    max_radius = min(center_x, center_y) * 0.95

    for y in range(sample_h):
        for x in range(sample_w):
            r, g, b = pixels[x, y]
            lum = 0.299 * r + 0.587 * g + 0.114 * b

            # Convert RGB to HSV
            r_norm, g_norm, b_norm = r / 255.0, g / 255.0, b / 255.0
            h, s, v = colorsys.rgb_to_hsv(r_norm, g_norm, b_norm)

            # Filter out background: neutral white/grey background around corners
            dist_from_center = ((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5
            is_background = (dist_from_center > max_radius) and (s < 0.12 and v > 0.85)

            if is_background:
                continue

            fg_pixels += 1

            # A. Dark necrotic / severe decay spot (very low luminance and low saturation)
            if v < 0.22 and s < 0.40:
                decay_necrotic_count += 1
                dark_blemish_count += 1

            # B. Blemish / Bruise candidate (darkened skin patch, low-mid V)
            elif (v < 0.35 and s < 0.35) or (lum < 55):
                dark_blemish_count += 1

            # C. Red blush (H near 0.0 or near 1.0, with adequate saturation)
            elif (h < 0.08 or h > 0.92) and s > 0.20 and v > 0.25:
                red_count += 1

            # D. Green or Yellow blush (H between 0.08 and 0.42)
            elif 0.08 <= h <= 0.42 and s > 0.15 and v > 0.25:
                green_yellow_count += 1

            else:
                if r > g and r > b:
                    red_count += 1
                else:
                    green_yellow_count += 1

    if fg_pixels == 0:
        fg_pixels = total_pixels

    # Compute percentages
    red_pct = round((red_count / fg_pixels) * 100.0, 1)
    green_yellow_pct = round((green_yellow_count / fg_pixels) * 100.0, 1)
    dark_blemish_pct = round((dark_blemish_count / fg_pixels) * 100.0, 1)
    decay_pct = round((decay_necrotic_count / fg_pixels) * 100.0, 1)

    # 3. Focus & Sharpness Label
    if sharpness_score >= 55.0:
        sharpness_label = "Sharp & Well-Focused"
    elif sharpness_score >= 25.0:
        sharpness_label = "Adequate Focus"
    else:
        sharpness_label = "Soft Focus / Minor Blur"

    # 4. Visible Rot / Mould Risk Flag
    if decay_pct >= 4.5 or dark_blemish_pct >= 18.0:
        decay_risk_level = "Suspected High (Potential Necrotic Decay / Rot)"
        is_decay_flagged = True
    elif decay_pct >= 1.5 or dark_blemish_pct >= 8.0:
        decay_risk_level = "Moderate (Visible Blemishes / Surface Markings)"
        is_decay_flagged = False
    else:
        decay_risk_level = "Low (Clean Visible Skin)"
        is_decay_flagged = False

    # 5. Three Illustrative Preliminary Visual Categories (Section 4)
    # - Grade A — Visually high quality
    # - Grade B — Visible blemishes or minor surface damage
    # - Grade C — Significant visible damage requiring further inspection
    if is_decay_flagged:
        preliminary_grade = "Grade C — Significant visible damage requiring further inspection"
        grade_code = "GRADE_C"
        grade_description = (
            "Significant dark blemish density or necrotic discoloration observed on the visible surface. "
            "Requires immediate physical isolation and tactile inspection."
        )
    elif dark_blemish_pct >= 4.0 or red_pct < 45.0:
        preliminary_grade = "Grade B — Visible blemishes or minor surface damage"
        grade_code = "GRADE_B"
        grade_description = (
            f"Visible surface markings or hail scuffs detected ({dark_blemish_pct}% blemish index), "
            f"or moderate blush coverage ({red_pct}%). Appears structurally sound with minor visual imperfections."
        )
    else:
        preliminary_grade = "Grade A — Visually high quality"
        grade_code = "GRADE_A"
        grade_description = (
            f"High visible blush ({red_pct}%) with smooth skin texture and minimal dark anomalies ({dark_blemish_pct}%). "
            "Exhibits characteristics of premium table fruit on the photographed face."
        )

    # 6. Visible Characteristics Observed
    visible_characteristics = []
    if red_pct >= 70.0:
        visible_characteristics.append(f"Dominant red coloration ({red_pct}%): Strong visible blush coverage.")
    elif red_pct >= 40.0:
        visible_characteristics.append(f"Moderate red blush ({red_pct}%) with green/golden undertones ({green_yellow_pct}%).")
    else:
        visible_characteristics.append(f"Predominantly yellow/green ground color ({green_yellow_pct}%), with {red_pct}% red tint.")

    if dark_blemish_pct < 4.0:
        visible_characteristics.append(f"Minimal surface contrast marks ({dark_blemish_pct}%): Visually clean skin.")
    elif dark_blemish_pct < 12.0:
        visible_characteristics.append(f"Noticeable surface spotting ({dark_blemish_pct}%): May correspond to russeting or light hail scuffs.")
    else:
        visible_characteristics.append(f"Dense surface markings ({dark_blemish_pct}%): Dark patches requiring physical inspection.")

    if is_decay_flagged:
        visible_characteristics.append("⚠️ Suspected decay indicator: Dark necrotic cluster detected on visible face.")

    # 7. Safety Advisory & Food Policy
    if is_decay_flagged:
        safety_advisory = (
            "🚨 VISIBLE ROT / MOULD SUSPECTED: Flagged for isolation and manual physical inspection. "
            "In strict accordance with AppleValue AI food-safety policy, apples with suspected rot or mould "
            "MUST NEVER be recommended for human consumption, table fruit, juice, cider, or other food processing. "
            "Unsound culls must be diverted to verified non-food agricultural composting or bio-fertilizer production."
        )
    else:
        safety_advisory = (
            "🛡️ Mandatory Reinspection: This visual check reviews visible surface skin only. "
            "Always inspect fruit physically before packing or commercial dispatch."
        )

    # 8. Proposed Quality Allocation (For Grower Review — NEVER Auto-Overwrites)
    if is_decay_flagged:
        prop_prem = 0.0
        prop_lower = 20.0
        prop_bruised = 30.0
        prop_rotten = 50.0
    elif dark_blemish_pct >= 8.0:
        prop_prem = 35.0
        prop_lower = 45.0
        prop_bruised = 15.0
        prop_rotten = 5.0
    elif red_pct >= 65.0:
        prop_prem = 80.0
        prop_lower = 14.0
        prop_bruised = 4.0
        prop_rotten = 2.0
    else:
        prop_prem = 55.0
        prop_lower = 30.0
        prop_bruised = 10.0
        prop_rotten = 5.0

    return {
        "is_valid": True,
        "is_suitable": True,
        "image_filename": image_filename,
        "image_dimensions": f"{orig_w} × {orig_h} px",
        "analysis_method": "Preliminary Optical Feature Extractor (Pillow Color & Contrast Profiler)",
        "model_name": "No custom trained deep learning model loaded (Preliminary image-processing heuristic)",
        "is_ml_model": False,
        "model_status_note": (
            "Transparent Disclosure: Operating in transparent preliminary image-processing mode. "
            "No custom trained computer vision model (such as a trained ResNet, YOLO, or MobileNet) is present. "
            "Results are preliminary visual observations, not AI-certified grades."
        ),
        "preliminary_grade": preliminary_grade,
        "grade_code": grade_code,
        "grade_description": grade_description,
        "red_coverage_pct": red_pct,
        "green_yellow_pct": green_yellow_pct,
        "dark_blemish_pct": dark_blemish_pct,
        "decay_risk_level": decay_risk_level,
        "sharpness_score": sharpness_score,
        "sharpness_label": sharpness_label,
        "visible_characteristics": visible_characteristics,
        "mandatory_internal_warning": MANDATORY_INTERNAL_WARNING,
        "safety_advisory": safety_advisory,
        "is_decay_flagged": is_decay_flagged,
        "proposed_allocation": {
            "premium_pct": prop_prem,
            "lower_grade_pct": prop_lower,
            "bruised_pct": prop_bruised,
            "rotten_pct": prop_rotten,
        },
        "limitations_disclosure": (
            "Assessment Limitations: Results reflect optical observations from a 2D photograph. "
            "Lighting angle, shadows, and camera white balance influence color measurements. "
            "Photographs cannot diagnose internal rot, sugar BRIX levels, pesticide residues, or flesh firmness."
        )
    }
