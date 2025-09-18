import os
import logging
from typing import Optional, Tuple
from tkinter import messagebox

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TextExtractor:
    """Handles text extraction from various file types."""
    
    def __init__(self):
        self.supported_extensions = {'.pdf', '.txt', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'}
    
    def can_extract(self, file_path: str) -> bool:
        """Check if the file type is supported for text extraction."""
        _, ext = os.path.splitext(file_path.lower())
        return ext in self.supported_extensions
    
    def extract_text(self, file_path: str) -> Tuple[bool, str]:
        """
        Extract text from a file.
        Returns (success, text) tuple.
        """
        if not os.path.exists(file_path):
            return False, "File not found"
        
        _, ext = os.path.splitext(file_path.lower())
        
        try:
            if ext == '.pdf':
                return self._extract_from_pdf(file_path)
            elif ext == '.txt':
                return self._extract_from_txt(file_path)
            elif ext in {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'}:
                return self._extract_from_image(file_path)
            else:
                return False, f"Unsupported file type: {ext}"
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {str(e)}")
            return False, f"Error extracting text: {str(e)}"
    
    def _extract_from_pdf(self, file_path: str) -> Tuple[bool, str]:
        """Extract text from PDF file."""
        try:
            import PyPDF2
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return True, text.strip()
        except ImportError:
            # Fallback: Try with pdfplumber if PyPDF2 is not available
            try:
                import pdfplumber
                with pdfplumber.open(file_path) as pdf:
                    text = ""
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                    return True, text.strip()
            except ImportError:
                return False, "PDF extraction requires PyPDF2 or pdfplumber library. Please install with: pip install PyPDF2"
    
    def _extract_from_txt(self, file_path: str) -> Tuple[bool, str]:
        """Extract text from text file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()
            return True, text.strip()
        except UnicodeDecodeError:
            # Try with different encoding
            try:
                with open(file_path, 'r', encoding='latin-1') as file:
                    text = file.read()
                return True, text.strip()
            except Exception as e:
                return False, f"Error reading text file: {str(e)}"
    
    def _extract_from_image(self, file_path: str) -> Tuple[bool, str]:
        """Extract text from image using OCR."""
        try:
            import pytesseract
            from PIL import Image
            
            # Open and process the image
            image = Image.open(file_path)
            text = pytesseract.image_to_string(image)
            return True, text.strip()
        except ImportError:
            return False, "OCR extraction requires pytesseract and Pillow libraries. Please install with: pip install pytesseract Pillow"
        except Exception as e:
            return False, f"Error extracting text from image: {str(e)}"

def show_extracted_text_dialog(parent, extracted_text: str, filename: str) -> bool:
    """
    Show a dialog with the extracted text and return True if user clicks OK.
    """
    # Create a custom dialog
    import tkinter as tk
    from tkinter import ttk, scrolledtext
    
    dialog = tk.Toplevel(parent)
    dialog.title(f"Bill Parsed - {filename}")
    dialog.geometry("600x400")
    dialog.transient(parent)
    dialog.grab_set()
    
    # Center the dialog
    dialog.geometry("+%d+%d" % (
        parent.winfo_rootx() + 50, 
        parent.winfo_rooty() + 50
    ))
    
    # Main frame
    main_frame = ttk.Frame(dialog, padding="10")
    main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    
    # Configure grid weights
    dialog.columnconfigure(0, weight=1)
    dialog.rowconfigure(0, weight=1)
    main_frame.columnconfigure(0, weight=1)
    main_frame.rowconfigure(1, weight=1)
    
    # Title label
    title_label = ttk.Label(main_frame, text="✅ Bill has been successfully parsed!", 
                           font=('TkDefaultFont', 12, 'bold'))
    title_label.grid(row=0, column=0, pady=(0, 10))
    
    # Text display
    text_frame = ttk.LabelFrame(main_frame, text="Extracted Text", padding="5")
    text_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
    text_frame.columnconfigure(0, weight=1)
    text_frame.rowconfigure(0, weight=1)
    
    text_widget = scrolledtext.ScrolledText(text_frame, wrap=tk.WORD, height=15, width=70)
    text_widget.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    text_widget.insert(tk.END, extracted_text)
    text_widget.config(state=tk.DISABLED)  # Make it read-only
    
    # Button frame
    btn_frame = ttk.Frame(main_frame)
    btn_frame.grid(row=2, column=0, pady=(10, 0))
    
    # Result variable
    result = {'clicked_ok': False}
    
    def on_ok():
        result['clicked_ok'] = True
        dialog.destroy()
    
    def on_cancel():
        result['clicked_ok'] = False
        dialog.destroy()
    
    ttk.Button(btn_frame, text="OK - Import File", command=on_ok).grid(
        row=0, column=0, padx=(0, 5)
    )
    ttk.Button(btn_frame, text="Cancel", command=on_cancel).grid(
        row=0, column=1
    )
    
    # Wait for dialog to close
    dialog.wait_window()
    
    return result['clicked_ok']