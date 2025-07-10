# views/ocr_view.py
"""
View layer untuk OCR aplikasi
Menangani semua user interface dan output formatting
"""

import os
from typing import Dict, List, Optional


class OCRView:
    """View untuk menampilkan UI dan hasil OCR"""
    
    def __init__(self):
        """Initialize OCR View"""
        pass
    
    def show_welcome(self):
        """Display welcome message"""
        print("🤖 OCR Pipeline dengan Gemini 2.0 Flash (MVC Version)")
        print("=" * 60)
        print("📁 Gambar akan dicari di folder: ./gambar/")
        print()
    
    def show_error(self, message: str, details: Optional[str] = None):
        """Display error message"""
        print(f"❌ Error: {message}")
        if details:
            print(f"💡 {details}")
    
    def show_warning(self, message: str):
        """Display warning message"""
        print(f"⚠️ Warning: {message}")
    
    def show_success(self, message: str):
        """Display success message"""
        print(f"✅ {message}")
    
    def show_info(self, message: str, emoji: str = "ℹ️"):
        """Display info message"""
        print(f"{emoji} {message}")
    
    def show_image_selection_menu(self, image_files: List[str]) -> int:
        """Display image selection menu and get user choice"""
        if not image_files:
            print("❌ Tidak ada gambar ditemukan di folder 'gambar'!")
            print("💡 Pastikan ada file gambar (jpg, png, dll) di folder './gambar/'")
            return -1
        
        print(f"📁 Ditemukan {len(image_files)} gambar:")
        print("-" * 40)
        
        for i, file_path in enumerate(image_files, 1):
            filename = os.path.basename(file_path)
            file_size = self._get_file_size(file_path)
            print(f"   {i:2d}. {filename:<25} ({file_size})")
        
        print(f"   {len(image_files) + 1:2d}. Input path manual")
        print("    0. Keluar")
        
        while True:
            try:
                choice = input(f"\nPilih gambar (1-{len(image_files) + 1}): ").strip()
                
                if not choice:
                    continue
                
                choice = int(choice)
                
                if choice == 0:
                    return -1
                elif 1 <= choice <= len(image_files):
                    return choice - 1  # Convert to 0-based index
                elif choice == len(image_files) + 1:
                    return -2  # Manual input
                else:
                    print(f"❌ Pilihan tidak valid. Masukkan 1-{len(image_files) + 1} atau 0 untuk keluar")
                    
            except ValueError:
                print("❌ Input tidak valid. Masukkan angka.")
            except KeyboardInterrupt:
                print("\n❌ Dibatalkan oleh user")
                return -1
    
    def get_manual_image_path(self) -> str:
        """Get manual image path from user"""
        while True:
            try:
                path = input("🖼️ Masukkan path gambar: ").strip().strip('"\'')
                if path:
                    return path
                print("❌ Path tidak boleh kosong!")
            except KeyboardInterrupt:
                print("\n❌ Dibatalkan oleh user")
                return ""
    
    def show_psm_selection_menu(self, psm_info: Dict, recommended_psm: Optional[int] = None) -> int:
        """Display PSM mode selection menu"""
        common_psms = [3, 4, 5, 6, 7, 8, 11, 12]
        
        print(f"\n🔧 PILIH PSM MODE")
        print("=" * 60)
        print("📋 Mode Umum:")
        
        for psm in common_psms:
            info = psm_info[psm]
            marker = " (🌟 Recommended)" if psm == recommended_psm else ""
            print(f"   {psm:2d}. {info['name']:<25} - {info['use_case']}{marker}")
        
        print(f"\n🤖 Automatic Detection:")
        print(f"   99. Auto-detect PSM terbaik (testing multiple modes)")
        print(f"   98. Tampilkan semua PSM modes")
        
        if recommended_psm:
            print(f"\n💡 Berdasarkan analisis sebelumnya:")
            print(f"   - PSM {recommended_psm}: Hasil terbersih (Recommended)")
        
        print(f"   - PSM 6: Default untuk dokumen terstruktur")
        print(f"   - PSM 11: Menangkap kata terbanyak")
        print(f"   - PSM 3: Default Tesseract")
        
        while True:
            try:
                choice = input(f"\nPilih PSM mode (default: {recommended_psm or 6}): ").strip()
                
                if not choice:
                    return recommended_psm or 6
                
                choice = int(choice)
                
                if choice == 99:
                    return 99  # Auto-detect signal
                elif choice == 98:
                    self._show_all_psm_modes(psm_info)
                    continue
                elif choice in psm_info:
                    return choice
                else:
                    print(f"❌ PSM {choice} tidak valid. Pilih 0-13, 98, atau 99")
                    
            except ValueError:
                print("❌ Input tidak valid. Masukkan angka.")
            except KeyboardInterrupt:
                print("\n❌ Dibatalkan oleh user")
                return recommended_psm or 6
    
    def _show_all_psm_modes(self, psm_info: Dict):
        """Show all PSM modes"""
        print(f"\n📚 SEMUA PSM MODES:")
        print("=" * 80)
        for psm, info in psm_info.items():
            print(f"{psm:2d}. {info['name']:<30} - {info['use_case']}")
    
    def show_auto_detection_result(self, recommended_psm: int, quality_score: float) -> bool:
        """Show auto-detection result and get confirmation"""
        print(f"\n🎯 Auto-detection merekomendasikan PSM {recommended_psm}")
        print(f"   Quality Score: {quality_score:.1f}/10")
        
        confirm = input("Gunakan rekomendasi ini? (y/n, default: y): ").strip().lower()
        return confirm in ['', 'y', 'yes']
    
    def show_processing_status(self, step: str, image_name: str):
        """Show processing status"""
        if step == "tesseract":
            print(f"🔍 Mengekstrak teks dari {image_name}...")
        elif step == "correction":
            print(f"🤖 Mengoreksi typo dengan Gemini AI...")
        elif step == "postprocess":
            print(f"✨ Post-processing teks...")
        elif step == "saving":
            print(f"💾 Menyimpan hasil...")
    
    def show_results_summary(self, result: Dict):
        """Display comprehensive results summary"""
        print("\n" + "="*60)
        print("📊 HASIL KOREKSI GEMINI")
        print("="*60)
        
        # Basic information
        print(f"\n📈 Informasi:")
        print(f"   Gambar: {result['image_name']}")
        print(f"   PSM Mode: {result['psm_mode']} ({result.get('psm_description', 'N/A')})")
        print(f"   Metode: {result['method']}")
        print(f"   Confidence: {result['confidence']}/10")
        
        # Statistics
        print(f"\n📊 Statistik:")
        stats = result['statistics']
        print(f"   Kata mentah: {stats['raw_words']}")
        print(f"   Kata final: {stats['final_words']}")
        print(f"   Koreksi dilakukan: {stats['corrections_count']}")
        
        # Show warning if present
        if 'warning' in result:
            print(f"   ⚠️ Warning: {result['warning']}")
        
        # Show corrections if any
        if result['corrections']:
            print(f"\n🔧 Koreksi yang dilakukan:")
            for correction in result['corrections']:
                print(f"   '{correction['original']}' → '{correction['corrected']}' ({correction['reason']})")
        
        # Show texts
        print(f"\n🔤 Teks Mentah (OCR):")
        print("-" * 40)
        print(result['raw_text'] if result['raw_text'] else "(Tidak ada teks terdeteksi)")
        
        print(f"\n🤖 Teks Terkoreksi (Gemini):")
        print("-" * 40)
        print(result['final_text'] if result['final_text'] else "(Tidak ada teks terdeteksi)")
    
    def show_save_confirmation(self, output_file: str):
        """Show save confirmation"""
        print(f"\n💾 Hasil disimpan ke: {output_file}")
        print("✅ Pipeline dengan Gemini selesai!")
    
    def show_tesseract_check(self, available: bool):
        """Show Tesseract availability status"""
        if available:
            print("✅ Tesseract OCR tersedia")
        else:
            print("❌ Tesseract OCR tidak ditemukan!")
            print("💡 Install Tesseract dari: https://github.com/tesseract-ocr/tesseract")
    
    def show_auto_detection_progress(self, current_psm: int, total_psms: int):
        """Show auto-detection progress"""
        print(f"🔍 Testing PSM {current_psm}... ({current_psm}/{total_psms})")
    
    def show_auto_detection_results(self, results: Dict):
        """Show detailed auto-detection results"""
        print(f"\n📊 HASIL AUTO-DETECTION:")
        print("=" * 60)
        
        for psm, data in results['test_results'].items():
            quality = data['quality_score']
            words = data['word_count']
            preview = data['text_preview']
            
            print(f"PSM {psm:2d}: Quality {quality:4.1f} | Words {words:3d} | {preview}")
        
        print(f"\n🏆 Rekomendasi: PSM {results['recommended_psm']} (Quality: {results['best_quality_score']:.1f})")
        print(f"📝 Kata terbanyak: PSM {results['most_words_psm']}")
    
    def _get_file_size(self, file_path: str) -> str:
        """Get formatted file size"""
        try:
            size = os.path.getsize(file_path)
            if size < 1024:
                return f"{size}B"
            elif size < 1024 * 1024:
                return f"{size/1024:.1f}KB"
            else:
                return f"{size/(1024*1024):.1f}MB"
        except:
            return "N/A"
