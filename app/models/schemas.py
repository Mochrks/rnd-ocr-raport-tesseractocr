from pydantic import BaseModel, Field
from typing import List, Optional

class SubjectScore(BaseModel):
    subjectId: Optional[int] = None
    subjectName: str
    category: Optional[str] = "Umum"
    kkm: Optional[float] = None
    score: float
    accuracy: Optional[float] = None

class SubjectScoreConfirm(BaseModel):
    subjectId: int
    score: float

class OCRResultResponse(BaseModel):
    documentId: str
    status: str
    accuracy: Optional[float] = None
    processingTime: Optional[float] = None
    subjects: Optional[List[SubjectScore]] = []

class ConfirmRequest(BaseModel):
    documentId: str
    subjects: List[SubjectScoreConfirm]

class FinalSaveRequest(BaseModel):
    studentId: str
    academicData: List[SubjectScoreConfirm]

class MasterSubjectCreate(BaseModel):
    subject_name: str
    aliases: List[str] = []
