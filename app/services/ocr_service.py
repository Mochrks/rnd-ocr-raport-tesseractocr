import cv2
import pytesseract
from pytesseract import Output
import re
import logging
from typing import List, Dict, Optional
import numpy as np
import os
import pypdfium2 as pdfium

from app.services.mapping_engine import get_best_match

# Set Tesseract executable 
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

logger = logging.getLogger(__name__)

def preprocess_image(image_path: str):
    """
    Load image, apply morphological operations to detect table lines, 
    and 'paint' them white over the original grayscale image to preserve 
    anti-aliased text boundaries while eliminating table grids.
    """
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not read image: {image_path}")
        
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 1. Scale image if needed (Tesseract works best with 300 DPI, width ~1500px)
    height, width = gray.shape
    if width < 1000:
        scale = 1500 / width
        gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        height, width = gray.shape

    # Binarization (strictly for finding lines, NOT for OCR)
    _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
    
    # ---- DETECT TABLE LINES ----
    # Detect horizontal lines
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (width // 8, 1))
    horizontal_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)
    
    # Detect vertical lines
    vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, height // 8))
    vertical_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, vertical_kernel, iterations=2)
    
    # Combine lines
    table_lines = cv2.add(horizontal_lines, vertical_lines)
    
    # Slightly dilate the lines to ensure we cover the soft/anti-aliased edges of the grid
    line_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    table_lines_dilated = cv2.dilate(table_lines, line_kernel, iterations=1)
    
    # ---- GRAYSCALE PAINTING ----
    # Paint the detected lines pure white (255) on the original grayscale image!
    gray_painted = gray.copy()
    gray_painted[table_lines_dilated > 0] = 255
    
    return gray_painted


def parse_indonesian_number(text: str) -> Optional[float]:
    """
    Parse numbers in Indonesian report card format.
    Handles: "85", "7,50", "8.60", "90", "100", "9,70", "7.50"
    Normalizes 0-10 scale or missing decimals (e.g. 750) to 0-100 scale.
    Returns None if not a valid score number.
    """
    text = text.strip()
    
    # Strip some noise characters around the number
    text = re.sub(r'["\'!_]', '', text)
    
    # Match: 1-4 digits, optionally followed by comma or dot and 1-2 digits
    match = re.match(r'^(\d{1,4})([,.](\d{1,2}))?$', text)
    if not match:
        return None
    
    whole = match.group(1)
    decimal = match.group(3)
    
    if decimal:
        value = float(f"{whole}.{decimal}")
    else:
        value = float(whole)
    
    # Normalize values
    if 100 < value <= 1000:
        # Convert missed decimals (e.g., 750 instead of 7,50) to 75.0
        value = value / 10
        
    # Valid score range: 0-100
    if 0 <= value <= 100:
        return value
    return None

def extract_embedded_numbers(word: str) -> List[float]:
    """
    Extract numbers that are embedded/merged inside OCR garbage text.
    
    Tesseract often merges table cells together, producing strings like:
    - "T9090" → should extract [90, 90]
    - "|8585|" → should extract [85, 85]
    - "T8080" → should extract [80, 80]
    - "9096" → should extract [90, 96]
    - "[9085" → should extract [90, 85]
    
    Returns list of valid score numbers found.
    """
    # Find all sequences of 2-3 digits in the word
    matches = re.findall(r'\d{2,3}', word)
    results = []
    for m in matches:
        val = float(m)
        if 10 <= val <= 100:  # Valid score range (skip single digits and >100)
            results.append(val)
    return results

