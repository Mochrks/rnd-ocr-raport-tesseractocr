# Document OCR System

This ** (New Student Admissions/PPDB)** system is an _Enterprise-class_ _Fullstack_ application designed to automate the reading of grades from student report card documents. The system combines **Computer Vision**, **Optical Character Recognition (OCR)**, and lightweight **Natural Language Processing (NLP)** to read messy report card photos, intelligently remove table lines, and automatically extract grades.

---

## Technologies Used

This project has been restructured into 2 main parts: **Frontend** and **Backend**, using cutting-edge modern technologies.

### Frontend (`/frontend`)

- **Next.js 14 (App Router)**: The main React framework for super-fast web performance and modern _routing_.
- **Tailwind CSS & Glassmorphism**: Utility _styling_ for designing responsive _Premium Dark Mode_ interfaces.
- **Shadcn UI**: An expertly designed component library (Radix UI) to present perfect UI elements like _Cards_, _Data Tables_, and _Accordions_.
- **React Dropzone**: Handles interactive _Multi-file Upload_ (multiple photos at once).
- **Axios**: A robust _HTTP Client_ for asynchronous communication between _Frontend_ and _Backend_.

### Backend (`/backend`)

- **FastAPI**: A blazing-fast Python API framework (based on _Asynchronous_) for serving web requests.
- **Tesseract OCR**: An advanced optical character reading engine (tuned with `Page Segmentation Mode 6`).
- **OpenCV (`cv2`)**: Runs advanced _Computer Vision_ (Image Manipulation) to perform **Grayscale Contour Painting** (painting table lines white so text is unobstructed).
- **TheFuzz**: A _Natural Language Processing_ engine based on the _Levenshtein Distance_ algorithm to correct the spelling of subject names (e.g., "Pdidikan Pancasla" to "Pendidikan Pancasila").
- **Uvicorn**: A lightning-fast ASGI Web Server to run the FastAPI application.

---

## System Flow

How does the application read report card grades from the initial upload until they appear on the screen? Here is the flow:

1. **Multi-File Dropzone (Frontend):**
   The user drags & drops report card images/pdfs onto the _browser_ screen. The frontend asynchronously uses the `onDrop()` function to send them via AJAX to the Backend.
2. **Asynchronous Upload (Backend API):**
   The `POST /upload` _endpoint_ in the Backend receives the photos and immediately saves them into the `backend/uploads/` folder. Instead of holding the user screen for _loading_, the API immediately provides a Receipt number / `documentId` and triggers a background worker (`BackgroundTasks`) to run.
3. **Computer Vision & Painting (Backend Task):**
   The engine executes `preprocess_image()`. This function converts the photo to Black and White (Grayscale). Then it detects all table line coordinates (`vertical_lines` & `horizontal_lines`). These lines are then **painted white** so they disappear without cutting into the original text pixels.
4. **Text Extraction & Mapping (Backend Task):**
   The cleaned image is passed to Tesseract via the `perform_ocr_and_extract()` function. Tesseract reads word by word. Aligned words are merged into complete lines. The `get_best_match()` function then corrects the _Subject_ names, and a `max()` heuristic logic is used to distinguish the passing grade threshold (KKM) from the student's Actual Final Grade.
5. **Polling & Rendering (Frontend):**
   While the backend is busy computing, the Frontend periodically runs the `pollResult()` function hitting the `GET /result` route every 2 seconds. Once the status becomes `SUCCESS`, the _loading_ bar will disappear, and the grade results (complete with _Confidence Accuracy_ in percentage format) are displayed neatly in a table component.

---

## 🚀 How to Run (Development Mode)

Since the architecture is divided into two, you must start the _Backend_ and _Frontend_ simultaneously using **two separate terminal windows**.

### 1. Running the Backend Server (API)

Use the first terminal (Git Bash / PowerShell):

```bash
# 1. Enter the backend folder
cd backend

# 2. Activate Python Virtual Environment (example for Windows/Git Bash)
source ../venv/Scripts/activate
# Or for PowerShell: ..\venv\Scripts\Activate.ps1

# 3. Install dependencies (only for the first time)
pip install -r requirements.txt

# 4. Start the FastAPI Server
uvicorn app.main:app --reload
```

_The Backend will be running at `http://localhost:8000`_

### 2. Running the Frontend UI (Web)

Open the second terminal:

```bash
# 1. Enter the frontend folder
cd frontend

# 2. Install Node.js dependencies (only for the first time)
npm install

# 3. Start the Node.js Next App server
npm run dev
```

_The Frontend will be running at `http://localhost:3000`_

Please open `http://localhost:3000` in your _browser_, drop a report card image, and let the AI magic work!
