"""
PaddleOCR Service — Dual-Mode OCR Engine for Indonesian Report Cards.

Mode 1 (Table Structure): Uses PPStructure/SLANet to detect table structure,
       converts to HTML, parses into rows of subject + score.
Mode 2 (Raw OCR Fallback): Uses PaddleOCR bounding boxes + Y-clustering
       when table detection fails (e.g. borderless/partial tables).

Supports both digital (printed) and handwritten text.
"""

import cv2
import numpy as np
import re
import logging
from typing import List, Dict, Optional, Tuple
from io import StringIO

from paddleocr import PaddleOCR, PPStructureV3
import pandas as pd

from app.services.mapping_engine import get_best_match

logger = logging.getLogger(__name__)

# ============================================================
# GLOBAL ENGINE INSTANCES (lazy-loaded on first call)
# ============================================================
_ocr_engine: Optional[PaddleOCR] = None
_table_engine: Optional[PPStructureV3] = None


def _get_ocr_engine() -> PaddleOCR:
    """Lazy-initialize PaddleOCR engine (singleton)."""
    global _ocr_engine
    if _ocr_engine is None:
        logger.info("Initializing PaddleOCR engine (first call)...")
        _ocr_engine = PaddleOCR(
            use_textline_orientation=True,    # Auto-rotate tilted text
            lang="en",             # Use English model (works for Indonesian latin chars + numbers)
            text_det_thresh=0.3,     # Lower threshold to catch faint handwriting
            text_det_box_thresh=0.4, # Lower box threshold for handwritten text
        )
        logger.info("PaddleOCR engine ready.")
    return _ocr_engine


def _get_table_engine() -> PPStructureV3:
    """Lazy-initialize PPStructure table engine (singleton)."""
    global _table_engine
    if _table_engine is None:
        logger.info("Initializing PPStructure table engine (first call)...")
        _table_engine = PPStructureV3(
            use_table_recognition=True,
            use_gpu=False,
            lang="en",
        )
        logger.info("PPStructure engine ready.")
    return _table_engine


# ============================================================
# IMAGE PREPROCESSING
# ============================================================

def preprocess_image(image_path: str) -> np.ndarray:
    """
    Load and preprocess image for optimal OCR accuracy.
    - Upscale small images to ~1500px width
    - Convert to grayscale
    - Apply adaptive denoising for handwritten text
    - Apply CLAHE for contrast enhancement
    """
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not read image: {image_path}")
    
    # Upscale small images
    height, width = img.shape[:2]
    if width < 1000:
        scale = 1500 / width
        img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        height, width = img.shape[:2]
        logger.info(f"Upscaled image to {width}x{height}")
    
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Denoise (preserve edges for handwriting)
    denoised = cv2.fastNlMeansDenoising(gray, h=10, templateWindowSize=7, searchWindowSize=21)
    
    # CLAHE (Contrast Limited Adaptive Histogram Equalization)
    # Enhances contrast locally — critical for faded handwriting
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(denoised)
    
    # Convert back to BGR (PaddleOCR expects 3-channel)
    result = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)
    
    return result


# ============================================================
# NUMBER PARSING
# ============================================================

def parse_score(text: str) -> Optional[float]:
    """
    Parse a score value from OCR text.
    Handles: "85", "7,50", "8.60", "90", "100", "75.5"
    Returns None if not a valid score.
    """
    text = text.strip()
    
    # Fix handwritten "7o" -> "70" before removing letters
    text = re.sub(r'(\d)[oO]', r'\g<1>0', text)
    
    # Remove common OCR noise
    if not text:
        return None
    
    # Normalize comma to dot
    text = text.replace(',', '.')
    
    try:
        value = float(text)
    except ValueError:
        return None
    
    # Handle missed decimals (e.g. 750 -> 75.0)
    if 100 < value <= 1000:
        value = value / 10
        
    # Scale single digit scores ONLY if they are floats like 7.5 or 8.0, 
    # but be careful with row numbers (1, 2, 3). 
    # To avoid row numbers becoming 10, 20, 30, we rely on the caller's x_pos filter.
    if 0 < value <= 10 and isinstance(value, float) and value != int(value):
        value = value * 10
    
    # Valid score range
    if 0 <= value <= 100:
        return round(value, 1)
    return None