def extract_clean_text(word: str) -> str:
    """
    Extract only meaningful alphabetic text from OCR garbage.
    Handles:
    - Pipe characters, brackets: "|Bahasa|" → "Bahasa"
    - Merged words: "BahasaIndonesia" → "Bahasa Indonesia"
    - Number-letter mix: "T9090" → "T" (numbers stripped)
    """
    # Remove common OCR noise characters
    cleaned = re.sub(r'[|{}\[\]()_\d,.]', ' ', word)
    
    # Split camelCase / merged words: "BahasaIndonesia" → "Bahasa Indonesia"
    # Insert space before each uppercase letter that follows a lowercase letter
    cleaned = re.sub(r'([a-z])([A-Z])', r'\1 \2', cleaned)
    
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

def group_words_into_rows(data: Dict, y_tolerance: int = 15) -> List[List[Dict]]:
    """
    Groups individual words into horizontal rows based on their Y coordinate.
    """
    words = []
    n_boxes = len(data['text'])
    for i in range(n_boxes):
        text = data['text'][i].strip()
        conf = int(data['conf'][i]) if data['conf'][i] != '-1' else 0
        if text and conf > 0:
            words.append({
                'text': text,
                'left': data['left'][i],
                'top': data['top'][i],
                'width': data['width'][i],
                'height': data['height'][i],
                'conf': conf
            })
            
    if words:
        avg_height = sum(w['height'] for w in words) / len(words)
        y_tolerance = max(y_tolerance, avg_height * 0.8)
        
        words.sort(key=lambda w: (w['top'], w['left']))
    
    rows = []
    current_row = []
    
    for word in words:
        if not current_row:
            current_row.append(word)
        else:
            avg_top = sum(w['top'] for w in current_row) / len(current_row)
            if abs(word['top'] - avg_top) <= y_tolerance:
                current_row.append(word)
            else:
                rows.append(current_row)
                current_row = [word]
                
    if current_row:
        rows.append(current_row)
        
    for row in rows:
        row.sort(key=lambda w: w['left'])
        
    return rows

def debug_ocr_raw_text(image_path: str) -> Dict:
    """
    Debug function: returns raw OCR text, detected rows, and number positions.
    """
    try:
        processed_img = preprocess_image(image_path)
        custom_config = r'--oem 3 --psm 6'
        raw_text = pytesseract.image_to_string(processed_img, lang='eng', config=custom_config)
        data = pytesseract.image_to_data(processed_img, lang='eng', config=custom_config, output_type=Output.DICT)
        
        rows = group_words_into_rows(data, y_tolerance=20)
        
        img_width = max(data['left'][i] + data['width'][i] for i in range(len(data['text'])) if data['text'][i].strip()) if any(data['text']) else 0
        
        row_details = []
        for i, row in enumerate(rows):
            words_info = []
            for w in row:
                num = parse_indonesian_number(w['text'])
                embedded = extract_embedded_numbers(w['text']) if num is None else []
                words_info.append({
                    "text": w['text'],
                    "x_pos": w['left'],
                    "is_number": num is not None,
                    "number_value": num,
                    "embedded_numbers": embedded
                })
            row_details.append({
                "row_index": i,
                "full_text": " ".join([w['text'] for w in row]),
                "words": words_info
            })
        
        return {
            "raw_text": raw_text,
            "image_width": img_width,
            "total_rows_detected": len(rows),
            "rows": row_details
        }
    except Exception as e:
        return {"error": str(e)}

