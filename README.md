<h1 align="center"> Document OCR System (Backend Service)</h1>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB" alt="Python" />
  <img src="https://img.shields.io/badge/FastAPI-Latest-009688" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Tesseract_OCR-5.x-4285F4" alt="Tesseract OCR" />
  <img src="https://img.shields.io/badge/OpenCV-4.x-5C3EE8" alt="OpenCV" />
  <img src="https://img.shields.io/badge/TheFuzz-Latest-FF9800" alt="TheFuzz" />
  <img src="https://img.shields.io/badge/Uvicorn-Latest-499848" alt="Uvicorn" />
</p>

<p align="center">
  <img src="https://skillicons.dev/icons?i=python,fastapi,opencv,git,docker" alt="Tech Stack Icons" />
</p>

---

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

# Or for PowerShell:
.\venv\Scripts\Activate.ps1

# 4. Install dependencies (only for the first time)
pip install -r requirements.txt

# 5. Start the FastAPI Server
uvicorn app.main:app --reload
```

The Backend will be running at `http://localhost:8000`

You can access the API Documentation (Swagger UI) at `http://localhost:8000/docs`


## Connect with me:

[![GitHub](https://img.shields.io/badge/GitHub-333?style=for-the-badge&logo=github&logoColor=white)](https://github.com/mochrks)
[![YouTube](https://img.shields.io/badge/YouTube-FF0000?style=for-the-badge&logo=youtube&logoColor=white)](https://youtube.com/@Gdvisuel)
[![Instagram](https://img.shields.io/badge/Instagram-E4405F?style=for-the-badge&logo=instagram&logoColor=white)](https://instagram.com/mochrks)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white)](https://linkedin.com/in/mochrks)
[![Behance](https://img.shields.io/badge/Behance-1769FF?style=for-the-badge&logo=behance&logoColor=white)](https://behance.net/mochrks)
[![Dribbble](https://img.shields.io/badge/Dribbble-EA4C89?style=for-the-badge&logo=dribbble&logoColor=white)](https://dribbble.com/mochrks)