# ============================================================
# MODE 1: TABLE STRUCTURE EXTRACTION (PPStructure)
# ============================================================

def extract_via_table_structure(image_path: str, master_subjects: List[Dict]) -> List[Dict]:
    """
    Use PPStructure to detect table structure → HTML → parse rows.
    Best for: well-structured tables with clear grid lines.
    """
    engine = _get_table_engine()
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not read image: {image_path}")
    
    # Also try with preprocessed image
    preprocessed = preprocess_image(image_path)
    
    results = []
    seen_subjects = set()
    
    # Try both raw and preprocessed
    for attempt_img, attempt_name in [(img, "raw"), (preprocessed, "preprocessed")]:
        try:
            structure_result = engine(attempt_img)
            
            for block in structure_result:
                if block.get("type") != "table":
                    continue
                
                html_str = block.get("res", {}).get("html", "")
                if not html_str:
                    continue
                
                logger.info(f"PPStructure [{attempt_name}]: Found table with HTML ({len(html_str)} chars)")
                
                try:
                    dfs = pd.read_html(StringIO(html_str))
                except Exception as e:
                    logger.warning(f"Failed to parse HTML table: {e}")
                    continue
                
                for df in dfs:
                    _extract_from_dataframe(df, master_subjects, results, seen_subjects)
            
            # If we found results with raw image, no need to try preprocessed
            if results:
                break
                
        except Exception as e:
            logger.warning(f"PPStructure [{attempt_name}] error: {e}")
            continue
    
    logger.info(f"Table Structure Mode: extracted {len(results)} subjects")
    return results


def _extract_from_dataframe(
    df: pd.DataFrame, 
    master_subjects: List[Dict], 
    results: List[Dict], 
    seen_subjects: set
):
    """Extract subject names and scores from a parsed DataFrame."""
    
    for _, row in df.iterrows():
        row_values = [str(v).strip() for v in row.values if pd.notna(v) and str(v).strip()]
        
        if not row_values:
            continue
        
        # Separate text parts and number parts
        text_parts = []
        score_candidates = []
        
        for cell in row_values:
            score = parse_score(cell)
            if score is not None and score >= 10:
                score_candidates.append(score)
            else:
                # Check if cell contains mixed text+numbers
                cleaned = re.sub(r'[\d,.\-]', ' ', cell).strip()
                if cleaned and re.search(r'[A-Za-z]', cleaned):
                    text_parts.append(cleaned)
        
        if not text_parts or not score_candidates:
            continue
        
        candidate_name = " ".join(text_parts)
        
        # Skip header/footer rows
        skip_keywords = [
            'jumlah', 'rata', 'kkm', 'predikat', 'kelompok', 'deskripsi',
            'no', 'mata pelajaran', 'nilai', 'huruf', 'angka', 'keterangan',
            'muatan', 'kompetensi', 'normatif', 'adaptif', 'produktif',
            'capaian', 'kriteria', 'ketuntasan', 'minimum', 'peringkat',
            'sakit', 'izin', 'tanpa', 'kegiatan', 'jenis', 'semester',
            'kelas', 'nama', 'nisn', 'nis', 'tahun', 'pelajaran',
            'mengetahui', 'kepala', 'wali', 'nip', 'tabel',
            'menunjukkan', 'penguasaan', 'diperoleh',
        ]
        candidate_lower = candidate_name.lower()
        words = re.findall(r'\w+', candidate_lower)
        if all(w in skip_keywords for w in words):
            continue
        if len(candidate_name) < 3:
            continue
        
        match = get_best_match(candidate_name, master_subjects, threshold=60)
        if match and match['id'] not in seen_subjects:
            valid_scores = [s for s in score_candidates if s <= 100]
            if not valid_scores:
                continue
                
            if len(valid_scores) >= 2:
                kkm_val = float(valid_scores[0])
                best_score = float(valid_scores[1])
            else:
                kkm_val = None
                best_score = float(valid_scores[0])

            seen_subjects.add(match['id'])
            results.append({
                "subjectId": match['id'],
                "subjectName": match['subject_name'],
                "category": match.get("category", "Umum"),
                "kkm": kkm_val,
                "score": best_score,
                "accuracy": 90.0,
            })
            logger.info(f"  ✅ [Table] '{candidate_name}' → {match['subject_name']} (KKM: {kkm_val}, Score: {best_score})")


