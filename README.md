# Document OCR System (Backend Service)

This **(New Student Admissions/PPDB)** system is an application designed to automate the reading of grades from student report card documents. The system combines **Computer Vision**, **Optical Character Recognition (OCR)**, and lightweight **Natural Language Processing (NLP)** to read messy report card photos, intelligently remove table lines, and automatically extract grades.

---

## Technologies Used

This project is a Backend API service built with modern Python technologies.

### Backend

- **FastAPI**: A blazing-fast Python API framework (based on Asynchronous) for serving web requests.
- **Tesseract OCR**: An advanced optical character reading engine (tuned with Page Segmentation Mode 6).
- **OpenCV (cv2)**: Runs advanced Computer Vision (Image Manipulation) to perform Grayscale Contour Painting (painting table lines white so text is unobstructed).
- **TheFuzz**: A Natural Language Processing engine based on the Levenshtein Distance algorithm to correct the spelling of subject names (e.g., "Pdidikan Pancasla" to "Pendidikan Pancasila").
- **Uvicorn**: A lightning-fast ASGI Web Server to run the FastAPI application.

---

## System Flow

How does the application read report card grades from the initial upload? Here is the flow:

1. **Asynchronous Upload (Backend API):**
   The `POST /api/v1/academic/report/upload` endpoint receives the photos and saves them into the `uploads/` folder. The API immediately provides a `documentId` and triggers a background worker (`BackgroundTasks`) to run.
2. **Computer Vision & Painting (Background Task):**
   The engine executes `preprocess_image()`. This function converts the photo to Black and White (Grayscale). Then it detects all table line coordinates (`vertical_lines` & `horizontal_lines`). These lines are then **painted white** so they disappear without cutting into the original text pixels.
3. **Text Extraction & Mapping (Background Task):**
   The cleaned image is passed to Tesseract via the `perform_ocr_and_extract()` function. Tesseract reads word by word. Aligned words are merged into complete lines. The `get_best_match()` function then corrects the Subject names, and a heuristic logic is used to distinguish the passing grade threshold (KKM) from the student's Actual Final Grade.
4. **Polling & Rendering (Client):**
   The client periodically calls the `GET /api/v1/academic/report/{documentId}/result` route. Once the status becomes `SUCCESS`, the grade results (complete with Confidence Accuracy in percentage format) are returned.

---

## How to Run (Development Mode)

### 1. Running the Backend Server (API)

Use the terminal (Git Bash / PowerShell):

```bash
# 1. Ensure you are in the project root directory

# 2. Setup Environment Variables
cp .env.example .env
# Edit .env with your configuration

# 3. Activate Python Virtual Environment (example for Windows/Git Bash)
source venv/Scripts/activate
# Or for PowerShell: .\venv\Scripts\Activate.ps1

# 4. Install dependencies (only for the first time)
pip install -r requirements.txt

# 5. Start the FastAPI Server
uvicorn app.main:app --reload
```

The Backend will be running at `http://localhost:8000`
You can access the API Documentation (Swagger UI) at `http://localhost:8000/docs`
