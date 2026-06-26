from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException
from app.models.schemas import OCRResultResponse
from app.services.ocr_service import perform_ocr_and_extract, debug_ocr_raw_text
from app.services.mapping_engine import get_best_match
import uuid
import os
import time
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/academic")

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# IN-MEMORY DATA STORES
DOCUMENTS_STORE = {}
FINAL_ACADEMIC_DATA = []

# ============================================================
# MASTER SUBJECTS
# ============================================================
MASTER_SUBJECTS = [
    # --- Kelompok Agama Islam ---
    {"id": 1,  "subject_name": "Pendidikan Agama Islam", "aliases": ["PAI", "Agama Islam", "Pendidikan Agama"], "category": "IT Islam Terpadu"},
    {"id": 2,  "subject_name": "Al-Qur'an Hadits", "aliases": ["Quran Hadits", "Qur'an Hadits", "Al Quran Hadis", "Qur an Hadits"], "category": "IT Islam Terpadu"},
    {"id": 3,  "subject_name": "Akidah Akhlak", "aliases": ["Aqidah Akhlaq", "Aqidah Akhlak"], "category": "IT Islam Terpadu"},
    {"id": 4,  "subject_name": "Fikih", "aliases": ["Fiqh", "Fiqih"], "category": "IT Islam Terpadu"},
    {"id": 5,  "subject_name": "Sejarah Kebudayaan Islam", "aliases": ["SKI"], "category": "IT Islam Terpadu"},
    
    # --- Kelompok Umum Wajib ---
    {"id": 6,  "subject_name": "Pendidikan Kewarganegaraan", "aliases": ["PKN", "PPKn", "Pendidikan Pancasila", "Pendidikan Pancasila dan Kewarganegaraan", "PRN"], "category": "Umum"},
    {"id": 7,  "subject_name": "Bahasa Indonesia", "aliases": ["B. Ind", "Bhs Indonesia", "B.Indonesia"], "category": "Umum"},
    {"id": 8,  "subject_name": "Bahasa Inggris", "aliases": ["B. Ing", "English", "Bhs Inggris", "Bahasa Ingris", "B.Inggris"], "category": "Umum"},
    {"id": 9,  "subject_name": "Matematika", "aliases": ["MTK", "Mtk", "Matematika Wajib", "Matematika Umum", "nngn aika", "nngn"], "category": "Umum"},
    {"id": 10, "subject_name": "Ilmu Pengetahuan Alam", "aliases": ["IPA", "Sains"], "category": "Umum"},
    {"id": 11, "subject_name": "Ilmu Pengetahuan Sosial", "aliases": ["IPS"], "category": "Umum"},
    
    # --- Kelompok Sains (SMA/MA) ---
    {"id": 12, "subject_name": "Fisika", "aliases": ["Fsk"], "category": "Umum"},
    {"id": 13, "subject_name": "Kimia", "aliases": ["Kma"], "category": "Umum"},
    {"id": 14, "subject_name": "Biologi", "aliases": ["Bio"], "category": "Umum"},
    
    # --- Kelompok Keterampilan ---
    {"id": 15, "subject_name": "Seni Budaya", "aliases": ["Seni Budaya dan Prakarya", "SBK", "Kesenian", "Seni"], "category": "Umum"},
    {"id": 16, "subject_name": "PJOK", "aliases": ["Penjas", "Pendidikan Jasmani", "Pend. Jasmani Olahraga dan Kesehatan", "Penjas Olah Raga", "Pendidikan Jasmani Olahraga dan Kesehatan", "Pendidikan Jasmani & Olah Raga"], "category": "Umum"},
    {"id": 17, "subject_name": "Prakarya", "aliases": ["Prakarya dan Kewirausahaan", "Prakarya dan/atau Informatika"], "category": "Umum"},
    {"id": 18, "subject_name": "Teknologi Informasi", "aliases": ["TIK", "Informatika", "Teknologi Informasi dan Komunikasi", "T I K"], "category": "Umum"},
    
    # --- Kelompok Bahasa & Muatan Lokal ---
    {"id": 19, "subject_name": "Bahasa Arab", "aliases": ["B. Arab", "Bhs Arab"], "category": "IT Islam Terpadu"},
    {"id": 20, "subject_name": "Bahasa Sunda", "aliases": ["B. Sunda", "Bhs Sunda"], "category": "Umum"},
    {"id": 21, "subject_name": "Bahasa Madura", "aliases": ["B. Madura", "Bhs Madura"], "category": "Umum"},
    {"id": 22, "subject_name": "Bahasa Jawa", "aliases": ["B. Jawa", "Bhs Jawa"], "category": "Umum"},
    {"id": 101, "subject_name": "Bahasa Mandarin", "aliases": ["Mandarin"], "category": "Internasional"},
    {"id": 102, "subject_name": "Bahasa Jepang", "aliases": ["B. Jepang"], "category": "Internasional"},
    {"id": 103, "subject_name": "Sastra Inggris", "aliases": ["Sastra"], "category": "Internasional"},
    
    # --- Kelompok Sejarah ---
    {"id": 23, "subject_name": "Sejarah", "aliases": ["Sejarah Indonesia", "Sejarah Wajib"], "category": "Umum"},
    
    # --- Kelompok Pesantren / Madrasah ---
    {"id": 24, "subject_name": "Nahwu Sharraf", "aliases": ["Nahwu/Sharraf", "Nahwu", "Sharraf"], "category": "IT Islam Terpadu"},
    {"id": 25, "subject_name": "Bulughul Marom", "aliases": ["Bulughul Maram"], "category": "IT Islam Terpadu"},
    {"id": 26, "subject_name": "Kifayatul Akhyar", "aliases": ["Kifayatul Ahyar"], "category": "IT Islam Terpadu"},
    {"id": 27, "subject_name": "Husnul Hamidi", "aliases": ["Husnul Hamidiyah"], "category": "IT Islam Terpadu"},
    {"id": 28, "subject_name": "Tafsir", "aliases": ["Tafsir Quran"], "category": "IT Islam Terpadu"},
    {"id": 29, "subject_name": "BTQ", "aliases": ["Baca Tulis Quran", "Baca Tulis Al-Quran", "Baca Tulis Qur'an"], "category": "IT Islam Terpadu"},
    {"id": 30, "subject_name": "Khalighrafi", "aliases": ["Kaligrafi", "Khat"], "category": "IT Islam Terpadu"},
    {"id": 31, "subject_name": "Kepesantrenan", "aliases": ["Kepesantrenan"], "category": "IT Islam Terpadu"},
    {"id": 32, "subject_name": "Kitab Kuning", "aliases": [], "category": "IT Islam Terpadu"},
    {"id": 33, "subject_name": "Tarikh Tasyri", "aliases": ["Tarikh Tasyri'"], "category": "IT Islam Terpadu"},
    {"id": 34, "subject_name": "I'dzatun Nasyi'in", "aliases": ["Idzatun Nasyi'in"], "category": "IT Islam Terpadu"},
    
    # --- Ekonomi / Sosiologi / Geografi / Antropologi (SMA) ---
    {"id": 35, "subject_name": "Ekonomi", "aliases": [], "category": "Umum"},
    {"id": 36, "subject_name": "Sosiologi", "aliases": [], "category": "Umum"},
    {"id": 37, "subject_name": "Geografi", "aliases": [], "category": "Umum"},
    {"id": 38, "subject_name": "Antropologi", "aliases": [], "category": "Umum"},
    
    # --- Agama Non-Islam ---
    {"id": 39, "subject_name": "Pendidikan Agama Kristen", "aliases": ["Agama Kristen"], "category": "Non Islam"},
    {"id": 40, "subject_name": "Pendidikan Agama Katolik", "aliases": ["Agama Katolik"], "category": "Non Islam"},
    {"id": 41, "subject_name": "Pendidikan Agama Hindu", "aliases": ["Agama Hindu"], "category": "Non Islam"},
    {"id": 42, "subject_name": "Pendidikan Agama Buddha", "aliases": ["Agama Buddha"], "category": "Non Islam"},
    {"id": 43, "subject_name": "Pendidikan Agama Khonghucu", "aliases": ["Agama Khonghucu"], "category": "Non Islam"},
    
    # --- Keterampilan & Kejuruan ---
    {"id": 44, "subject_name": "Prakarya", "aliases": ["Prakarya dan Kewirausahaan", "PKWU", "Kerajinan"], "category": "Umum"},
    {"id": 45, "subject_name": "Muatan Lokal", "aliases": ["Mulok"], "category": "Umum"},
    {"id": 47, "subject_name": "Bimbingan dan Konseling", "aliases": ["BK", "Bimbingan Konseling"], "category": "Umum"},
    
    # --- Rumpun Seni Khusus ---
    {"id": 48, "subject_name": "Seni Musik", "aliases": [], "category": "Umum"},
    {"id": 49, "subject_name": "Seni Rupa", "aliases": [], "category": "Umum"},
    {"id": 50, "subject_name": "Seni Tari", "aliases": [], "category": "Umum"},
    {"id": 51, "subject_name": "Seni Teater", "aliases": [], "category": "Umum"},
    
    # --- Kejuruan SMK ---
    {"id": 60, "subject_name": "Kompetensi Kejuruan", "aliases": ["Kejuruan", "Kompetensi Keahlian", "Produktif"], "category": "SMK"},
    {"id": 61, "subject_name": "Kewirausahaan", "aliases": ["Wirausaha"], "category": "SMK"},
    {"id": 62, "subject_name": "Desain Grafis", "aliases": ["Desain Grafis", "DKV", "Desain Komunikasi Visual"], "category": "SMK"},
    {"id": 63, "subject_name": "Ketrampilan Komputer dan Pengolahan Informasi", "aliases": ["KKPI", "Ketrampilan Komputer"], "category": "SMK"},
]