# ============================================================
# MODE 2: RAW OCR + Y-CLUSTERING FALLBACK
# ============================================================

def extract_via_raw_ocr(image_path: str, master_subjects: List[Dict]) -> List[Dict]:
    """
    Use PaddleOCR raw bounding boxes + Y-coordinate clustering.
    Fallback mode when table structure detection fails.
    """
    engine = _get_ocr_engine()
    preprocessed = preprocess_image(image_path)
    
    ocr_result = engine.ocr(preprocessed)
    
    if not ocr_result or not ocr_result[0]:
        logger.warning("PaddleOCR returned no results")
        return []
    
    # Flatten results into word entries with coordinates
    # PaddleOCR.predict() returns a dict for this model version
    words = []
    
    if isinstance(ocr_result, list) and isinstance(ocr_result[0], list):
        # Support older nested list format just in case
        for line in ocr_result[0]:
            if not line: continue
            bbox = line[0]           # [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
            text = line[1][0]        # recognized text
            confidence = line[1][1]  # confidence score
            
            y_center = (bbox[0][1] + bbox[2][1]) / 2
            x_left = min(bbox[0][0], bbox[3][0])
            x_right = max(bbox[1][0], bbox[2][0])
            box_width = x_right - x_left
            
            words.append({
                'text': text,
                'x': x_left,
                'y': y_center,
                'width': box_width,
                'conf': float(confidence),
            })
    else:
        # Support dict format (e.g. paddlex returns)
        # It could be a single dict, or a list containing a dict
        res_dict = ocr_result[0] if isinstance(ocr_result, list) else ocr_result
        if not isinstance(res_dict, dict):
            logger.error(f"Unknown OCR result format: {type(res_dict)}")
            return []
            
        rec_texts = res_dict.get('rec_texts', [])
        rec_scores = res_dict.get('rec_scores', [])
        rec_boxes = res_dict.get('rec_boxes', [])
        
        for i in range(len(rec_texts)):
            text = rec_texts[i]
            confidence = rec_scores[i]
            bbox = rec_boxes[i] # [x_min, y_min, x_max, y_max]
            
            y_center = (bbox[1] + bbox[3]) / 2
            x_left = bbox[0]
            box_width = bbox[2] - bbox[0]
            
            words.append({
                'text': text,
                'x': x_left,
                'y': y_center,
                'width': box_width,
                'conf': float(confidence),
            })
    
    # Sort by Y then X
    words.sort(key=lambda w: (w['y'], w['x']))
    
    # Calculate image width for score zone
    if not words:
        return []
    img_width = max(w['x'] + w['width'] for w in words)
    score_zone_start = img_width * 0.30
    
    # Group words into rows by Y-coordinate proximity
    rows = _cluster_by_y(words, y_tolerance=20)
    
    logger.info(f"Raw OCR: {len(words)} words → {len(rows)} rows, img_width={img_width:.0f}, score_zone>={score_zone_start:.0f}")
    
    results = []
    seen_subjects = set()
    
    for i, row in enumerate(rows):
        text_parts = []
        score_candidates = []
        confidences = []
        
        for w in row:
            word = w['text'].strip()
            x_pos = w['x']
            confidences.append(w['conf'])
            
            # Try parsing as number
            # Fix "7#7" -> "77" common PaddleOCR mistake for handwritten 77
            word_for_score = word.replace('#', '')
            score = parse_score(word_for_score)
            if score is not None:
                if x_pos >= score_zone_start:
                    # Normalize single digit scores if they slipped through
                    if score <= 10:
                        score *= 10
                    score_candidates.append(score)
                continue
            
            # Try extracting embedded numbers (e.g. "T9090")
            embedded = re.findall(r'\d{2,3}', word)
            for emb in embedded:
                val = float(emb)
                if 10 <= val <= 100:
                    score_candidates.append(val)
            
            # Clean text for subject matching
            cleaned = re.sub(r'[|{}\[\]()_\d,.]', ' ', word)
            cleaned = re.sub(r'([a-z])([A-Z])', r'\1 \2', cleaned)
            cleaned = re.sub(r'\s+', ' ', cleaned).strip()
            
            if cleaned and re.search(r'[A-Za-z]', cleaned):
                for part in cleaned.split():
                    if len(part) == 1 and part.upper() in 'ABCDT':
                        continue
                    if len(part) < 2:
                        continue
                    text_parts.append(part)
        
        candidate_name = " ".join(text_parts).strip()
        
        if not candidate_name or not score_candidates:
            continue
        
        # Skip known non-subject rows
        skip_keywords = [
            'jumlah', 'rata', 'kkm', 'predikat', 'kelompok', 'deskripsi',
            'no', 'mata pelajaran', 'nilai', 'huruf', 'angka', 'keterangan',
            'muatan', 'kompetensi', 'normatif', 'adaptif', 'produktif',
            'capaian', 'kriteria', 'ketuntasan', 'minimum', 'peringkat',
            'sakit', 'izin', 'tanpa', 'kegiatan', 'jenis', 'semester',
            'kelas', 'nama', 'nisn', 'nis', 'tahun', 'pelajaran',
            'mengetahui', 'kepala', 'wali', 'nip', 'tabel',
            'menunjukkan', 'penguasaan', 'diperoleh',
        ]
        words_lower = [w.lower() for w in text_parts]
        if all(w in skip_keywords for w in words_lower):
            continue
        if len(candidate_name) < 3:
            continue
        
        match = get_best_match(candidate_name, master_subjects, threshold=75)
        if match and match['id'] not in seen_subjects:
            valid_scores = [s for s in score_candidates if s <= 100]
            if not valid_scores:
                continue
                
            # Filter out random small numbers if we have large numbers (>=50)
            has_large_scores = any(s >= 50 for s in valid_scores)
            if has_large_scores:
                valid_scores = [s for s in valid_scores if s >= 50]
            else:
                # Normalization for 1-10 scale
                valid_scores = [s * 10 if s <= 10 else s for s in valid_scores]
                
            if not valid_scores:
                continue
                
            if len(valid_scores) >= 2:
                kkm_val = float(valid_scores[0])
                # Usually KKM is the first number, and the main score is the second number
                best_score = float(valid_scores[1]) 
            else:
                kkm_val = None
                best_score = float(valid_scores[0])
            
            seen_subjects.add(match['id'])
            avg_conf = sum(confidences) / len(confidences) if confidences else 0
            results.append({
                "subjectId": match['id'],
                "subjectName": match['subject_name'],
                "category": match.get("category", "Umum"),
                "kkm": kkm_val,
                "score": float(best_score),
                "accuracy": round(avg_conf * 100, 1),
            })
            logger.info(f"  ✅ [Raw] '{candidate_name}' → {match['subject_name']} (KKM: {kkm_val}, Score: {best_score}, conf={avg_conf:.2f})")
    
    logger.info(f"Raw OCR Mode: extracted {len(results)} subjects")
    return results


