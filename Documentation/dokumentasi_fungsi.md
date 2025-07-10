# Dokumentasi OCR dengan Gemini 2.0 Flash

## Gambaran Umum
Sistem OCR ini menggunakan kombinasi Tesseract OCR untuk ekstraksi teks mentah dari gambar, kemudian menggunakan Google Gemini 2.0 Flash untuk koreksi typo dan perbaikan teks. Pipeline ini dirancang untuk memberikan hasil OCR yang lebih akurat dan mudah dibaca.

## Struktur Kelas dan Fungsi

### Class: `OCRWithGemini`

#### 1. `__init__(self, api_key: Optional[str] = None)`
**Tujuan**: Inisialisasi class dengan API key Gemini
**Cara Kerja**:
- Memuat environment variables dari file `.env`
- Mengatur API key dari parameter atau environment variable `GEMINI_API_KEY`
- Menyiapkan endpoint Gemini dan format file yang didukung
- Menampilkan pesan inisialisasi

**Penggunaan**: Dipanggil otomatis saat membuat instance `OCRWithGemini()`

---

#### 2. `check_tesseract(self) -> bool`
**Tujuan**: Memverifikasi apakah Tesseract OCR terinstall dan dapat diakses
**Cara Kerja**:
- Menjalankan command `tesseract --version`
- Mengembalikan `True` jika berhasil, `False` jika gagal

**Penggunaan**: Dipanggil sebelum melakukan OCR untuk memastikan Tesseract tersedia

---

#### 3. `find_image_files(self, directory: str = "gambar") -> List[str]`
**Tujuan**: Mencari semua file gambar dalam direktori tertentu
**Cara Kerja**:
- Menggunakan `glob.glob()` untuk mencari file dengan ekstensi gambar
- Mendukung format: `.jpg`, `.jpeg`, `.png`, `.bmp`, `.tiff`, `.gif`, `.webp`
- Mengembalikan list file yang diurutkan

**Penggunaan**: Dipanggil oleh `get_image_path()` untuk menampilkan pilihan gambar

---

#### 4. `get_image_path(self, filename: Optional[str] = None) -> Optional[str]`
**Tujuan**: Mendapatkan path gambar yang valid dengan interaksi user
**Cara Kerja**:
- Jika filename diberikan, cek apakah file ada
- Jika tidak, tampilkan daftar gambar yang tersedia
- User dapat memilih berdasarkan nomor atau nama file
- Mengembalikan path yang valid atau None

**Penggunaan**: Dipanggil di `main()` untuk mendapatkan input gambar dari user

---

#### 5. `extract_text_tesseract(self, image_path: str, psm_mode: int = 6) -> str`
**Tujuan**: Mengekstrak teks dari gambar menggunakan Tesseract OCR
**Cara Kerja**:
- Membuat command Tesseract dengan parameter:
  - `--oem 3`: OCR Engine Mode 3 (default)
  - `--psm [mode]`: Page Segmentation Mode
  - `-l ind+eng`: Bahasa Indonesia + English
- Menjalankan command dan mengembalikan hasil teks

**Penggunaan**: Dipanggil oleh `process_image()` untuk ekstraksi teks mentah

---

#### 6. `correct_typo_with_gemini(self, text: str) -> Dict`
**Tujuan**: Mengoreksi typo dalam teks OCR menggunakan Gemini AI
**Cara Kerja**:
- Menyiapkan prompt yang detail untuk koreksi typo
- Mengirim request ke Gemini API dengan text yang perlu dikoreksi
- Mem-parse response JSON yang berisi teks terkoreksi dan daftar koreksi
- Mengembalikan dictionary dengan hasil koreksi

**Penggunaan**: Dipanggil oleh `process_image()` setelah ekstraksi teks Tesseract

---

#### 7. `handle_api_failure(self, text: str) -> Dict`
**Tujuan**: Menangani kegagalan API Gemini dengan graceful fallback
**Cara Kerja**:
- Mengembalikan teks original tanpa koreksi
- Memberikan flag `success: False`
- Menyediakan pesan warning untuk user

**Penggunaan**: Dipanggil oleh `correct_typo_with_gemini()` jika API gagal

---

#### 8. `post_process_text(self, text: str) -> str`
**Tujuan**: Membersihkan dan memformat teks hasil koreksi
**Cara Kerja**:
- Menghapus whitespace berlebih dengan regex
- Memperbaiki line breaks
- Menghapus leading/trailing whitespace dari setiap baris

**Penggunaan**: Dipanggil oleh `process_image()` sebagai tahap akhir processing

---

