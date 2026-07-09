import time
import logging
from app.services.ocr_service import perform_ocr_and_extract, perform_pdf_ocr_and_extract
from app.data.store import store
from app.data.constants import MASTER_SUBJECTS

logger = logging.getLogger(__name__)

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
        doc = store.get_document(document_id)
        if doc:
            updates = {
                "status": "SUCCESS",
                "extracted_data": mapped_results,
                "processingTime": processing_time
            }
            
            if mapped_results:
                updates["accuracy"] = round(
                    sum(d["accuracy"] for d in mapped_results if d.get("accuracy") is not None) / len(mapped_results), 1
                )
            else:
                updates["accuracy"] = 0.0
                
            store.update_document(document_id, updates)
                
        logger.info(f"Document {document_id}: extracted {len(mapped_results)} subjects in {processing_time}s")
                
    except Exception as e:
        end_time = time.time()
        doc = store.get_document(document_id)
        if doc:
            store.update_document(document_id, {
                "status": "FAILED",
                "error": str(e),
                "processingTime": round(end_time - start_time, 2)
            })
        logger.error(f"Background Task Error for {document_id}: {e}", exc_info=True)