def _cluster_by_y(words: List[Dict], y_tolerance: int = 20) -> List[List[Dict]]:
    """Group words into horizontal rows based on Y-coordinate proximity."""
    if not words:
        return []
    
    rows = []
    current_row = [words[0]]
    
    for word in words[1:]:
        avg_y = sum(w['y'] for w in current_row) / len(current_row)
        if abs(word['y'] - avg_y) <= y_tolerance:
            current_row.append(word)
        else:
            rows.append(current_row)
            current_row = [word]
    
    if current_row:
        rows.append(current_row)
    
    # Sort each row by X position (left to right)
    for row in rows:
        row.sort(key=lambda w: w['x'])
    
    return rows


# ============================================================
# MAIN ORCHESTRATOR
# ============================================================

def perform_ocr_and_extract(image_path: str, master_subjects: List[Dict]) -> List[Dict]:
    """
    Main OCR orchestrator — Dual-Mode Strategy:
    1. Try PPStructure table detection first.
    2. If result < 3 subjects, fallback to raw OCR + Y-clustering.
    3. Return whichever mode extracted more subjects.
    """
    logger.info(f"=== Starting OCR for: {image_path} ===")
    
    # Mode 1: Table Structure
    table_results = []
    try:
        table_results = extract_via_table_structure(image_path, master_subjects)
        logger.info(f"Mode 1 (Table): {len(table_results)} subjects found")
    except Exception as e:
        logger.warning(f"Mode 1 (Table) failed: {e}")
    
    # Mode 2: Raw OCR (always run as comparison)
    raw_results = []
    try:
        raw_results = extract_via_raw_ocr(image_path, master_subjects)
        logger.info(f"Mode 2 (Raw OCR): {len(raw_results)} subjects found")
    except Exception as e:
        logger.warning(f"Mode 2 (Raw OCR) failed: {e}")
    
    # Choose the mode that extracted MORE subjects
    if len(table_results) >= len(raw_results) and len(table_results) >= 3:
        logger.info(f"=== Using Table Structure results ({len(table_results)} subjects) ===")
        return table_results
    elif len(raw_results) > 0:
        logger.info(f"=== Using Raw OCR results ({len(raw_results)} subjects) ===")
        return raw_results
    else:
        logger.warning("=== Both modes returned 0 subjects ===")
        return table_results if table_results else raw_results


