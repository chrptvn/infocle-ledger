import os
import logging
import base64
import json
import urllib.request
import urllib.parse
import urllib.error
from typing import Optional, Tuple
from tkinter import messagebox
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TextExtractor:
    """Handles text extraction from various file types."""
    
    def __init__(self):
        self.supported_extensions = {'.pdf', '.txt', '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'}
        self.config = Config()
    
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
        """Extract text from image using OpenAI Vision API."""
        try:
            api_key = self.config.get_openai_api_key()
            if not api_key:
                return False, "OpenAI API key not configured. Please set your API key in the configuration."
            
            # Read and encode the image
            with open(file_path, 'rb') as image_file:
                image_data = image_file.read()
                base64_image = base64.b64encode(image_data).decode('utf-8')
            
            # Prepare the API request
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {api_key}'
            }
            
            payload = {
                "model": self.config.get_openai_model(),
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Please extract all text from this image. Return only the text content, no additional commentary."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 1000
            }
            
            # Make the API request
            request = urllib.request.Request(
                'https://api.openai.com/v1/chat/completions',
                data=json.dumps(payload).encode('utf-8'),
                headers=headers
            )
            
            with urllib.request.urlopen(request) as response:
                result = json.loads(response.read().decode('utf-8'))
                
                if 'choices' in result and len(result['choices']) > 0:
                    extracted_text = result['choices'][0]['message']['content']
                    return True, extracted_text.strip()
                else:
                    return False, "No text extracted from the API response"
                    
        except urllib.error.HTTPError as e:
            error_msg = f"OpenAI API error: {e.code} - {e.reason}"
            if e.code == 401:
                error_msg = "Invalid OpenAI API key. Please check your configuration."
            elif e.code == 429:
                error_msg = "OpenAI API rate limit exceeded. Please try again later."
            return False, error_msg
        except Exception as e:
            return False, f"Error extracting text from image: {str(e)}"
    
    def configure_api_key(self, parent_widget=None):
        """Show dialog to configure OpenAI API key."""
        from tkinter import simpledialog
        
        current_key = self.config.get_openai_api_key() or ""
        masked_key = f"{'*' * (len(current_key) - 8)}{current_key[-8:]}" if len(current_key) > 8 else current_key
        
        prompt = f"Enter your OpenAI API key:\n(Current: {masked_key if current_key else 'Not set'})"
        
        new_key = simpledialog.askstring(
            "Configure OpenAI API Key",
            prompt,
            show='*' if current_key else None
        )
        
        if new_key and new_key.strip():
            self.config.set_openai_api_key(new_key.strip())
            if parent_widget:
                messagebox.showinfo("Configuration", "OpenAI API key has been saved successfully!")
            return True
        return False

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