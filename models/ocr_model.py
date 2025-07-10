# models/ocr_model.py
"""
Model layer untuk OCR dengan Gemini
Menangani data processing, API calls, dan business logic
"""

import os
import subprocess
import re
import requests
import json
import glob
import time
from typing import Dict, List, Optional
from dotenv import load_dotenv


class OCRModel:
    """Model untuk OCR processing dan Gemini API integration"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize OCR Model dengan API key"""
        load_dotenv()
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        
        if not self.api_key:
            raise ValueError("❌ API key tidak ditemukan! Pastikan GEMINI_API_KEY ada di file .env")
        
        self.gemini_endpoint = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent"
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif', '.webp'}
    
    def check_tesseract(self) -> bool:
        """Check if Tesseract is available"""
        try:
            result = subprocess.run(['tesseract', '--version'], 
                                  capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def find_image_files(self, directory: str = "gambar") -> List[str]:
        """Find all image files in directory"""
        if not os.path.exists(directory):
            return []
        
        image_files = set()
        for ext in self.supported_formats:
            pattern = os.path.join(directory, f"*{ext}")
            image_files.update(glob.glob(pattern))
            pattern = os.path.join(directory, f"*{ext.upper()}")
            image_files.update(glob.glob(pattern))
        
        return sorted(list(image_files))
    
    def extract_text_tesseract(self, image_path: str, psm_mode: int = 6) -> str:
        """Extract text using Tesseract OCR"""
        try:
            cmd = [
                'tesseract', image_path, 'stdout',
                '--oem', '3', '--psm', str(psm_mode),
                '-l', 'ind+eng'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
            
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                return ""
        except Exception:
            return ""
    
    def correct_typo_with_gemini(self, text: str) -> Dict:
        """Correct typos using Gemini AI"""
        try:
            prompt = f"""
Anda adalah ahli koreksi teks yang berpengalaman. Tugas Anda adalah memperbaiki kesalahan OCR (typo) dalam teks berikut, sambil mempertahankan format dan struktur asli.

TEKS OCR YANG PERLU DIKOREKSI:
{text}

INSTRUKSI KOREKSI:
1. Perbaiki HANYA kesalahan ejaan/typo yang jelas dan pasti
2. Gunakan bahasa Indonesia yang benar dan konteks yang sesuai
3. Pertahankan format, spasi, dan struktur baris asli
4. Jangan tambahkan atau hapus informasi yang tidak perlu
5. Fokus pada kesalahan umum OCR: huruf terbalik, spasi berlebih, karakter salah
6. Pertahankan angka, tanggal, dan format khusus apa adanya

RESPONSE FORMAT:
Berikan respon dalam format JSON:
{{
    "corrected_text": "teks yang sudah dikoreksi",
    "corrections": [
        {{"original": "kata asli", "corrected": "kata terkoreksi", "reason": "alasan koreksi"}}
    ],
    "confidence": "nilai kepercayaan 1-10"
}}

Berikan hanya JSON response, tanpa penjelasan tambahan.
"""
            
            headers = {'Content-Type': 'application/json'}
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.1,
                    "topK": 40,
                    "topP": 0.95,
                    "maxOutputTokens": 1024,
                }
            }
            
            url = f"{self.gemini_endpoint}?key={self.api_key}"
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                
                if 'candidates' in result and len(result['candidates']) > 0:
                    generated_text = result['candidates'][0]['content']['parts'][0]['text']
                    
                    json_text = generated_text.strip()
                    if json_text.startswith('```json'):
                        json_text = json_text.replace('```json', '').replace('```', '').strip()
                    
                    correction_result = json.loads(json_text)
                    
                    return {
                        'success': True,
                        'corrected_text': correction_result.get('corrected_text', text),
                        'corrections': correction_result.get('corrections', []),
                        'confidence': correction_result.get('confidence', 5),
                        'method': 'Gemini 2.0 Flash'
                    }
                    
        except Exception:
            pass
            
        return self._handle_api_failure(text)
    
    def _handle_api_failure(self, text: str) -> Dict:
        """Handle API failure gracefully"""
        return {
            'success': False,
            'corrected_text': text,
            'corrections': [],
            'confidence': 0,
            'method': 'Original Text (API Failed)'
        }
    
    def post_process_text(self, text: str) -> str:
        """Post-process text for cleanup"""
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n', text)
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        return '\n'.join(lines)
    
    def calculate_text_quality(self, text: str) -> float:
        """Calculate text quality score (0-10)"""
        if not text:
            return 0
        
        score = 0
        word_count = len(text.split())
        
        # Factor 1: Word count
        if word_count > 0:
            score += min(word_count / 10, 3)
        
        # Factor 2: Character variety
        char_types = {
            'letters': sum(1 for c in text if c.isalpha()),
            'numbers': sum(1 for c in text if c.isdigit()),
            'spaces': sum(1 for c in text if c.isspace())
        }
        
        if char_types['letters'] > 0:
            score += 2
        if char_types['numbers'] > 0:
            score += 1
        if char_types['spaces'] > 0:
            score += 1
        
        # Factor 3: Reasonable text length
        if 10 < len(text) < 1000:
            score += 1
        
        # Factor 4: Low special characters ratio
        special_chars = sum(1 for c in text if not c.isalnum() and c not in ' .,!?;:()[]{}')
        if special_chars < len(text) * 0.1:
            score += 1
        
        # Factor 5: Common words
        common_words = ['dan', 'atau', 'yang', 'dengan', 'untuk', 'dari', 'ke', 'di', 'pada', 'dalam',
                       'the', 'and', 'or', 'of', 'to', 'in', 'for', 'with', 'on', 'at']
        
        text_lower = text.lower()
        found_common = sum(1 for word in common_words if word in text_lower)
        if found_common > 0:
            score += min(found_common / 5, 1)
        
        return min(score, 10)
    
    def auto_detect_psm(self, image_path: str) -> Dict:
        """Automatic PSM detection by testing multiple modes"""
        test_modes = [3, 4, 5, 6, 7, 8, 11, 12]
        results = {}
        
        for psm in test_modes:
            try:
                text = self.extract_text_tesseract(image_path, psm)
                
                if text:
                    word_count = len(text.split())
                    quality_score = self.calculate_text_quality(text)
                    
                    results[psm] = {
                        'text': text,
                        'word_count': word_count,
                        'quality_score': quality_score,
                        'text_preview': text[:50] + "..." if len(text) > 50 else text
                    }
                else:
                    results[psm] = {
                        'text': '',
                        'word_count': 0,
                        'quality_score': 0,
                        'text_preview': 'No text detected'
                    }
            except Exception as e:
                results[psm] = {
                    'text': '',
                    'word_count': 0,
                    'quality_score': 0,
                    'text_preview': f'Error: {e}'
                }
        
        if results:
            best_psm = max(results.keys(), key=lambda x: results[x]['quality_score'])
            most_words_psm = max(results.keys(), key=lambda x: results[x]['word_count'])
            
            return {
                'recommended_psm': best_psm,
                'most_words_psm': most_words_psm,
                'test_results': results,
                'best_quality_score': results[best_psm]['quality_score']
            }
        
        return {
            'recommended_psm': 6,
            'most_words_psm': 6,
            'test_results': {},
            'best_quality_score': 0
        }
    
    def get_psm_info(self) -> Dict:
        """Get PSM mode information"""
        return {
            0: {'name': 'OSD only', 'use_case': 'Deteksi orientasi dan script saja'},
            1: {'name': 'Automatic page segmentation with OSD', 'use_case': 'Segmentasi halaman otomatis dengan OSD'},
            2: {'name': 'Automatic page segmentation', 'use_case': 'Segmentasi halaman otomatis tanpa OSD'},
            3: {'name': 'Fully automatic', 'use_case': 'Default Tesseract - cocok untuk dokumen umum'},
            4: {'name': 'Single column', 'use_case': 'Kolom teks tunggal dengan ukuran bervariasi'},
            5: {'name': 'Single block', 'use_case': 'Blok teks tunggal yang seragam'},
            6: {'name': 'Single uniform block', 'use_case': 'Recommended - Dokumen terstruktur (laporan, form)'},
            7: {'name': 'Single text line', 'use_case': 'Baris teks tunggal (header, caption)'},
            8: {'name': 'Single word', 'use_case': 'Kata tunggal (logo, label)'},
            9: {'name': 'Single word in circle', 'use_case': 'Kata dalam lingkaran (stempel, logo)'},
            10: {'name': 'Single character', 'use_case': 'Karakter tunggal (captcha, angka)'},
            11: {'name': 'Sparse text', 'use_case': 'Teks tersebar - tangkap sebanyak mungkin kata'},
            12: {'name': 'Sparse text with OSD', 'use_case': 'Teks tersebar dengan deteksi orientasi'},
            13: {'name': 'Raw line', 'use_case': 'Baris mentah tanpa processing tambahan'}
        }
    
    def save_results(self, result: Dict, output_file: Optional[str] = None) -> str:
        """Save OCR results to file"""
        if output_file is None:
            image_name = os.path.splitext(result['image_name'])[0]
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            output_file = f"hasil_ocr_{image_name}_{timestamp}.txt"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=== OCR DENGAN GEMINI 2.0 FLASH ===\n")
            f.write("=" * 60 + "\n\n")
            
            f.write("INFORMASI:\n")
            f.write(f"File gambar: {result['image_name']}\n")
            f.write(f"Path lengkap: {result['image_path']}\n")
            f.write(f"PSM Mode: {result['psm_mode']} ({result.get('psm_description', 'N/A')})\n")
            f.write(f"Metode koreksi: {result['method']}\n")
            f.write(f"Confidence: {result['confidence']}/10\n")
            f.write(f"Tanggal: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("STATISTIK:\n")
            f.write(f"Kata mentah: {result['statistics']['raw_words']}\n")
            f.write(f"Kata final: {result['statistics']['final_words']}\n")
            f.write(f"Jumlah koreksi: {result['statistics']['corrections_count']}\n")
            
            if 'warning' in result:
                f.write(f"⚠️ Warning: {result['warning']}\n")
            f.write("\n")
            
            if result['corrections']:
                f.write("KOREKSI YANG DILAKUKAN:\n")
                f.write("-" * 40 + "\n")
                for correction in result['corrections']:
                    f.write(f"'{correction['original']}' → '{correction['corrected']}' ({correction['reason']})\n")
                f.write("\n")
            
            f.write("TEKS MENTAH (OCR):\n")
            f.write("-" * 40 + "\n")
            f.write(result['raw_text'] + "\n\n")
            
            f.write("TEKS TERKOREKSI (GEMINI):\n")
            f.write("-" * 40 + "\n")
            f.write(result['corrected_text'] + "\n\n")
            
            f.write("TEKS FINAL (POST-PROCESSED):\n")
            f.write("-" * 40 + "\n")
            f.write(result['final_text'] + "\n")
        
        return output_file
