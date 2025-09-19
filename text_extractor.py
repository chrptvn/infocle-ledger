import os
import logging
import json
import requests
from typing import Optional, Tuple, List, Dict, Any
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

    # -------------------- Public API --------------------

    def extract_text(self, file_path: str, categories: List[str]) -> Tuple[bool, str]:
        """
        Extracts and structures bill data from a file using the OpenAI Responses API.
        Returns (success, json_string).
        """
        if not os.path.exists(file_path):
            return False, "File not found"

        _, ext = os.path.splitext(file_path.lower())
        try:
            if ext == '.txt':
                ok, raw = self._extract_from_txt(file_path)
                if not ok:
                    return False, raw
                bill = self._wrap_plain_text_as_bill(raw, categories or [])
                return True, json.dumps(bill, ensure_ascii=False, indent=2)

            # For PDFs and images, use the Responses API with file upload
            return self._extract_bill_via_responses_api(file_path, categories or [])
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {str(e)}", exc_info=True)
            return False, f"Error extracting text: {str(e)}"

    # -------------------- OpenAI plumbing --------------------

    def _headers(self) -> Dict[str, str]:
        api_key = self.config.get_openai_api_key()
        if not api_key:
            raise RuntimeError("OpenAI API key not configured")
        return {"Authorization": f"Bearer {api_key}"}

    def _upload_file(self, path: str, purpose: str = "user_data") -> str:
        """Uploads a file to OpenAI Files API and returns its file_id."""
        with open(path, "rb") as f:
            files = {
                "file": (os.path.basename(path), f),
                "purpose": (None, purpose),
            }
            r = requests.post(f"{OPENAI_API_BASE}/files", headers=self._headers(), files=files, timeout=300)
        if r.status_code >= 300:
            raise RuntimeError(f"File upload failed: {r.status_code} {r.text}")
        return r.json()["id"]

    def _responses_post(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        r = requests.post(
            f"{OPENAI_API_BASE}/responses",
            headers={**self._headers(), "Content-Type": "application/json"},
            data=json.dumps(payload),
            timeout=600
        )
        if r.status_code >= 300:
            raise RuntimeError(f"Responses API error: {r.status_code} {r.text}")
        return r.json()

    # -------------------- Bill extraction (Responses API) --------------------

    def _extract_bill_via_responses_api(self, file_path: str, categories: List[str]) -> Tuple[bool, str]:
        """
        Uploads the file and requests a JSON output conforming to our schema.
        Uses the Responses API `text.format` field.
        """
        # 1) Upload file once and reference by file_id
        file_id = self._upload_file(file_path, purpose="user_data")

        # 2) Build JSON schema for strict structured output
        # Some Responses API deployments require that when strict=true,
        # every property present must appear in `required`. We therefore
        # include all keys as required and allow nulls for soft/optional fields.
        if categories:
            category_prop: Dict[str, Any] = {"anyOf": [{"type": "null"}, {"type": "string", "enum": categories}]}
        else:
            category_prop = {"type": ["string", "null"]}

        item_properties: Dict[str, Any] = {
            "description": {"type": "string"},
            "quantity": {"type": ["number", "null"]},
            "unit_price": {"type": ["number", "null"]},
            "price": {"type": "number"},
            "category": category_prop
        }
        item_required = list(item_properties.keys())  # require all keys; null allowed where applicable

        top_properties: Dict[str, Any] = {
            "bill_number": {"type": ["string", "null"]},
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": item_properties,
                    "required": item_required
                }
            },
            "source_filename": {"type": "string"}
        }
        top_required = list(top_properties.keys())

        bill_schema: Dict[str, Any] = {
            "type": "object",
            "additionalProperties": False,
            "properties": top_properties,
            "required": top_required
        }

        # 3) Prompt
        prompt = self._load_prompt(categories)

        # 4) Build Responses API payload
        model = self.config.get_openai_model() or "gpt-4o-mini"
        payload: Dict[str, Any] = {
            "model": model,
            "input": [
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": prompt},
                        {"type": "input_file", "file_id": file_id}
                    ]
                }
            ],
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "bill_extraction",
                    "schema": bill_schema,
                    "strict": True
                }
            },
            "max_output_tokens": 8000
        }

        # 5) Call Responses API
        data = self._responses_post(payload)

        # 6) Extract the JSON text from the response
        json_text = data.get("output_text")
        if not json_text:
            try:
                json_text = data["output"][0]["content"][0]["text"]
            except Exception:
                return False, f"Unexpected API response format: {json.dumps(data)[:2000]}"

        # 7) Validate/normalize JSON and inject filename if missing
        try:
            obj = json.loads(json_text)
        except json.JSONDecodeError:
            json_text = self._coerce_to_json(json_text)
            obj = json.loads(json_text)

        obj.setdefault("source_filename", os.path.basename(file_path))
        return True, json.dumps(obj, ensure_ascii=False, indent=2)

    # -------------------- Prompt loader --------------------

    def _load_prompt(self, categories: List[str]) -> str:
        """
        Load a prompt template if available and inject categories; otherwise return a solid default prompt.
        The template should contain the literal default category list to be replaced.
        """
        prompt_file = os.path.join("prompts", "bill_extraction.txt")
        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                prompt_template = f.read()
            categories_json = json.dumps(categories, ensure_ascii=False)
            default_list_literal = '["groceries","utilities","transportation","entertainment","healthcare","personal care","education","miscellaneous"]'
            prompt = prompt_template.replace(default_list_literal, categories_json)
            return prompt
        except Exception as e:
            logger.warning(f"Could not load prompt file {prompt_file}: {e}")
            categories_json = json.dumps(categories, ensure_ascii=False)
            return (
                "You are an expert at reading bills/invoices/receipts (scanned or digital).\n\n"
                "TASK\n"
                "- Read the attached document and extract the purchased items.\n"
                "- Classify each item into one of the allowed categories.\n\n"
                f"ALLOWED CATEGORIES\n{categories_json}\n\n"
                "OUTPUT FORMAT (JSON ONLY)\n"
                "Return ONLY a single JSON object with this shape:\n"
                "{\n"
                '  "bill_number": string|null,\n'
                '  "items": [\n'
                "    {\n"
                '      "description": string,\n'
                '      "quantity": number|null,\n'
                '      "unit_price": number|null,\n'
                '      "price": number,\n'
                '      "category": string\n'
                "    }\n"
                "  ]\n"
                "}\n\n"
                "RULES\n"
                "1) Use ONLY the allowed categories; if unsure, choose the closest match.\n"
                "2) Use numbers (not strings) for quantity, unit_price, price; round to 2 decimals.\n"
                "3) If quantity and unit_price are shown but price is missing, compute price = quantity * unit_price.\n"
                "4) Ignore totals/taxes/shipping/fees unless they are clearly part of an item line.\n"
                "5) If no bill number is visible, set it to null.\n"
                "6) Output must be valid JSON (double quotes only), with no commentary or markdown.\n"
            )

    # -------------------- Local helpers --------------------

    def _coerce_to_json(self, text: str) -> str:
        """Trim non-JSON pre/postfix if the model wrapped the JSON."""
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return text[start:end+1]
        return text

    def _wrap_plain_text_as_bill(self, content: str, categories: List[str]) -> Dict[str, Any]:
        """Wraps .txt content into a minimal bill-like JSON for consistency."""
        category = categories[0] if categories else None
        return {
            "bill_number": None,
            "items": [
                {
                    "description": content[:2000],
                    "quantity": None,
                    "unit_price": None,
                    "price": 0.0,
                    "category": category
                }
            ],
            "source_filename": "text-file"
        }

    # -------------------- Legacy TXT extractor --------------------

    def _extract_from_txt(self, file_path: str) -> Tuple[bool, str]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return True, f.read().strip()
        except UnicodeDecodeError:
            with open(file_path, 'r', encoding='latin-1') as f:
                return True, f.read().strip()

    # -------------------- UI helper (unchanged) --------------------

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