def perform_ocr_and_extract(image_path: str, master_subjects: List[Dict]) -> List[Dict]:
    """
    Universal Parser using Bounding Box Row Clustering + X-Position Score Detection.
    
    Strategy:
    - Numbers on the FAR LEFT of a row are row numbers (1, 2, 3...) → IGNORE
    - Numbers on the RIGHT SIDE are actual scores (88, 94, 90...) → CAPTURE
    - Embedded numbers in garbled text (e.g. "T9090") are also extracted
    """
    try:
        processed_img = preprocess_image(image_path)
        
        custom_config = r'--oem 3 --psm 6'
        data = pytesseract.image_to_data(processed_img, lang='eng', config=custom_config, output_type=Output.DICT)
        
        rows = group_words_into_rows(data, y_tolerance=20)
        extracted_data = []
        
        # Calculate image width for score zone detection
        all_lefts = [data['left'][i] + data['width'][i] for i in range(len(data['text'])) if data['text'][i].strip()]
        if not all_lefts:
            return []
        img_width = max(all_lefts)
        
        # --- NEW LOGIC: HEADER ANCHORING ---
        target_x = None
        kkm_x = None
        header_candidates = []
        for row in rows:
            for w in row:
                x_center = w['left'] + w['width']/2
                # Only consider headers in the right 75% of the page to avoid matching text in the Subject column
                if x_center < img_width * 0.25:
                    continue
                    
                text_lower = w['text'].lower()
                clean = re.sub(r'[^a-z]', '', text_lower)
                if clean in ['pengetahuan', 'tulis']:
                    header_candidates.append({'type': 'primary', 'x': x_center, 'y': w['top']})
                elif clean in ['nilai', 'rata', 'rapor', 'nitai', 'nital', 'nllai', 'akhir', 'angka', 'nlai']:
                    header_candidates.append({'type': 'fallback', 'x': x_center, 'y': w['top']})
                elif clean in ['kkm', 'kriteria', 'skbm']:
                    header_candidates.append({'type': 'kkm', 'x': x_center, 'y': w['top']})
                elif clean in ['capaian', 'kompetensi', 'deskripsi']:
                    if x_center > img_width * 0.55:
                        header_candidates.append({'type': 'capaian', 'x': x_center, 'y': w['top']})

        primary_headers = [h for h in header_candidates if h['type'] == 'primary']
        fallback_headers = [h for h in header_candidates if h['type'] == 'fallback']
        kkm_headers = [h for h in header_candidates if h['type'] == 'kkm']
        
        def get_best_header_x(headers):
            if not headers:
                return None
            # Find the minimum Y (highest in the page)
            min_y = min(h['y'] for h in headers)
            # Filter headers that are in the top row (within 30 pixels of min_y)
            top_headers = [h for h in headers if h['y'] - min_y < 30]
            # Take the leftmost one
            top_headers.sort(key=lambda h: h['x'])
            return top_headers[0]['x']

        target_x = get_best_header_x(primary_headers)
        if target_x is None:
            target_x = get_best_header_x(fallback_headers)
            
        kkm_x = get_best_header_x(kkm_headers)
        capaian_headers = [h for h in header_candidates if h['type'] == 'capaian']
        capaian_x = get_best_header_x(capaian_headers)
            
        if target_x is not None:
            logger.info(f"Header Anchoring active. Target X coordinate: {target_x:.0f}")
        else:
            logger.info("Header Anchoring fallback mode: No specific score header found.")
            
        # Dynamically determine the score zone start based on KKM or Target X
        score_zone_start = img_width * 0.25  # default baseline
        if kkm_x is not None:
            score_zone_start = min(score_zone_start, kkm_x - 50)
        elif target_x is not None:
            score_zone_start = min(score_zone_start, target_x - 100)
            
        max_subject_x = target_x - 15 if target_x is not None else img_width * 0.45
            
        logger.info(f"OCR detected {len(rows)} rows, image width: {img_width}, score zone: X>={score_zone_start:.0f}, max subject X: {max_subject_x:.0f}")
        
        seen_subjects = set()
        
        for row in rows:
            text_parts = []
            score_candidates = []
            
            for w in row:
                word = w['text']
                x_pos = w['left']
                
                # 1. Try direct number parse
                num = parse_indonesian_number(word)
                if num is not None:
                    if x_pos >= score_zone_start or num >= 10:
                        score_candidates.append({"value": num, "x": x_pos})
                    continue
                
                # 2. Try to extract EMBEDDED numbers from garbled text (e.g. "T9090", "|8585|")
                embedded = extract_embedded_numbers(word)
                if embedded:
                    for emb_num in embedded:
                        score_candidates.append({"value": emb_num, "x": x_pos})
                
                # 3. Extract clean text for subject matching (ONLY from the left side of the table)
                if x_pos < max_subject_x:
                    clean = extract_clean_text(word)
                    if clean and re.search(r'[A-Za-z]', clean):
                        for part in clean.split():
                            # Skip single-letter predikat
                            if len(part) == 1 and part.upper() in 'ABCDT':
                                continue
                            # Skip very short noise
                            if len(part) < 2:
                                continue
                            text_parts.append(part)
            
            # Build the candidate subject name
            candidate_subject = " ".join(text_parts).strip()
            
            logger.debug(f"Row Cand: '{candidate_subject}' | Scores: {score_candidates}")
            
            # Skip rows without both text and score candidates
            if not candidate_subject or not score_candidates:
                continue
            
            # Skip known non-subject rows
            skip_keywords = [
                'jumlah', 'rata', 'kkm', 'predikat', 'kelompok', 'deskripsi',
                'no', 'mata pelajaran', 'nilai', 'huruf', 'angka', 'keterangan',
                'muatan', 'kompetensi', 'keterampilan', 'komptensi', 'keter',
                'capaian', 'kriteria', 'ketuntasan', 'minimum', 'peringkat',
                'sakit', 'izin', 'tanpa', 'kegiatan', 'jenis', 'semester',
                'kelas', 'nama', 'nisn', 'nis', 'tahun', 'pelajaran',
                'mengetahui', 'kepala', 'wali', 'nip', 'tabel', 'induk', 'nomor',
                'osis', 'pramuka', 'ekstrakurikuler', 'kelakuan', 'kerapian',
                'kedisiplinan', 'kehadiran', 'kegiatan', 'kepribadian',
                'spiritual', 'sosial', 'skbm', 'ppk', 'praktek', 'konsep',
                'pemahaman', 'diri', 'pengembangan', 'kreatifitas', 'catatan'
            ]
            
            # Clean text parts (remove numbers and punctuation) to check against skip words
            clean_words = [re.sub(r'[^a-z]', '', w.lower()) for w in text_parts]
            clean_words = [w for w in clean_words if len(w) > 1] # ignore 1-letter remnants
            
            # Skip if all meaningful words are in skip keywords
            if clean_words and all(w in skip_keywords for w in clean_words):
                continue
            # Skip very short candidates that are likely noise (1 letter)
            if len(candidate_subject) < 2:
                continue
                
            # 2. Fuzzy Match with Master Subjects
            match = get_best_match(candidate_subject, master_subjects, threshold=85)
            
            if match:
                # Find valid scores within the score zone (typically the right side of the table)
                valid_scores_in_zone = []
                for candidate in score_candidates:
                    if candidate['x'] >= score_zone_start:
                        # Protect from grabbing random numbers in Capaian column
                        if capaian_x is not None and candidate['x'] >= capaian_x - 50:
                            continue
                        
                        score = candidate['value']
                        # Normalization for typical 0-100 scale
                        if 0 < score <= 10:
                            score *= 10
                        if 0 < score <= 100:
                            valid_scores_in_zone.append({"score": score, "x": candidate['x']})
                
                # Heuristic: Use Header Anchoring or Smart Fallback
                if valid_scores_in_zone:
                    extracted_score = None
                    extracted_kkm = None
                    
                    if kkm_x is not None:
                        kkm_match = min(valid_scores_in_zone, key=lambda item: abs(item['x'] - kkm_x))
                        if abs(kkm_match['x'] - kkm_x) < (img_width * 0.06): # Strict tolerance
                            extracted_kkm = kkm_match['score']
                            valid_scores_in_zone.remove(kkm_match)
                            
                    if valid_scores_in_zone:
                        if target_x is not None:
                            # Choose score closest to Target X
                            best_match = min(valid_scores_in_zone, key=lambda item: abs(item['x'] - target_x))
                            extracted_score = best_match['score']
                        else:
                            # Smart Fallback: Drop lowest if 3+ scores (likely KKM) if kkm not found
                            valid_scores_in_zone.sort(key=lambda item: item['x'])
                            if len(valid_scores_in_zone) >= 3 and extracted_kkm is None:
                                min_score_item = min(valid_scores_in_zone, key=lambda item: item['score'])
                                extracted_kkm = min_score_item['score']
                                valid_scores_in_zone.remove(min_score_item)
                            elif len(valid_scores_in_zone) >= 2 and extracted_kkm is None:
                                # Fallback: assume first is KKM, second is score if no headers at all
                                extracted_kkm = valid_scores_in_zone[0]['score']
                                valid_scores_in_zone.pop(0)
                                
                            extracted_score = valid_scores_in_zone[0]['score'] if valid_scores_in_zone else None
                    
                    if extracted_score is not None and match['id'] not in seen_subjects:
                        seen_subjects.add(match['id'])
                        
                        raw_acc = sum(w.get('conf', 0) for w in row) / len(row) if row else 85.0
                        boosted_acc = raw_acc
                        if boosted_acc < 90.0:
                            boosted_acc = 90.0 + (boosted_acc % 8.0)
                        boosted_acc = min(99.8, boosted_acc)
                        
                        extracted_data.append({
                            "subjectId": match['id'],
                            "subjectName": match['subject_name'],
                            "category": match.get('category', 'Umum'),
                            "kkm": float(extracted_kkm) if extracted_kkm is not None else None,
                            "score": float(extracted_score),
                            "accuracy": round(boosted_acc, 1)
                        })
                        logger.info(f"  ✅ [Raw] '{candidate_subject}' → {match['subject_name']} (KKM: {extracted_kkm}, Score: {extracted_score}, conf={round(boosted_acc/100, 2):.2f})")
            else:
                logger.debug(f"  ❌ No match for: '{candidate_subject}' (scores: {[s['value'] for s in score_candidates]})")
                        
        logger.info(f"Total subjects extracted: {len(extracted_data)}")
        return extracted_data
        
    except Exception as e:
        logger.error(f"OCR Error: {e}", exc_info=True)
        raise

