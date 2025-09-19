import os
import logging
import json
import requests
from typing import Optional, Tuple
from tkinter import messagebox
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OPENAI_API_BASE = "https://api.openai.com/v1"

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
        """Extract text from a file. Returns (success, text)."""
        if not os.path.exists(file_path):
            return False, "File not found"

        _, ext = os.path.splitext(file_path.lower())
        try:
            if ext == '.pdf':
                return self._extract_from_pdf_with_openai(file_path)
            elif ext == '.txt':
                return self._extract_from_txt(file_path)
            elif ext in {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'}:
                return self._extract_from_image_with_openai(file_path)
            else:
                return False, f"Unsupported file type: {ext}"
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {str(e)}", exc_info=True)
            return False, f"Error extracting text: {str(e)}"

    def _headers(self):
        api_key = self.config.get_openai_api_key()
        if not api_key:
            raise RuntimeError("OpenAI API key not configured")
        return {"Authorization": f"Bearer {api_key}"}

    def _upload_file(self, path: str, purpose: str = "user_data") -> str:
        """Upload a file and return its file_id."""
        with open(path, "rb") as f:
            files = {
                "file": (os.path.basename(path), f),
                "purpose": (None, purpose),
            }
            r = requests.post(f"{OPENAI_API_BASE}/files", headers=self._headers(), files=files, timeout=300)
        if r.status_code >= 300:
            raise RuntimeError(f"File upload failed: {r.status_code} {r.text}")
        return r.json()["id"]

    def _ask_model_with_file(self, file_id: str, prompt: str, max_tokens: int = 4000) -> str:
        """Call the Responses API with a file reference."""
        payload = {
            "model": self.config.get_openai_model() or "gpt-4o-mini",
            "input": [
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": prompt},
                        {"type": "input_file", "file_id": file_id}
                    ],
                }
            ],
            "max_output_tokens": max_tokens
        }
        r = requests.post(
            f"{OPENAI_API_BASE}/responses",
            headers={**self._headers(), "Content-Type": "application/json"},
            data=json.dumps(payload),
            timeout=600
        )
        if r.status_code >= 300:
            raise RuntimeError(f"Responses API error: {r.status_code} {r.text}")
        data = r.json()
        return data["output"][0]["content"][0]["text"]

    def _extract_from_pdf_with_openai(self, file_path: str) -> Tuple[bool, str]:
        try:
            file_id = self._upload_file(file_path, purpose="user_data")
            text = self._ask_model_with_file(
                file_id,
                "Extract all textual content from this PDF document in reading order. Return only the text, no commentary.",
                max_tokens=8000
            )
            return True, text.strip()
        except Exception as e:
            return False, f"Error extracting text from PDF: {str(e)}"

    def _extract_from_image_with_openai(self, file_path: str) -> Tuple[bool, str]:
        try:
            file_id = self._upload_file(file_path, purpose="user_data")
            text = self._ask_model_with_file(
                file_id,
                "Perform OCR on this image. Return only the recognized text.",
                max_tokens=4000
            )
            return True, text.strip()
        except Exception as e:
            return False, f"Error extracting text from image: {str(e)}"

    def _extract_from_txt(self, file_path: str) -> Tuple[bool, str]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return True, f.read().strip()
        except UnicodeDecodeError:
            with open(file_path, 'r', encoding='latin-1') as f:
                return True, f.read().strip()

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
    text_widget.config(state=tk.DISABLED)

    # Button frame
    btn_frame = ttk.Frame(main_frame)
    btn_frame.grid(row=2, column=0, pady=(10, 0))

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

    dialog.wait_window()
    return result['clicked_ok']