def process_ocr_background(document_id: str, image_path: str):
    """
    Background task to run OCR and Fuzzy Mapping.
    """
    start_time = time.time()
    try:
        # Extract and map data using Bounding Box Clustering
        if image_path.lower().endswith(".pdf"):
            mapped_results = perform_pdf_ocr_and_extract(image_path, MASTER_SUBJECTS)
        else:
            mapped_results = perform_ocr_and_extract(image_path, MASTER_SUBJECTS)
        
        end_time = time.time()
        processing_time = round(end_time - start_time, 2)
        
        # Update Document Status in Memory
        if document_id in DOCUMENTS_STORE:
            doc = DOCUMENTS_STORE[document_id]
            doc["status"] = "SUCCESS"
            doc["extracted_data"] = mapped_results
            doc["processingTime"] = processing_time
            
            if mapped_results:
                doc["accuracy"] = round(
                    sum(d["accuracy"] for d in mapped_results if d.get("accuracy") is not None) / len(mapped_results), 1
                )
            else:
                doc["accuracy"] = 0.0
                
        logger.info(f"Document {document_id}: extracted {len(mapped_results)} subjects in {processing_time}s")
                
    except Exception as e:
        end_time = time.time()
        if document_id in DOCUMENTS_STORE:
            DOCUMENTS_STORE[document_id]["status"] = "FAILED"
            DOCUMENTS_STORE[document_id]["error"] = str(e)
            DOCUMENTS_STORE[document_id]["processingTime"] = round(end_time - start_time, 2)
        logger.error(f"Background Task Error for {document_id}: {e}", exc_info=True)