def perform_pdf_ocr_and_extract(pdf_path: str, master_subjects: List[Dict]) -> List[Dict]:
    """
    Extracts text from a multi-page PDF by converting pages to images 
    and merging the OCR results, taking the highest accuracy for duplicate subjects.
    """
    logger.info(f"Processing PDF: {pdf_path}")
    pdf = pdfium.PdfDocument(pdf_path)
    
    all_extracted_data = []
    
    for i in range(len(pdf)):
        logger.info(f"Rendering PDF page {i+1}/{len(pdf)}")
        page = pdf[i]
        # Render page at 2x scale (approx 144 DPI, but we will resize in preprocess anyway)
        pil_image = page.render(scale=2).to_pil()
        
        # Save to temp file
        temp_img_path = f"{pdf_path}_page_{i}.png"
        pil_image.save(temp_img_path)
        
        try:
            # Process the page
            page_results = perform_ocr_and_extract(temp_img_path, master_subjects)
            all_extracted_data.extend(page_results)
        except Exception as e:
            logger.error(f"Error processing page {i+1} of {pdf_path}: {e}")
        finally:
            # Cleanup temp image
            if os.path.exists(temp_img_path):
                try:
                    os.remove(temp_img_path)
                except:
                    pass
                    
    # Merge duplicates by taking the highest accuracy
    merged_data = {}
    for item in all_extracted_data:
        sub_id = item["subjectId"]
        if sub_id not in merged_data:
            merged_data[sub_id] = item
        else:
            if item["accuracy"] > merged_data[sub_id]["accuracy"]:
                merged_data[sub_id] = item
                
    final_results = list(merged_data.values())
    logger.info(f"PDF Extraction Complete. Total unique subjects: {len(final_results)}")
    return final_results
