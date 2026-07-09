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
    {"id": 9,  "subject_name": "Matematika", "aliases": ["MTK", "Mtk", "Matematika Wajib", "Matematika Umum"], "category": "Umum"},
    {"id": 10, "subject_name": "Ilmu Pengetahuan Alam", "aliases": ["IPA", "Sains"], "category": "Umum"},
    {"id": 11, "subject_name": "Ilmu Pengetahuan Sosial", "aliases": ["IPS"], "category": "Umum"},
    
    # --- Kelompok Sains (SMA/MA) ---
    {"id": 12, "subject_name": "Fisika", "aliases": ["Fsk"], "category": "Umum"},
    {"id": 13, "subject_name": "Kimia", "aliases": ["Kma"], "category": "Umum"},
    {"id": 14, "subject_name": "Biologi", "aliases": ["Bio"], "category": "Umum"},
    
    # --- Kelompok Keterampilan ---
    {"id": 15, "subject_name": "Seni Budaya", "aliases": ["Seni Budaya dan Prakarya", "SBK", "Kesenian", "Seni"], "category": "Umum"},
    {"id": 16, "subject_name": "PJOK", "aliases": ["Penjas", "Pendidikan Jasmani", "Pend. Jasmani Olahraga dan Kesehatan", "Penjas Olah Raga", "Pendidikan Jasmani Olahraga dan Kesehatan", "PIOK", "PJOK"], "category": "Umum"},
    {"id": 17, "subject_name": "Prakarya", "aliases": ["Prakarya dan Kewirausahaan", "Prakarya dan/atau Informatika"], "category": "Umum"},
    {"id": 18, "subject_name": "Teknologi Informasi", "aliases": ["TIK", "Informatika", "Teknologi Informasi dan Komunikasi", "T I K", "IK"], "category": "Umum"},
    
    # --- Kelompok Bahasa & Muatan Lokal ---
    {"id": 19, "subject_name": "Bahasa Arab", "aliases": ["B. Arab", "Bhs Arab"], "category": "IT Islam Terpadu"},
    {"id": 20, "subject_name": "Bahasa Sunda", "aliases": ["B. Sunda", "Bhs Sunda"], "category": "Umum"},
    {"id": 21, "subject_name": "Bahasa Madura", "aliases": ["B. Madura", "Bhs Madura"], "category": "Umum"},
    {"id": 22, "subject_name": "Bahasa Jawa", "aliases": ["B. Jawa", "Bhs Jawa"], "category": "Umum"},
    {"id": 101, "subject_name": "Bahasa Mandarin", "aliases": ["Mandarin"], "category": "Internasional"},
    {"id": 102, "subject_name": "Bahasa Jepang", "aliases": ["B. Jepang"], "category": "Internasional"},
    {"id": 103, "subject_name": "Sastra Inggris", "aliases": ["Sastra"], "category": "Internasional"},
    {"id": 104, "subject_name": "Bahasa Jerman", "aliases": ["B. Jerman"], "category": "Internasional"},
    {"id": 105, "subject_name": "Bahasa Prancis", "aliases": ["B. Prancis"], "category": "Internasional"},
    
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
    {"id": 45, "subject_name": "Muatan Lokal", "aliases": ["Mulok", "Muatan Daerah Lokal Bahasa"], "category": "Umum"},
    # {"id": 46, "subject_name": "Kejuruan", "aliases": ["Mata Pelajaran Kejuruan", "Kompetensi Keahlian", "C3", "C2", "C1", "Produktif"], "category": "Umum"},
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