#### 9. `get_psm_info(self) -> Dict`
**Tujuan**: Menyediakan informasi lengkap tentang PSM (Page Segmentation Mode)
**Cara Kerja**:
- Mengembalikan dictionary dengan 14 mode PSM (0-13)
- Setiap mode memiliki nama, deskripsi, dan use case

**Penggunaan**: Dipanggil oleh `choose_psm_mode()` untuk menampilkan opsi PSM

---

#### 10. `calculate_text_quality(self, text: str) -> float`
**Tujuan**: Menghitung kualitas teks OCR berdasarkan berbagai faktor
**Cara Kerja**:
- **Faktor 1**: Jumlah kata (max 3 poin)
- **Faktor 2**: Variasi karakter (huruf, angka, spasi, tanda baca)
- **Faktor 3**: Panjang teks yang wajar
- **Faktor 4**: Proporsi karakter khusus yang rendah
- **Faktor 5**: Keberadaan kata-kata umum Indonesia/English

**Penggunaan**: Dipanggil oleh `auto_detect_psm()` untuk menilai hasil setiap PSM

---

#### 11. `auto_detect_psm(self, image_path: str) -> Dict`
**Tujuan**: Mendeteksi PSM terbaik secara otomatis dengan testing multiple mode
**Cara Kerja**:
- Menjalankan OCR dengan 8 PSM mode berbeda [3,4,5,6,7,8,11,12]
- Menghitung quality score untuk setiap hasil
- Merekomendasikan PSM dengan score tertinggi
- Menyediakan alternatif PSM dengan kata terbanyak

**Penggunaan**: Dipanggil oleh `choose_psm_mode()` jika user memilih auto-detection

---

#### 12. `choose_psm_mode(self, image_path: str) -> int`
**Tujuan**: Interface interaktif untuk memilih PSM mode
**Cara Kerja**:
- Menampilkan PSM mode umum dan opsi khusus
- Menyediakan auto-detection (99) dan tampilkan semua mode (98)
- Memberikan rekomendasi berdasarkan analisis sebelumnya
- Mengembalikan PSM mode yang dipilih user

**Penggunaan**: Dipanggil di `main()` setelah mendapat image path

---

#### 13. `process_image(self, image_path: str, psm_mode: int = 6) -> Dict`
**Tujuan**: Pipeline utama OCR lengkap dengan koreksi Gemini
**Cara Kerja**:
1. **Validasi**: Cek Tesseract, file gambar, dan format
2. **Ekstraksi**: Jalankan Tesseract OCR
3. **Koreksi**: Gunakan Gemini untuk perbaikan typo
4. **Post-processing**: Bersihkan dan format teks
5. **Kompilasi**: Gabungkan semua hasil dalam dictionary

**Penggunaan**: Dipanggil di `main()` sebagai fungsi utama processing

---

#### 14. `save_results(self, result: Dict, output_file: Optional[str] = None)`
**Tujuan**: Menyimpan hasil OCR ke file dengan format yang rapi
**Cara Kerja**:
- Generate nama file otomatis jika tidak diberikan
- Menulis metadata (gambar, PSM, tanggal, dll)
- Menulis statistik dan daftar koreksi
- Menulis teks mentah, terkoreksi, dan final

**Penggunaan**: Dipanggil di `main()` setelah `process_image()` selesai

---

### Function: `main()`
**Tujuan**: Fungsi utama yang menjalankan seluruh pipeline OCR
**Cara Kerja**:
1. Inisialisasi `OCRWithGemini`
2. Dapatkan path gambar dari user
3. Pilih PSM mode
4. Proses gambar dengan OCR+Gemini
5. Simpan dan tampilkan hasil

**Penggunaan**: Entry point aplikasi, dipanggil saat script dijalankan

## Alur Kerja Sistem

### Pipeline Utama:
1. **Inisialisasi** → Load API key dan setup
2. **Input Selection** → User pilih gambar dan PSM mode
3. **OCR Processing** → Tesseract ekstrak teks mentah
4. **AI Correction** → Gemini koreksi typo
5. **Post Processing** → Bersihkan dan format
6. **Output** → Simpan ke file dan tampilkan hasil

### Error Handling:
- **Tesseract tidak ditemukan** → Stop dengan pesan error
- **File gambar tidak ada** → Stop dengan pesan error
- **Gemini API gagal** → Lanjut dengan teks original
- **User cancel** → Graceful exit

### Quality Assurance:
- **Auto PSM Detection** → Test multiple mode untuk hasil optimal
- **Text Quality Scoring** → Evaluasi hasil berdasarkan metrics
- **Fallback Mechanism** → Backup plan jika komponen gagal
