# controllers/ocr_controller.py
"""
Controller layer untuk OCR aplikasi
Menangani workflow dan koordinasi antara Model dan View
"""

import os
from typing import Dict, List, Optional
from models.ocr_model import OCRModel
from views.ocr_view import OCRView


class OCRController:
    """Controller untuk mengatur alur kerja OCR aplikasi"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize OCR Controller dengan Model dan View"""
        try:
            self.model = OCRModel(api_key)
            self.view = OCRView()
            self.psm_info = self.model.get_psm_info()
        except Exception as e:
            self.view = OCRView()
            self.view.show_error(str(e), "Pastikan file .env berisi GEMINI_API_KEY yang valid")
            raise
    
    def run(self):
        """Main method untuk menjalankan aplikasi OCR"""
        try:
            # Show welcome message
            self.view.show_welcome()
            
            # Check Tesseract availability
            if not self.model.check_tesseract():
                self.view.show_tesseract_check(False)
                return
            else:
                self.view.show_tesseract_check(True)
            
            # Get image path
            image_path = self._get_image_path()
            if not image_path:
                self.view.show_error("Tidak ada gambar yang dipilih")
                return
            
            # Choose PSM mode
            psm_mode = self._choose_psm_mode(image_path)
            if psm_mode is None:
                self.view.show_error("PSM mode tidak dipilih")
                return
            
            # Process image
            result = self._process_image(image_path, psm_mode)
            if not result:
                return
            
            # Save and display results
            self._handle_results(result)
            
        except KeyboardInterrupt:
            self.view.show_error("Dibatalkan oleh user")
        except Exception as e:
            self.view.show_error(f"Unexpected error: {e}")
    
    def _get_image_path(self) -> Optional[str]:
        """Get image path from user selection"""
        # Find available images
        image_files = self.model.find_image_files()
        
        # Show selection menu
        choice = self.view.show_image_selection_menu(image_files)
        
        if choice == -1:
            # User chose to exit
            return None
        elif choice == -2:
            # Manual input
            manual_path = self.view.get_manual_image_path()
            if manual_path and os.path.exists(manual_path):
                return manual_path
            else:
                self.view.show_error("File tidak ditemukan", f"Path: {manual_path}")
                return None
        elif 0 <= choice < len(image_files):
            # Selected from list
            return image_files[choice]
        else:
            self.view.show_error("Pilihan tidak valid")
            return None
    
    def _choose_psm_mode(self, image_path: str) -> Optional[int]:
        """Choose PSM mode with optional auto-detection"""
        # Get initial recommendation (could be from previous analysis)
        recommended_psm = 6  # Default recommendation
        
        # Show PSM selection menu
        choice = self.view.show_psm_selection_menu(self.psm_info, recommended_psm)
        
        if choice == 99:
            # Auto-detect PSM
            return self._auto_detect_psm(image_path)
        else:
            return choice
    
    def _auto_detect_psm(self, image_path: str) -> Optional[int]:
        """Perform auto PSM detection"""
        self.view.show_info("Melakukan auto-detection PSM mode...", "🔍")
        
        # Get auto-detection results
        auto_result = self.model.auto_detect_psm(image_path)
        
        if not auto_result['test_results']:
            self.view.show_error("Auto-detection gagal")
            return 6  # Fallback to default
        
        # Show detailed results
        self.view.show_auto_detection_results(auto_result)
        
        # Get user confirmation
        recommended_psm = auto_result['recommended_psm']
        quality_score = auto_result['best_quality_score']
        
        if self.view.show_auto_detection_result(recommended_psm, quality_score):
            return recommended_psm
        else:
            # User declined, show selection menu again
            return self.view.show_psm_selection_menu(self.psm_info, recommended_psm)
    
    def _process_image(self, image_path: str, psm_mode: int) -> Optional[Dict]:
        """Process image with selected PSM mode"""
        try:
            image_name = os.path.basename(image_path)
            
            # Step 1: Extract text with Tesseract
            self.view.show_processing_status("tesseract", image_name)
            raw_text = self.model.extract_text_tesseract(image_path, psm_mode)
            
            if not raw_text:
                self.view.show_warning("Tidak ada teks yang terdeteksi dari gambar")
                # Continue with empty text for consistency
            
            # Step 2: Correct typos with Gemini
            self.view.show_processing_status("correction", image_name)
            correction_result = self.model.correct_typo_with_gemini(raw_text)
            
            # Step 3: Post-process text
            self.view.show_processing_status("postprocess", image_name)
            final_text = self.model.post_process_text(correction_result['corrected_text'])
            
            # Prepare result
            result = {
                'image_path': image_path,
                'image_name': image_name,
                'psm_mode': psm_mode,
                'psm_description': self.psm_info[psm_mode]['name'],
                'raw_text': raw_text,
                'corrected_text': correction_result['corrected_text'],
                'final_text': final_text,
                'corrections': correction_result['corrections'],
                'confidence': correction_result['confidence'],
                'method': correction_result['method'],
                'statistics': {
                    'raw_words': len(raw_text.split()) if raw_text else 0,
                    'final_words': len(final_text.split()) if final_text else 0,
                    'corrections_count': len(correction_result['corrections'])
                }
            }
            
            # Add warning if API failed
            if not correction_result['success']:
                result['warning'] = 'Gemini API tidak tersedia, menggunakan teks original'
            
            return result
            
        except Exception as e:
            self.view.show_error(f"Error saat processing: {e}")
            return None
    
    def _handle_results(self, result: Dict):
        """Handle and display results"""
        try:
            # Step 4: Save results
            self.view.show_processing_status("saving", result['image_name'])
            output_file = self.model.save_results(result)
            
            # Display comprehensive results
            self.view.show_results_summary(result)
            
            # Show save confirmation
            self.view.show_save_confirmation(output_file)
            
        except Exception as e:
            self.view.show_error(f"Error saat menyimpan hasil: {e}")
    
    def process_single_image(self, image_path: str, psm_mode: int = 6, save_results: bool = True) -> Optional[Dict]:
        """
        Process single image programmatically (for API usage)
        
        Args:
            image_path: Path to image file
            psm_mode: PSM mode to use
            save_results: Whether to save results to file
            
        Returns:
            Processing result dictionary or None if failed
        """
        try:
            if not os.path.exists(image_path):
                return None
            
            result = self._process_image(image_path, psm_mode)
            
            if result and save_results:
                self.model.save_results(result)
            
            return result
            
        except Exception:
            return None
    
    def batch_process_images(self, directory: str = "gambar", psm_mode: int = 6) -> List[Dict]:
        """
        Process all images in directory
        
        Args:
            directory: Directory containing images
            psm_mode: PSM mode to use for all images
            
        Returns:
            List of processing results
        """
        results = []
        image_files = self.model.find_image_files(directory)
        
        if not image_files:
            self.view.show_error(f"Tidak ada gambar ditemukan di folder '{directory}'")
            return results
        
        self.view.show_info(f"Memproses {len(image_files)} gambar dalam batch mode...", "🔄")
        
        for i, image_path in enumerate(image_files, 1):
            try:
                self.view.show_info(f"[{i}/{len(image_files)}] Processing {os.path.basename(image_path)}", "📸")
                
                result = self._process_image(image_path, psm_mode)
                if result:
                    # Save each result
                    self.model.save_results(result)
                    results.append(result)
                    self.view.show_success(f"Berhasil: {result['image_name']}")
                else:
                    self.view.show_warning(f"Gagal: {os.path.basename(image_path)}")
                    
            except Exception as e:
                self.view.show_error(f"Error processing {os.path.basename(image_path)}: {e}")
        
        self.view.show_success(f"Batch processing selesai: {len(results)}/{len(image_files)} berhasil")
        return results