@router.post("/report/upload", response_model=OCRResultResponse)
async def upload_report(file: UploadFile = File(...)):
    try:
        filename = file.filename if file.filename else "unknown.png"
        if not filename.lower().endswith(('.png', '.jpg', '.jpeg', '.pdf')):
            raise HTTPException(status_code=400, detail=f"Invalid file type: {filename}. Allowed: png, jpg, jpeg, pdf")
            
        doc_id = f"DOC{uuid.uuid4().hex[:8].upper()}"
        file_path = os.path.join(UPLOAD_DIR, f"{doc_id}_{filename}")
        
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
            
        # Save document state in memory
        DOCUMENTS_STORE[doc_id] = {
            "id": doc_id,
            "status": "PROCESSING",
            "confidence": 0.0,
            "accuracy": 0.0,
            "processingTime": 0.0,
            "extracted_data": [],
            "image_path": file_path
        }
        
        # Run OCR Synchronously instead of background task
        process_ocr_background(doc_id, file_path)
        
        doc = DOCUMENTS_STORE[doc_id]
        
        return {
            "documentId": doc["id"],
            "status": doc["status"],
            "accuracy": doc.get("accuracy", doc.get("confidence", 0.0)),
            "processingTime": doc.get("processingTime", 0.0),
            "subjects": doc.get("extracted_data", [])
        }
    except Exception as e:
        import traceback
        err_msg = traceback.format_exc()
        logger.error(f"Upload Route Error: {err_msg}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/report/{documentId}/debug")
async def debug_ocr(documentId: str):
    """
    Debug endpoint: shows raw PaddleOCR text, bounding boxes, and detected rows.
    """
    if documentId not in DOCUMENTS_STORE:
        raise HTTPException(status_code=404, detail="Document not found")
    
    doc = DOCUMENTS_STORE[documentId]
    image_path = doc.get("image_path", "")
    
    if not image_path or not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Image file not found")
    
    debug_data = debug_ocr_raw_text(image_path)
    return debug_data


