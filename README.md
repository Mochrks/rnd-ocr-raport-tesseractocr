# Document OCR System

Sistem ** (Penerimaan Peserta Didik Baru)** ini adalah aplikasi _Fullstack_ kelas _Enterprise_ yang dirancang untuk mengotomatiskan pembacaan nilai dari dokumen rapor siswa. Sistem ini menggabungkan **Computer Vision**, **Optical Character Recognition (OCR)**, dan **Natural Language Processing (NLP)** ringan untuk membaca foto rapor yang berantakan, menghapus garis tabel secara cerdas, dan mengekstraksi nilai secara otomatis.

---

## Teknologi yang Digunakan

Proyek ini telah direstrukturisasi menjadi 2 bagian utama: **Frontend** dan **Backend**, menggunakan teknologi modern mutakhir.

### Frontend (`/frontend`)

- **Next.js 14 (App Router)**: Framework React utama untuk performa web super cepat dan _routing_ modern.
- **Tailwind CSS & Glassmorphism**: _Styling_ utilitas untuk merancang desain antarmuka _Premium Dark Mode_ yang responsif.
- **Shadcn UI**: Pustaka komponen yang dirancang dengan ahli (Radix UI) untuk menyajikan elemen UI sempurna seperti _Card_, _Data Tables_, dan _Accordion_.
- **React Dropzone**: Menangani _Upload Multi-file_ interaktif (banyak foto sekaligus).
- **Axios**: _HTTP Client_ tangguh untuk komunikasi asinkron antara _Frontend_ dan _Backend_.

### Backend (`/backend`)

- **FastAPI**: Kerangka kerja API Python yang sangat cepat (berbasis _Asynchronous_) untuk melayani permintaan web.
- **Tesseract OCR**: Mesin pembaca karakter optik tingkat lanjut (disetel dengan `Page Segmentation Mode 6`).
- **OpenCV (`cv2`)**: Menjalankan _Computer Vision_ (Manipulasi Citra) tingkat lanjut untuk melakukan **Grayscale Contour Painting** (mengecat putih garis tabel agar huruf bebas hambatan).
- **TheFuzz**: Mesin _Natural Language Processing_ berbasis algoritma _Levenshtein Distance_ untuk mengoreksi ejaan nama pelajaran ("Pdidikan Pancasla" menjadi "Pendidikan Pancasila").
- **Uvicorn**: Server Web ASGI super cepat untuk menjalankan aplikasi FastAPI.

---

## Alur Sistem (System Flow)

Bagaimana aplikasi membaca nilai rapor dari awal unggah hingga muncul di layar? Berikut adalah alurnya:

1. **Multi-File Dropzone (Frontend):**
   Pengguna menggeser (drag & drop) gambar/pdf rapor ke layar _browser_. Frontend secara asinkron menggunakan fungsi `onDrop()` untuk mengirimkannya via AJAX ke Backend.
2. **Asynchronous Upload (Backend API):**
   _Endpoint_ `POST /upload` di Backend menerima foto tersebut dan langsung menyimpannya ke dalam folder `backend/uploads/`. Daripada menahan layar pengguna untuk _loading_, API akan langsung memberikan nomor Resi / `documentId` dan menyuruh mesin pekerja (`BackgroundTasks`) berjalan di latar belakang.
3. **Computer Vision & Painting (Backend Task):**
   Mesin mengeksekusi `preprocess_image()`. Fungsi ini mengubah foto menjadi Hitam-Putih (Grayscale). Kemudian ia mendeteksi seluruh koordinat garis tabel (`vertical_lines` & `horizontal_lines`). Garis-garis ini kemudian **dicat warna putih** agar hilang tanpa memotong piksel teks aslinya.
4. **Ekstraksi Text & Mapping (Backend Task):**
   Gambar yang bersih diberikan ke Tesseract via fungsi `perform_ocr_and_extract()`. Tesseract membaca posisi kata per kata. Kata-kata sejajar digabung menjadi baris utuh. Fungsi `get_best_match()` lalu mengoreksi nama _Mata Pelajaran_ dan logika heuristik `max()` digunakan untuk membedakan mana yang angka KKM dan mana Nilai Akhir Asli siswa.
5. **Polling & Rendering (Frontend):**
   Sementara backend sibuk menghitung, Frontend secara berkala menjalankan fungsi `pollResult()` menembak rute `GET /result` setiap 2 detik. Begitu status menjadi `SUCCESS`, bar _loading_ akan menghilang dan hasil nilai (lengkap dengan _Confidence Accuracy_ berformat persen) ditampilkan sangat rapi ke dalam komponen tabel.

---

## 🚀 Cara Menjalankan (Development Mode)

Karena arsitekturnya sudah terbagi menjadi dua, Anda wajib menghidupkan _Backend_ dan _Frontend_ secara bersamaan menggunakan **dua jendela terminal** yang terpisah.

### 1. Menjalankan Server Backend (API)

Gunakan terminal pertama (Git Bash / PowerShell):

```bash
# 1. Masuk ke folder backend
cd backend

# 2. Aktifkan Virtual Environment Python (contoh untuk Windows/Git Bash)
source ../venv/Scripts/activate
# Atau untuk PowerShell: ..\venv\Scripts\Activate.ps1

# 3. Instal dependensi (hanya untuk pertama kali)
pip install -r requirements.txt

# 4. Nyalakan Server API FastAPI
uvicorn app.main:app --reload
```

```bash
# 1. Masuk ke folder backend
cd backend-paddleocr

# 2. Aktifkan Virtual Environment Python (contoh untuk Windows/Git Bash)
source ../venv-paddle/Scripts/activate

# Atau untuk PowerShell: ..\venv\Scripts\Activate.ps1

# 3. Instal dependensi (hanya untuk pertama kali)
pip install -r requirements.txt

# 4. Nyalakan Server API FastAPI
uvicorn app.main:app --reload
```

_Backend akan hidup di `http://localhost:8000`_

### 2. Menjalankan UI Frontend (Web)

Buka terminal kedua:

```bash
# 1. Masuk ke folder frontend
cd frontend

# 2. Instal dependensi Node.js (hanya untuk pertama kali)
npm install

# 3. Nyalakan server Node.js Next App
npm run dev
```

_Frontend akan hidup di `http://localhost:3000`_

Silakan buka `http://localhost:3000` di _browser_, jatuhkan gambar rapor, dan biarkan keajaiban AI bekerja!
