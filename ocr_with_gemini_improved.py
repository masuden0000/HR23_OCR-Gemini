"""
OCR Pipeline dengan Gemini 2.0 Flash untuk Koreksi Typo (Improved Version)
- Prompt LLM yang general (tidak restrict ke dokumen keuangan)
- API key dari file .env untuk keamanan
- Input gambar dinamis dengan validasi
- Folder gambar terorganisir
"""

import os
import subprocess
import re
import requests
import json
import glob
from typing import Dict, List, Optional
from dotenv import load_dotenv
import time

class OCRWithGemini:
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OCR with Gemini 2.0 Flash integration
        
        Args:
            api_key: Google Gemini API key (optional, will load from .env if not provided)
        """
        # Load environment variables from .env file
        load_dotenv()
        
        # Use provided API key or load from environment
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        
        if not self.api_key:
            raise ValueError("❌ API key tidak ditemukan! Pastikan GEMINI_API_KEY ada di file .env")
        
        self.gemini_endpoint = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent"
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif', '.webp'}
        
        print(f"🤖 OCR with Gemini 2.0 Flash initialized")
        print(f"📁 Gambar akan dicari di folder: ./gambar/")
        
    def check_tesseract(self) -> bool:
        """Check if Tesseract is available"""
        try:
            result = subprocess.run(['tesseract', '--version'], 
                                  capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def find_image_files(self, directory: str = "gambar") -> List[str]:
        """
        Find all image files in the specified directory
        
        Args:
            directory: Directory to search for images
            
        Returns:
            List of image file paths
        """
        if not os.path.exists(directory):
            return []
        
        image_files = set()  # Use set to avoid duplicates
        for ext in self.supported_formats:
            # Check lowercase extension
            pattern = os.path.join(directory, f"*{ext}")
            image_files.update(glob.glob(pattern))
            # Check uppercase extension
            pattern = os.path.join(directory, f"*{ext.upper()}")
            image_files.update(glob.glob(pattern))
        
        return sorted(list(image_files))
    
    def get_image_path(self, filename: Optional[str] = None) -> Optional[str]:
        """
        Get image path with validation
        
        Args:
            filename: Optional filename to process
            
        Returns:
            Valid image path or None
        """
        if filename:
            # Check if it's a full path
            if os.path.exists(filename):
                return filename
            
            # Check in gambar folder
            gambar_path = os.path.join("gambar", filename)
            if os.path.exists(gambar_path):
                return gambar_path
            
            # Check if file exists without extension
            for ext in self.supported_formats:
                test_path = os.path.join("gambar", f"{filename}{ext}")
                if os.path.exists(test_path):
                    return test_path
        
        # Show available images
        available_images = self.find_image_files()
        if not available_images:
            print("❌ Tidak ada gambar ditemukan di folder 'gambar'")
            return None
        
        print(f"📁 Gambar yang tersedia di folder 'gambar':")
        for i, img in enumerate(available_images, 1):
            print(f"   {i}. {os.path.basename(img)}")
        
        # Ask user to select
        while True:
            try:
                choice = input(f"\n🔍 Pilih gambar (1-{len(available_images)}) atau ketik nama file: ").strip()
                
                # Check if it's a number
                if choice.isdigit():
                    idx = int(choice) - 1
                    if 0 <= idx < len(available_images):
                        return available_images[idx]
                    else:
                        print(f"❌ Pilihan tidak valid. Pilih 1-{len(available_images)}")
                        continue
                
                # Check if it's a filename
                for img in available_images:
                    if choice.lower() in os.path.basename(img).lower():
                        return img
                
                print("❌ File tidak ditemukan. Coba lagi.")
                
            except KeyboardInterrupt:
                print("\n❌ Dibatalkan oleh user")
                return None
    
    def extract_text_tesseract(self, image_path: str, psm_mode: int = 6) -> str:
        """
        Extract text using Tesseract OCR
        
        Args:
            image_path: Path to image file
            psm_mode: Page Segmentation Mode (default: 6)
        """
        try:
            cmd = [
                'tesseract',
                image_path,
                'stdout',
                '--oem', '3',
                '--psm', str(psm_mode),
                '-l', 'ind+eng'  # Indonesian + English
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
            
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                print(f"❌ Tesseract error: {result.stderr}")
                return ""
                
        except Exception as e:
            print(f"❌ Error running Tesseract: {e}")
            return ""
    
    def correct_typo_with_gemini(self, text: str) -> Dict:
        """
        Correct typos using Gemini 2.0 Flash with general purpose prompt
        
        Args:
            text: Raw OCR text with potential typos
            
        Returns:
            Dict with corrected text and corrections made
        """
        print("🤖 Correcting typos with Gemini 2.0 Flash...")
        
        try:
            # General purpose prompt - tidak restrict ke dokumen keuangan
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

CONTOH KOREKSI UMUM:
- "Kerngi an" → "Kerugian"
- "lnventaris" → "Inventaris" 
- "Pembiay aan" → "Pembiayaan"
- "Petap" → "Tetap"
- "Tanggal: 31 Ocsember" → "Tanggal: 31 Desember"
- "Harga: Rp 1.000.OOO" → "Harga: Rp 1.000.000"

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

            # Prepare request to Gemini
            headers = {
                'Content-Type': 'application/json',
            }
            
            payload = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.1,
                    "topK": 40,
                    "topP": 0.95,
                    "maxOutputTokens": 1024,
                }
            }
            
            # Make request to Gemini API
            url = f"{self.gemini_endpoint}?key={self.api_key}"
            
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Extract generated text
                if 'candidates' in result and len(result['candidates']) > 0:
                    generated_text = result['candidates'][0]['content']['parts'][0]['text']
                    
                    # Parse JSON response
                    try:
                        # Clean JSON from markdown formatting
                        json_text = generated_text.strip()
                        if json_text.startswith('```json'):
                            json_text = json_text.replace('```json', '').replace('```', '').strip()
                        
                        correction_result = json.loads(json_text)
                        
                        print(f"✅ Gemini correction completed")
                        print(f"📊 Confidence: {correction_result.get('confidence', 'N/A')}/10")
                        print(f"🔧 Corrections made: {len(correction_result.get('corrections', []))}")
                        
                        return {
                            'success': True,
                            'corrected_text': correction_result.get('corrected_text', text),
                            'corrections': correction_result.get('corrections', []),
                            'confidence': correction_result.get('confidence', 5),
                            'method': 'Gemini 2.0 Flash'
                        }
                        
                    except json.JSONDecodeError as e:
                        print(f"❌ JSON parse error: {e}")
                        print(f"Raw response: {generated_text}")
                        return self.handle_api_failure(text)
                else:
                    print("❌ No candidates in Gemini response")
                    return self.handle_api_failure(text)
            else:
                print(f"❌ Gemini API error: {response.status_code}")
                print(f"Error details: {response.text}")
                return self.handle_api_failure(text)
                
        except Exception as e:
            print(f"❌ Error with Gemini API: {e}")
            return self.handle_api_failure(text)
    
    def handle_api_failure(self, text: str) -> Dict:
        """
        Handle API failure by returning original text
        """
        print("⚠️ Gemini API unavailable - returning original text")
        
        return {
            'success': False,
            'corrected_text': text,
            'corrections': [],
            'confidence': 0,
            'method': 'Original Text (API Failed)'
        }
    
    def post_process_text(self, text: str) -> str:
        """
        Post-process the corrected text
        """
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Fix line breaks
        text = re.sub(r'\n\s*\n', '\n', text)
        
        # Remove leading/trailing whitespace from each line
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        return '\n'.join(lines)
    
    def process_image(self, image_path: str, psm_mode: int = 6) -> Dict:
        """
        Complete OCR pipeline with Gemini correction
        
        Args:
            image_path: Path to image file
            psm_mode: Tesseract PSM mode
            
        Returns:
            Dictionary with results
        """
        print("🚀 Starting OCR Pipeline with Gemini 2.0 Flash")
        print("=" * 60)
        
        # Check prerequisites
        if not self.check_tesseract():
            return {'error': 'Tesseract OCR not found'}
        
        if not os.path.exists(image_path):
            return {'error': f'Image file not found: {image_path}'}
        
        # Validate image format
        file_ext = os.path.splitext(image_path)[1].lower()
        if file_ext not in self.supported_formats:
            return {'error': f'Unsupported image format: {file_ext}'}
        
        # Get PSM info for documentation
        psm_info = self.get_psm_info()
        psm_description = psm_info.get(psm_mode, {}).get('name', 'Unknown PSM')
        
        # Step 1: Extract text with Tesseract
        print(f"📖 Step 1: Extracting text with Tesseract (PSM {psm_mode}: {psm_description})...")
        print(f"🖼️ Processing: {os.path.basename(image_path)}")
        raw_text = self.extract_text_tesseract(image_path, psm_mode)
        
        if not raw_text:
            return {'error': 'No text extracted from image'}
        
        print(f"✅ Text extracted: {len(raw_text.split())} words")
        
        # Step 2: Correct typos with Gemini
        print("🤖 Step 2: Correcting typos with Gemini...")
        correction_result = self.correct_typo_with_gemini(raw_text)
        
        # Handle API failure gracefully
        if not correction_result['success']:
            print("⚠️ Using original text due to API failure")
            final_text = self.post_process_text(raw_text)
            
            return {
                'image_path': image_path,
                'image_name': os.path.basename(image_path),
                'psm_mode': psm_mode,
                'psm_description': psm_description,
                'raw_text': raw_text,
                'corrected_text': raw_text,
                'final_text': final_text,
                'corrections': [],
                'confidence': 0,
                'method': 'Original Text (API Failed)',
                'statistics': {
                    'raw_words': len(raw_text.split()),
                    'final_words': len(final_text.split()),
                    'corrections_count': 0
                },
                'warning': 'Gemini API was unavailable'
            }
        
        # Step 3: Post-processing
        print("🔧 Step 3: Post-processing...")
        final_text = self.post_process_text(correction_result['corrected_text'])
        
        # Compile results
        result = {
            'image_path': image_path,
            'image_name': os.path.basename(image_path),
            'psm_mode': psm_mode,
            'psm_description': psm_description,
            'raw_text': raw_text,
            'corrected_text': correction_result['corrected_text'],
            'final_text': final_text,
            'corrections': correction_result['corrections'],
            'confidence': correction_result['confidence'],
            'method': correction_result['method'],
            'statistics': {
                'raw_words': len(raw_text.split()),
                'final_words': len(final_text.split()),
                'corrections_count': len(correction_result['corrections'])
            }
        }
        
        return result
    
    def save_results(self, result: Dict, output_file: Optional[str] = None):
        """
        Save results to file
        
        Args:
            result: OCR processing result
            output_file: Output filename (optional, auto-generated if not provided)
        """
        if output_file is None:
            # Generate filename based on image name and timestamp
            image_name = os.path.splitext(result['image_name'])[0]
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            output_file = f"hasil_ocr_{image_name}_{timestamp}.txt"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=== OCR DENGAN GEMINI 2.0 FLASH (IMPROVED) ===\n")
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
            
            # Tambahkan warning jika API gagal
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

    def get_psm_info(self) -> Dict:
        """
        Get comprehensive PSM mode information
        
        Returns:
            Dictionary with PSM modes and their descriptions
        """
        return {
            0: {
                'name': 'OSD only',
                'description': 'Orientation and script detection (OSD) only',
                'use_case': 'Deteksi orientasi dan script saja'
            },
            1: {
                'name': 'Automatic page segmentation with OSD',
                'description': 'Automatic page segmentation with OSD',
                'use_case': 'Segmentasi halaman otomatis dengan OSD'
            },
            2: {
                'name': 'Automatic page segmentation',
                'description': 'Automatic page segmentation, but no OSD, or OCR',
                'use_case': 'Segmentasi halaman otomatis tanpa OSD'
            },
            3: {
                'name': 'Fully automatic',
                'description': 'Fully automatic page segmentation, but no OSD',
                'use_case': 'Default Tesseract - cocok untuk dokumen umum'
            },
            4: {
                'name': 'Single column',
                'description': 'Assume a single column of text of variable sizes',
                'use_case': 'Kolom teks tunggal dengan ukuran bervariasi'
            },
            5: {
                'name': 'Single block',
                'description': 'Assume a single uniform block of vertically aligned text',
                'use_case': 'Blok teks tunggal yang seragam'
            },
            6: {
                'name': 'Single uniform block',
                'description': 'Assume a single uniform block of text',
                'use_case': 'Recommended - Dokumen terstruktur (laporan, form)'
            },
            7: {
                'name': 'Single text line',
                'description': 'Treat the image as a single text line',
                'use_case': 'Baris teks tunggal (header, caption)'
            },
            8: {
                'name': 'Single word',
                'description': 'Treat the image as a single word',
                'use_case': 'Kata tunggal (logo, label)'
            },
            9: {
                'name': 'Single word in circle',
                'description': 'Treat the image as a single word in a circle',
                'use_case': 'Kata dalam lingkaran (stempel, logo)'
            },
            10: {
                'name': 'Single character',
                'description': 'Treat the image as a single character',
                'use_case': 'Karakter tunggal (captcha, angka)'
            },
            11: {
                'name': 'Sparse text',
                'description': 'Sparse text. Find as much text as possible',
                'use_case': 'Teks tersebar - tangkap sebanyak mungkin kata'
            },
            12: {
                'name': 'Sparse text with OSD',
                'description': 'Sparse text with OSD',
                'use_case': 'Teks tersebar dengan deteksi orientasi'
            },
            13: {
                'name': 'Raw line',
                'description': 'Raw line. Treat the image as a single text line',
                'use_case': 'Baris mentah tanpa processing tambahan'
            }
        }
    
    def auto_detect_psm(self, image_path: str) -> Dict:
        """
        Automatic PSM detection by testing multiple modes
        
        Args:
            image_path: Path to image file
            
        Returns:
            Dictionary with recommended PSM and test results
        """
        print("🔍 Mendeteksi PSM terbaik secara otomatis...")
        print("⏳ Testing multiple PSM modes... (ini akan memakan waktu)")
        
        # PSM modes to test (exclude OSD-only and character-specific modes)
        test_modes = [3, 4, 5, 6, 7, 8, 11, 12]
        results = {}
        
        for psm in test_modes:
            try:
                print(f"   Testing PSM {psm}...", end=" ")
                text = self.extract_text_tesseract(image_path, psm)
                
                if text:
                    word_count = len(text.split())
                    char_count = len(text)
                    confidence_score = self.calculate_text_quality(text)
                    
                    results[psm] = {
                        'text': text,
                        'word_count': word_count,
                        'char_count': char_count,
                        'quality_score': confidence_score,
                        'text_preview': text[:50] + "..." if len(text) > 50 else text
                    }
                    print(f"✅ {word_count} kata, quality: {confidence_score:.1f}")
                else:
                    results[psm] = {
                        'text': '',
                        'word_count': 0,
                        'char_count': 0,
                        'quality_score': 0,
                        'text_preview': 'No text detected'
                    }
                    print("❌ No text")
                    
            except Exception as e:
                print(f"❌ Error: {e}")
                results[psm] = {
                    'text': '',
                    'word_count': 0,
                    'char_count': 0,
                    'quality_score': 0,
                    'text_preview': f'Error: {e}'
                }
        
        # Analyze results and recommend best PSM
        if results:
            # Find PSM with best quality score
            best_psm = max(results.keys(), key=lambda x: results[x]['quality_score'])
            
            # Find PSM with most words
            most_words_psm = max(results.keys(), key=lambda x: results[x]['word_count'])
            
            print(f"\n📊 Hasil Auto-Detection:")
            print(f"   🏆 PSM terbaik (quality): {best_psm} (score: {results[best_psm]['quality_score']:.1f})")
            print(f"   📝 PSM terbanyak kata: {most_words_psm} ({results[most_words_psm]['word_count']} kata)")
            
            return {
                'recommended_psm': best_psm,
                'most_words_psm': most_words_psm,
                'test_results': results,
                'best_quality_score': results[best_psm]['quality_score']
            }
        
        return {
            'recommended_psm': 6,  # fallback
            'most_words_psm': 6,
            'test_results': {},
            'best_quality_score': 0
        }
    
    def calculate_text_quality(self, text: str) -> float:
        """
        Calculate text quality score based on various factors
        
        Args:
            text: OCR text to evaluate
            
        Returns:
            Quality score (0-10)
        """
        if not text:
            return 0
        
        score = 0
        
        # Factor 1: Word count (more words = better, up to a point)
        word_count = len(text.split())
        if word_count > 0:
            score += min(word_count / 10, 3)  # Max 3 points
        
        # Factor 2: Character variety (good mix of letters, numbers, spaces)
        char_types = {
            'letters': sum(1 for c in text if c.isalpha()),
            'numbers': sum(1 for c in text if c.isdigit()),
            'spaces': sum(1 for c in text if c.isspace()),
            'punctuation': sum(1 for c in text if c in '.,!?;:()[]{}')
        }
        
        if char_types['letters'] > 0:
            score += 2  # Has letters
        if char_types['numbers'] > 0:
            score += 1  # Has numbers
        if char_types['spaces'] > 0:
            score += 1  # Has proper spacing
        
        # Factor 3: Reasonable text length
        if 10 < len(text) < 1000:
            score += 1
        
        # Factor 4: Not too many special characters (indicates OCR errors)
        special_chars = sum(1 for c in text if not c.isalnum() and c not in ' .,!?;:()[]{}')
        if special_chars < len(text) * 0.1:  # Less than 10% special chars
            score += 1
        
        # Factor 5: Indonesian/English common words
        common_words = ['dan', 'atau', 'yang', 'dengan', 'untuk', 'dari', 'ke', 'di', 'pada', 'dalam',
                       'the', 'and', 'or', 'of', 'to', 'in', 'for', 'with', 'on', 'at']
        
        text_lower = text.lower()
        found_common = sum(1 for word in common_words if word in text_lower)
        if found_common > 0:
            score += min(found_common / 5, 1)  # Max 1 point
        
        return min(score, 10)  # Cap at 10
    
    def choose_psm_mode(self, image_path: str) -> int:
        """
        Interactive PSM mode selection with automatic detection option
        
        Args:
            image_path: Path to image file
            
        Returns:
            Selected PSM mode
        """
        psm_info = self.get_psm_info()
        
        print(f"\n🔧 PILIH PSM MODE:")
        print("=" * 50)
        
        # Show common PSM modes first
        common_psms = [3, 6, 11, 7, 8]
        print("📋 Mode Umum:")
        for psm in common_psms:
            info = psm_info[psm]
            print(f"   {psm:2d}. {info['name']:<25} - {info['use_case']}")
        
        print(f"\n🤖 Automatic Detection:")
        print(f"   99. Auto-detect PSM terbaik (testing multiple modes)")
        print(f"   98. Tampilkan semua PSM modes")
        
        print(f"\n💡 Berdasarkan analisis sebelumnya:")
        print(f"   - PSM 6: Hasil terbersih (Recommended)")
        print(f"   - PSM 11: Menangkap kata terbanyak")
        print(f"   - PSM 3: Default Tesseract")
        
        while True:
            try:
                choice = input(f"\nPilih PSM mode (default: 6): ").strip()
                
                if not choice:
                    return 6
                
                choice = int(choice)
                
                if choice == 99:
                    # Auto-detect
                    auto_result = self.auto_detect_psm(image_path)
                    recommended = auto_result['recommended_psm']
                    
                    print(f"\n🎯 Auto-detection merekomendasikan PSM {recommended}")
                    confirm = input("Gunakan rekomendasi ini? (y/n, default: y): ").strip().lower()
                    
                    if confirm in ['', 'y', 'yes']:
                        return recommended
                    else:
                        continue
                
                elif choice == 98:
                    # Show all PSM modes
                    print(f"\n📚 SEMUA PSM MODES:")
                    print("=" * 60)
                    for psm, info in psm_info.items():
                        print(f"{psm:2d}. {info['name']:<30} - {info['use_case']}")
                    continue
                
                elif choice in psm_info:
                    return choice
                
                else:
                    print(f"❌ PSM {choice} tidak valid. Pilih 0-13, 98, atau 99")
                    
            except ValueError:
                print("❌ Input tidak valid. Masukkan angka.")
            except KeyboardInterrupt:
                print("\n❌ Dibatalkan oleh user")
                return 6

def main():
    """
    Main function to run OCR with Gemini correction
    """
    print("🤖 OCR Pipeline dengan Gemini 2.0 Flash (Improved)")
    print("=" * 60)
    
    try:
        # Initialize OCR (akan load API key dari .env)
        ocr_gemini = OCRWithGemini()
        
        # Get image path (dynamic input)
        image_path = ocr_gemini.get_image_path()
        
        if not image_path:
            print("❌ Tidak ada gambar yang dipilih. Keluar dari program.")
            return
        
        # Choose PSM mode (with automatic detection)
        psm_mode = ocr_gemini.choose_psm_mode(image_path)
        
        # Process image
        result = ocr_gemini.process_image(image_path, psm_mode=psm_mode)
        
        if 'error' in result:
            print(f"❌ Error: {result['error']}")
            return
        
        # Save results
        output_file = ocr_gemini.save_results(result)
        
        # Display results
        print("\n" + "="*60)
        print("📊 HASIL KOREKSI GEMINI")
        print("="*60)
        
        print(f"\n📈 Statistik:")
        print(f"   Gambar: {result['image_name']}")
        print(f"   PSM Mode: {result['psm_mode']} ({result.get('psm_description', 'N/A')})")
        print(f"   Kata mentah: {result['statistics']['raw_words']}")
        print(f"   Kata final: {result['statistics']['final_words']}")
        print(f"   Koreksi dilakukan: {result['statistics']['corrections_count']}")
        print(f"   Confidence: {result['confidence']}/10")
        print(f"   Metode: {result['method']}")
        
        if result['corrections']:
            print(f"\n🔧 Koreksi yang dilakukan:")
            for correction in result['corrections']:
                print(f"   '{correction['original']}' → '{correction['corrected']}' ({correction['reason']})")
        
        print(f"\n🔤 Teks Mentah (OCR):")
        print("-" * 40)
        print(result['raw_text'])
        
        print(f"\n🤖 Teks Terkoreksi (Gemini):")
        print("-" * 40)
        print(result['final_text'])
        
        print(f"\n💾 Hasil disimpan ke: {output_file}")
        print("✅ Pipeline dengan Gemini selesai!")
        
    except ValueError as e:
        print(f"❌ {e}")
        print("💡 Pastikan file .env berisi GEMINI_API_KEY yang valid")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()
