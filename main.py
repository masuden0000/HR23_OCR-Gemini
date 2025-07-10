#!/usr/bin/env python3
"""
OCR Pipeline dengan Gemini 2.0 Flash - MVC Version
Refactored menggunakan Model-View-Controller pattern untuk better organization

Main entry point untuk aplikasi OCR
"""

import sys
import os
from typing import Optional

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from controllers.ocr_controller import OCRController


def main():
    """
    Main function untuk menjalankan OCR aplikasi dengan MVC pattern
    """
    try:
        # Initialize dan jalankan controller
        controller = OCRController()
        controller.run()
        
    except ValueError as e:
        print(f"❌ Configuration Error: {e}")
        print("💡 Pastikan file .env berisi GEMINI_API_KEY yang valid")
        sys.exit(1)
        
    except KeyboardInterrupt:
        print("\n❌ Program dihentikan oleh user")
        sys.exit(0)
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


def batch_mode(directory: str = "gambar", psm_mode: int = 6):
    """
    Batch processing mode untuk memproses semua gambar dalam folder
    
    Args:
        directory: Folder yang berisi gambar
        psm_mode: PSM mode yang akan digunakan
    """
    try:
        controller = OCRController()
        results = controller.batch_process_images(directory, psm_mode)
        return results
        
    except Exception as e:
        print(f"❌ Batch processing error: {e}")
        return []


def process_single(image_path: str, psm_mode: int = 6, api_key: Optional[str] = None) -> dict:
    """
    Process single image programmatically
    Berguna untuk integrasi dengan script lain
    
    Args:
        image_path: Path ke file gambar
        psm_mode: PSM mode (default: 6)
        api_key: Optional API key override
        
    Returns:
        Dictionary dengan hasil processing
    """
    try:
        controller = OCRController(api_key)
        result = controller.process_single_image(image_path, psm_mode)
        return result or {}
        
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    # Check untuk command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "batch":
            # Batch mode
            directory = sys.argv[2] if len(sys.argv) > 2 else "gambar"
            psm_mode = int(sys.argv[3]) if len(sys.argv) > 3 else 6
            
            print(f"🔄 Running in batch mode: {directory} (PSM: {psm_mode})")
            batch_mode(directory, psm_mode)
            
        elif command == "single":
            # Single file mode
            if len(sys.argv) < 3:
                print("❌ Usage: python main.py single <image_path> [psm_mode]")
                sys.exit(1)
                
            image_path = sys.argv[2]
            psm_mode = int(sys.argv[3]) if len(sys.argv) > 3 else 6
            
            print(f"📸 Processing single image: {image_path} (PSM: {psm_mode})")
            result = process_single(image_path, psm_mode)
            
            if "error" in result:
                print(f"❌ Error: {result['error']}")
            else:
                print("✅ Processing completed successfully")
                
        elif command == "help":
            print("🤖 OCR Pipeline dengan Gemini 2.0 Flash - MVC Version")
            print("=" * 60)
            print("Usage:")
            print("  python main.py                    # Interactive mode (default)")
            print("  python main.py batch [dir] [psm]  # Batch process all images")
            print("  python main.py single <img> [psm] # Process single image")
            print("  python main.py help               # Show this help")
            print()
            print("Examples:")
            print("  python main.py")
            print("  python main.py batch")
            print("  python main.py batch gambar 6")
            print("  python main.py single gambar/test.jpg 11")
            
        else:
            print(f"❌ Unknown command: {command}")
            print("💡 Use 'python main.py help' for usage information")
            sys.exit(1)
    else:
        # Default: interactive mode
        main()