def debug_ocr_raw_text(image_path: str) -> Dict:
    """
    Debug function: returns raw PaddleOCR text, bounding boxes, and detected rows.
    """
    try:
        engine = _get_ocr_engine()
        preprocessed = preprocess_image(image_path)
        
        ocr_result = engine.ocr(preprocessed)
        
        if not ocr_result or not ocr_result[0]:
            return {"raw_text": "", "total_detections": 0, "rows": []}
        
        # Build raw text
        raw_lines = []
        detections = []
        for line in ocr_result[0]:
            bbox = line[0]
            text = line[1][0]
            conf = line[1][1]
            y_center = (bbox[0][1] + bbox[2][1]) / 2
            x_left = min(bbox[0][0], bbox[3][0])
            
            raw_lines.append(text)
            detections.append({
                "text": text,
                "x_pos": round(x_left),
                "y_pos": round(y_center),
                "confidence": round(conf, 3),
                "is_number": parse_score(text) is not None,
                "number_value": parse_score(text),
            })
        
        # Group into rows
        words = [{'text': d['text'], 'x': d['x_pos'], 'y': d['y_pos'], 'conf': d['confidence'], 'width': 0} for d in detections]
        rows = _cluster_by_y(words, y_tolerance=20)
        
        row_details = []
        for i, row in enumerate(rows):
            row_details.append({
                "row_index": i,
                "full_text": " ".join(w['text'] for w in row),
                "words": [{"text": w['text'], "x": w['x'], "conf": w['conf']} for w in row],
            })
        
        return {
            "raw_text": "\n".join(raw_lines),
            "total_detections": len(detections),
            "total_rows": len(rows),
            "detections": detections,
            "rows": row_details,
        }
    except Exception as e:
        logger.error(f"Debug OCR error: {e}", exc_info=True)
        return {"error": str(e)}
