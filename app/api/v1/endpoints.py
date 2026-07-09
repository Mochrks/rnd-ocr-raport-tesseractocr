from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException
from app.models.schemas import OCRResultResponse, ConfirmRequest, FinalSaveRequest
from app.services.ocr_service import debug_ocr_raw_text
from app.services.background_tasks import process_ocr_background
from app.data.store import store
from app.core.config import settings
import uuid
import os
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix=settings.API_V1_STR)

@router.post("/report/upload")
async def upload_report(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    try:
        filename = file.filename if file.filename else "unknown.png"
        if not filename.lower().endswith(('.png', '.jpg', '.jpeg', '.pdf')):
            raise HTTPException(status_code=400, detail=f"Invalid file type: {filename}. Allowed: png, jpg, jpeg, pdf")
            
        doc_id = f"DOC{uuid.uuid4().hex[:8].upper()}"
        file_path = os.path.join(settings.UPLOAD_DIR, f"{doc_id}_{filename}")
        
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
            
        # Save document state in memory
        store.set_document(doc_id, {
            "id": doc_id,
            "status": "PROCESSING",
            "confidence": 0.0,
            "accuracy": 0.0,
            "processingTime": 0.0,
            "extracted_data": [],
            "image_path": file_path
        })
        
        # Run background OCR
        background_tasks.add_task(process_ocr_background, doc_id, file_path)
        
        return {"documentId": doc_id, "status": "PROCESSING"}
    except Exception as e:
        import traceback
        err_msg = traceback.format_exc()
        logger.error(f"Upload Route Error: {err_msg}")
        return {"error": str(e), "traceback": err_msg}

@router.get("/report/{documentId}/result", response_model=OCRResultResponse)
async def get_ocr_result(documentId: str):
    doc = store.get_document(documentId)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    return {
        "documentId": doc["id"],
        "status": doc["status"],
        "accuracy": doc.get("accuracy", doc.get("confidence", 0.0)),
        "processingTime": doc.get("processingTime", 0.0),
        "subjects": doc["extracted_data"]
    }

@router.get("/report/{documentId}/debug")
async def debug_ocr(documentId: str):
    """
    Debug endpoint: shows raw OCR text and detected rows.
    """
    doc = store.get_document(documentId)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    image_path = doc.get("image_path", "")
    
    if not image_path or not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Image file not found")
    
    debug_data = debug_ocr_raw_text(image_path)
    return debug_data

@router.post("/report/confirm")
async def confirm_results(request: ConfirmRequest):
    doc = store.get_document(request.documentId)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    store.update_document(request.documentId, {
        "extracted_data": [item.dict() for item in request.subjects],
        "status": "CONFIRMED"
    })
    
    return {"message": "Data confirmed successfully."}

@router.post("/")
async def final_save(request: FinalSaveRequest):
    for item in request.academicData:
        store.add_final_academic_data({
            "student_id": request.studentId,
            "subject_id": item.subjectId,
            "score": item.score
        })
        
    return {
        "message": "Academic data saved successfully (In-Memory)", 
        "total_records": len(store.get_all_final_academic_data())
    }
