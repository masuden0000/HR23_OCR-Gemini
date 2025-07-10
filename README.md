# 🤖 OCR dengan Gemini AI (MVC Version)

Program OCR (Optical Character Recognition) yang bisa membaca teks dari gambar dengan bantuan AI Gemini untuk memperbaiki typo secara otomatis. **Direfactor menggunakan MVC pattern** untuk better code organization.

## ✨ Fitur
- 📖 **Baca teks dari gambar** - Extract teks dari foto dokumen
- 🤖 **Koreksi typo otomatis** - AI Gemini memperbaiki kesalahan OCR
- 🎯 **Deteksi mode terbaik** - Cari setting optimal untuk setiap gambar
- 🇮🇩 **Support Bahasa Indonesia** - Optimized untuk teks Indonesia
- 💾 **Simpan hasil** - Export ke file teks dengan detail lengkap
- 🏗️ **MVC Architecture** - Clean, maintainable, dan extensible code
- 🔄 **Batch Processing** - Process multiple images sekaligus
- 🛠️ **API Mode** - Programmatic usage untuk integration

## 🚀 Cara Menggunakan

### 1. Persiapan
```bash
# Install library yang dibutuhkan
pip install -r requirements.txt

# Dapatkan API key Gemini dari Google AI Studio
# Buat file .env dan isi dengan:
GEMINI_API_KEY=your_api_key_here
```

### 2. Siapkan Gambar
- Masukkan gambar ke folder `gambar/`
- Format yang didukung: `.jpg`, `.png`, `.bmp`, `.tiff`, `.gif`, `.webp`

### 3. Jalankan Program

#### Mode Interactive (Recommended)
```bash
python main.py
```

#### Mode Batch (Process All Images)
```bash
python main.py batch           # Default folder 'gambar', PSM 6
python main.py batch images 11 # Custom folder dan PSM
```

#### Mode Single Image
```bash
python main.py single gambar/test.jpg    # PSM default
python main.py single gambar/test.jpg 11 # Custom PSM
```

#### Legacy Mode (Original Script)
```bash
python ocr_with_gemini_improved.py
```

Program akan:
1. Menampilkan daftar gambar yang tersedia
2. Meminta Anda memilih gambar
3. Meminta pilihan mode OCR (atau auto-detection)
4. Memproses gambar dan memperbaiki teks
5. Menyimpan hasil ke file

## 📁 Project Structure (MVC)
```
📂 OCR/
├── � main.py                       # Entry point MVC version (RECOMMENDED)
├── 🔒 .env                         # API key (jangan di-commit!)
├── 📄 requirements.txt             # Library yang dibutuhkan
├── 📄 README.md                    # Panduan ini
├── 
├── 📁 models/                      # MODEL LAYER
│   ├── __init__.py
│   └── ocr_model.py               # Business logic & data processing
├── 
├── 📁 views/                       # VIEW LAYER
│   ├── __init__.py
│   └── ocr_view.py                # User interface & presentation
├── 
├── 📁 controllers/                 # CONTROLLER LAYER
│   ├── __init__.py
│   └── ocr_controller.py          # Workflow coordination
├── 
└── 📁 gambar/                      # Folder untuk gambar input
    ├── gambar.jpg                 # Contoh gambar
    └── gambar2.jpeg               # Contoh gambar lain
```

## 🏗️ MVC Architecture

**Model-View-Controller** pattern untuk clean code organization:

- **Model** (`models/`): Business logic, data processing, API calls
- **View** (`views/`): User interface, input/output, presentation
- **Controller** (`controllers/`): Workflow coordination, application logic

👉 **Lihat `MVC_ARCHITECTURE.md` untuk dokumentasi detail arsitektur MVC.**

## ⚙️ Mode OCR (PSM)

Program menyediakan beberapa mode untuk membaca teks:

| Mode | Nama | Cocok Untuk |
|------|------|-------------|
| **6** | Single block | Dokumen terstruktur *(Recommended)* |
| **3** | Automatic | Dokumen umum (Default Tesseract) |
| **11** | Sparse text | Teks tersebar, maksimal ekstraksi |
| **7** | Single line | Header, caption |
| **99** | Auto-detect | Otomatis pilih mode terbaik |

**Tip:** Pilih mode 99 untuk auto-detection jika tidak yakin mode mana yang terbaik.

### Software:
- **Python 3.7+** - Bahasa pemrograman
- **Tesseract OCR** - Engine untuk baca teks dari gambar
  ```bash
  # Windows: Download dari https://github.com/UB-Mannheim/tesseract/wiki
  # Linux: sudo apt install tesseract-ocr tesseract-ocr-ind
  # macOS: brew install tesseract tesseract-lang
  ```

### Library Python:
```txt
pytesseract>=0.3.10    # Interface ke Tesseract
requests>=2.31.0       # Untuk API Gemini
python-dotenv>=1.0.0   # Untuk load .env file
```

### API Key:
- **Google Gemini API** - Gratis di [Google AI Studio](https://makersuite.google.com/)

## � Troubleshooting

### Problem: "Tesseract not found"
**Solusi:** Install Tesseract OCR dan pastikan ada di PATH

### Problem: "API key tidak ditemukan"
**Solusi:** Buat file `.env` dan isi dengan `GEMINI_API_KEY=your_key`

### Problem: "No text extracted"
**Solusi:** Coba mode PSM berbeda atau periksa kualitas gambar

### Problem: Hasil OCR buruk
**Solusi:**
- Gunakan gambar resolusi tinggi (1200px+ width)
- Pastikan kontras gambar bagus
- Crop area teks jika perlu
- Coba mode auto-detection (99)

## 💡 Tips Penggunaan

1. **Kualitas Gambar:** Gunakan gambar yang jelas dan kontras tinggi
2. **Mode Selection:** Mulai dengan auto-detection (mode 99)
3. **Batch Processing:** Untuk banyak gambar, letakkan semua di folder `gambar/`
4. **Review Hasil:** Selalu cek file hasil untuk memastikan akurasi

