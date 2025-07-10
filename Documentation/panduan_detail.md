# Panduan Detail Fungsi OCR dengan Gemini

## 📋 Daftar Isi
1. [Struktur Program](#struktur-program)
2. [Fungsi Utility](#fungsi-utility)
3. [Fungsi OCR Core](#fungsi-ocr-core)
4. [Fungsi AI Integration](#fungsi-ai-integration)
5. [Fungsi User Interface](#fungsi-user-interface)
6. [Contoh Penggunaan](#contoh-penggunaan)

---

## 1. Struktur Program

### Class `OCRWithGemini`
```python
class OCRWithGemini:
    def __init__(self, api_key: Optional[str] = None)
```

**Komponen Utama:**
- **API Integration**: Koneksi ke Gemini AI
- **OCR Processing**: Interface dengan Tesseract
- **User Interface**: Interaksi dengan pengguna
- **File Management**: Handling input/output files
- **Error Handling**: Menangani berbagai error scenarios

---

## 2. Fungsi Utility

### 🔧 `check_tesseract()`
```python
def check_tesseract(self) -> bool
```

**Fungsi:** Memverifikasi ketersediaan Tesseract OCR
**Return:** `True` jika Tesseract tersedia, `False` jika tidak

**Cara Kerja:**
1. Menjalankan command `tesseract --version`
2. Mengecek return code dari subprocess
3. Handle FileNotFoundError jika Tesseract tidak terinstall

**Kapan Dipanggil:** Sebelum melakukan OCR di `process_image()`

---

### 📁 `find_image_files()`
```python
def find_image_files(self, directory: str = "gambar") -> List[str]
```

**Fungsi:** Mencari semua file gambar dalam direktori
**Parameter:** `directory` - path direktori (default: "gambar")
**Return:** List path file gambar yang ditemukan

**Format Didukung:**
- `.jpg`, `.jpeg` - JPEG images
- `.png` - PNG images  
- `.bmp` - Bitmap images
- `.tiff` - TIFF images
- `.gif` - GIF images
- `.webp` - WebP images

**Cara Kerja:**
1. Cek apakah direktori exists
2. Loop setiap format file yang didukung
3. Gunakan `glob.glob()` untuk pattern matching
4. Cek lowercase dan uppercase extensions
5. Return sorted list untuk konsistensi

---

### 📊 `calculate_text_quality()`
```python
def calculate_text_quality(self, text: str) -> float
```

**Fungsi:** Menghitung kualitas teks OCR (score 0-10)
**Parameter:** `text` - teks hasil OCR
**Return:** Quality score (float)

**Faktor Penilaian:**
1. **Word Count (max 3 pts):** Lebih banyak kata = lebih baik
2. **Character Variety (max 4 pts):** 
   - Letters: +2 pts
   - Numbers: +1 pt  
   - Spaces: +1 pt
3. **Text Length (1 pt):** Panjang wajar (10-1000 char)
4. **Special Characters (1 pt):** < 10% dari total karakter
5. **Common Words (1 pt):** Kata umum Indonesia/English

**Contoh Score:**
- Text berkualitas tinggi: 8-10
- Text medium: 5-7  
- Text buruk: 0-4

---

## 3. Fungsi OCR Core

### 🔍 `extract_text_tesseract()`
```python
def extract_text_tesseract(self, image_path: str, psm_mode: int = 6) -> str
```

**Fungsi:** Ekstraksi teks dari gambar menggunakan Tesseract
**Parameters:**
- `image_path`: Path ke file gambar
- `psm_mode`: Page Segmentation Mode (default: 6)

**Command Structure:**
```bash
tesseract [image_path] stdout --oem 3 --psm [mode] -l ind+eng
```

**Parameter Tesseract:**
- `--oem 3`: OCR Engine Mode 3 (default, based on available engines)
- `--psm [mode]`: Page Segmentation Mode (0-13)
- `-l ind+eng`: Language packs (Indonesian + English)
- `stdout`: Output ke standard output

**PSM Modes yang Umum:**
- **PSM 3**: Fully automatic (default Tesseract)
- **PSM 6**: Single uniform block (recommended untuk dokumen)
- **PSM 7**: Single text line
- **PSM 8**: Single word
- **PSM 11**: Sparse text (untuk teks tersebar)

---

### 🎯 `auto_detect_psm()`
```python
def auto_detect_psm(self, image_path: str) -> Dict
```

**Fungsi:** Deteksi otomatis PSM terbaik dengan testing multiple modes
**Parameter:** `image_path` - path ke gambar
**Return:** Dictionary dengan recommended PSM dan hasil testing

**Testing Strategy:**
1. **PSM Modes Tested:** [3, 4, 5, 6, 7, 8, 11, 12]
2. **Metrics per PSM:**
   - Word count
   - Character count  
   - Quality score (dari `calculate_text_quality()`)
   - Text preview

**Selection Logic:**
- **Best PSM:** Highest quality score
- **Alternative:** PSM dengan word count tertinggi
- **Fallback:** PSM 6 jika semua testing gagal

**Return Structure:**
```python
{
    'recommended_psm': int,
    'most_words_psm': int,
    'test_results': dict,
    'best_quality_score': float
}
```

---

## 4. Fungsi AI Integration

### 🤖 `correct_typo_with_gemini()`
```python
def correct_typo_with_gemini(self, text: str) -> Dict
```

**Fungsi:** Koreksi typo menggunakan Gemini 2.0 Flash
**Parameter:** `text` - teks mentah hasil OCR
**Return:** Dictionary dengan hasil koreksi

**Prompt Engineering:**
```
INSTRUKSI KOREKSI:
1. Perbaiki HANYA kesalahan ejaan/typo yang jelas dan pasti
2. Gunakan bahasa Indonesia yang benar dan konteks yang sesuai  
3. Pertahankan format, spasi, dan struktur baris asli
4. Jangan tambahkan atau hapus informasi yang tidak perlu
5. Fokus pada kesalahan umum OCR: huruf terbalik, spasi berlebih, karakter salah
6. Pertahankan angka, tanggal, dan format khusus apa adanya
```

**API Configuration:**
```python
"generationConfig": {
    "temperature": 0.1,        # Low randomness untuk konsistensi
    "topK": 40,               # Limit vocabulary selection
    "topP": 0.95,             # Nucleus sampling
    "maxOutputTokens": 1024,   # Limit response length
}
```

**Response Format:**
```json
{
    "corrected_text": "teks yang sudah dikoreksi",
    "corrections": [
        {
            "original": "kata asli", 
            "corrected": "kata terkoreksi", 
            "reason": "alasan koreksi"
        }
    ],
    "confidence": "nilai kepercayaan 1-10"
}
```

**Error Handling:**
- HTTP errors → `handle_api_failure()`
- JSON parse errors → Fallback ke original text
- API rate limits → Graceful degradation
- Network timeouts → 30 second timeout

---

### 🛡️ `handle_api_failure()`
```python
def handle_api_failure(self, text: str) -> Dict
```

**Fungsi:** Fallback mechanism ketika Gemini API gagal
**Parameter:** `text` - teks original
**Return:** Dictionary dengan format sama seperti successful API call

**Fallback Strategy:**
1. Return original text tanpa modifikasi
2. Set `success: False` flag
3. Empty corrections list
4. Confidence score = 0
5. Method = "Original Text (API Failed)"

**Use Cases:**
- API key invalid/expired
- Network connectivity issues
- API service downtime
- Rate limit exceeded
- Malformed responses

---

## 5. Fungsi User Interface

### 🖼️ `get_image_path()`
```python
def get_image_path(self, filename: Optional[str] = None) -> Optional[str]
```

**Fungsi:** Interactive image selection dengan validasi
**Parameter:** `filename` - optional filename (jika sudah diketahui)
**Return:** Valid image path atau None jika dibatalkan

**Selection Flow:**
1. **Direct Path:** Jika filename diberikan dan exists
2. **Gambar Folder:** Cek di folder "gambar" 
3. **Extension Guess:** Coba tambahkan ekstensi otomatis
4. **Interactive List:** Tampilkan daftar gambar tersedia
5. **User Input:** Nomor urut atau partial filename matching

**User Experience:**
```
📁 Gambar yang tersedia di folder 'gambar':
   1. gambar.jpg
   2. gambar2.jpeg

🔍 Pilih gambar (1-2) atau ketik nama file: 
```

**Validation:**
- File existence check
- Supported format validation
- Case-insensitive matching
- Partial name matching

---

### ⚙️ `choose_psm_mode()`
```python
def choose_psm_mode(self, image_path: str) -> int
```

**Fungsi:** Interactive PSM mode selection
**Parameter:** `image_path` - untuk auto-detection
**Return:** Selected PSM mode (0-13)

**Interface Options:**
```
🔧 PILIH PSM MODE:
📋 Mode Umum:
   3. Fully automatic         - Default mode for most documents
   6. Single uniform block    - Best for clean text blocks  
   11. Sparse text            - Best for scattered text
   7. Single text line        - Single line text
   8. Single word             - Single word recognition

🤖 Automatic Detection:
   99. Auto-detect PSM terbaik (testing multiple modes)
   98. Tampilkan semua PSM modes

💡 Berdasarkan analisis sebelumnya:
   - PSM 6: Hasil terbersih (Recommended)
   - PSM 11: Menangkap kata terbanyak  
   - PSM 3: Default Tesseract
```

**Smart Defaults:**
- Default: PSM 6 (best for structured documents)
- Auto-detection available (PSM 99)
- Show all modes option (PSM 98)
- Recommendations based on analysis

---

## 6. Contoh Penggunaan

### Basic Usage
```python
# Inisialisasi
ocr = OCRWithGemini()

# Manual processing
image_path = "gambar/document.jpg"
result = ocr.process_image(image_path, psm_mode=6)

# Simpan hasil
output_file = ocr.save_results(result)
print(f"Hasil disimpan ke: {output_file}")
```

### Advanced Usage dengan Auto-Detection
```python
# Inisialisasi dengan custom API key
ocr = OCRWithGemini(api_key="your-api-key")

# Auto-detect PSM terbaik
auto_result = ocr.auto_detect_psm("gambar/complex_document.jpg")
best_psm = auto_result['recommended_psm']

# Process dengan PSM terbaik
result = ocr.process_image("gambar/complex_document.jpg", psm_mode=best_psm)

# Analisis hasil
if result['corrections']:
    print(f"Koreksi dilakukan: {len(result['corrections'])}")
    for correction in result['corrections']:
        print(f"'{correction['original']}' → '{correction['corrected']}'")
```

### Error Handling Example
```python
try:
    ocr = OCRWithGemini()
    
    # Cek prerequisites
    if not ocr.check_tesseract():
        print("❌ Tesseract tidak ditemukan!")
        return
    
    # Process dengan error handling
    result = ocr.process_image("gambar/test.jpg")
    
    if 'error' in result:
        print(f"❌ Error: {result['error']}")
    elif not result['success']:
        print(f"⚠️ Warning: {result['warning']}")
    else:
        print("✅ Processing berhasil!")
        
except ValueError as e:
    print(f"❌ Configuration error: {e}")
except Exception as e:
    print(f"❌ Unexpected error: {e}")
```

---

## 🎯 Key Features

### 1. **Robust Error Handling**
- Tesseract availability check
- API failure fallbacks
- File validation
- Graceful degradation

### 2. **Smart PSM Detection**
- Multiple mode testing
- Quality scoring
- Automatic recommendation
- Manual override option

### 3. **AI-Powered Correction**
- Context-aware typo correction
- Structured prompt engineering
- Detailed correction tracking
- Confidence scoring

### 4. **User-Friendly Interface**
- Interactive file selection
- Clear progress indicators
- Comprehensive result display
- Detailed logging

### 5. **Flexible Output**
- Multiple text versions (raw, corrected, final)
- Detailed metadata
- Structured file output
- Statistics and analytics

---

## 💡 Best Practices

1. **Image Quality:** Gunakan gambar dengan resolusi tinggi dan kontras baik
2. **PSM Selection:** Mulai dengan PSM 6, gunakan auto-detection untuk dokumen kompleks
3. **API Management:** Simpan API key di file `.env` untuk keamanan
4. **Batch Processing:** Process multiple images dengan loop dan error handling
5. **Result Validation:** Selalu cek quality score dan review corrections

---

## 🔧 Troubleshooting

### Common Issues:
1. **"Tesseract not found"** → Install Tesseract dan add ke PATH
2. **"API key tidak ditemukan"** → Buat file `.env` dengan `GEMINI_API_KEY=your-key`
3. **"No text extracted"** → Coba PSM mode berbeda atau periksa kualitas gambar
4. **"Gemini API error"** → Cek koneksi internet dan API key validity

### Performance Tips:
1. **Optimize Image:** Resize ke resolusi optimal (~1200-2000px width)
2. **Preprocessing:** Crop area text, adjust contrast jika perlu
3. **PSM Selection:** Gunakan auto-detection untuk hasil optimal
4. **Batch Processing:** Process multiple files dalam single session
