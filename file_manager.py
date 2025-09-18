import os
import shutil
from datetime import datetime
from typing import Optional
from tkinter import filedialog, messagebox
from text_extractor import TextExtractor, show_extracted_text_dialog
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FileManager:
    """Manages file operations for bill imports."""
    
    def __init__(self, base_data_dir: str = "data"):
        self.base_data_dir = base_data_dir
        self.text_extractor = TextExtractor()
        
    def get_date_directory(self, date: datetime = None) -> str:
        """Get the directory path for a specific date."""
        if date is None:
            date = datetime.now()
        
        date_str = date.strftime("%Y-%m-%d")
        return os.path.join(self.base_data_dir, date_str)
    
    def ensure_date_directory_exists(self, date: datetime = None) -> str:
        """Ensure the date directory exists and return its path."""
        date_dir = self.get_date_directory(date)
        os.makedirs(date_dir, exist_ok=True)
        return date_dir
    
    def import_file(self, source_path: str, date: datetime = None, parent_widget=None) -> Optional[str]:
        """
        Import a file to the appropriate date directory with text extraction.
        Returns the new file path if successful, None otherwise.
        """
        try:
            filename = os.path.basename(source_path)
            
            # Step 1: Extract text from the bill
            if self.text_extractor.can_extract(source_path):
                success, extracted_text = self.text_extractor.extract_text(source_path)
                
                if success and extracted_text:
                    # Step 2: Display popup with extracted text
                    # Step 3: Log the text in console
                    logger.info(f"=== EXTRACTED TEXT FROM {filename} ===")
                    logger.info(extracted_text)
                    logger.info(f"=== END OF EXTRACTED TEXT ===")
                    
                    # Show dialog and wait for user confirmation
                    if parent_widget:
                        user_confirmed = show_extracted_text_dialog(parent_widget, extracted_text, filename)
                        if not user_confirmed:
                            return None  # User cancelled
                    else:
                        # Fallback to simple messagebox if no parent widget
                        messagebox.showinfo("Bill Parsed", f"✅ Bill has been successfully parsed!\n\nExtracted text logged to console.")
                else:
                    # Text extraction failed, but continue with import
                    logger.warning(f"Failed to extract text from {filename}: {extracted_text}")
                    if parent_widget:
                        messagebox.showwarning("Text Extraction Failed", 
                                             f"Could not extract text from the bill:\n{extracted_text}\n\nFile will still be imported.")
            else:
                logger.info(f"File type not supported for text extraction: {filename}")
            
            # Step 4: Move the file to the directory (after user clicks OK)
            # Ensure the date directory exists
            date_dir = self.ensure_date_directory_exists(date)
            
            # Get the filename
            destination_path = os.path.join(date_dir, filename)
            
            # Handle duplicate filenames
            counter = 1
            base_name, extension = os.path.splitext(filename)
            while os.path.exists(destination_path):
                new_filename = f"{base_name}_{counter}{extension}"
                destination_path = os.path.join(date_dir, new_filename)
                counter += 1
            
            # Copy the file
            shutil.copy2(source_path, destination_path)
            return destination_path
            
        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to import file: {str(e)}")
            return None
    
    def select_and_import_file(self, date: datetime = None, parent_widget=None) -> Optional[str]:
        """
        Open file dialog to select and import a file with text extraction.
        Returns the new file path if successful, None otherwise.
        """
        # Define supported file types
        filetypes = [
            ("All supported", "*.pdf;*.jpg;*.jpeg;*.png;*.gif;*.bmp;*.tiff;*.txt;*.doc;*.docx"),
            ("PDF files", "*.pdf"),
            ("Image files", "*.jpg;*.jpeg;*.png;*.gif;*.bmp;*.tiff"),
            ("Document files", "*.txt;*.doc;*.docx"),
            ("All files", "*.*")
        ]
        
        # Open file dialog
        source_path = filedialog.askopenfilename(
            title="Select Bill/Document to Import",
            filetypes=filetypes
        )
        
        if not source_path:
            return None
        
        # Import the file
        destination_path = self.import_file(source_path, date, parent_widget)
        
        if destination_path:
            messagebox.showinfo(
                "Import Successful", 
                f"File imported successfully to:\n{destination_path}"
            )
        
        return destination_path
    
    def get_files_for_date(self, date: datetime = None) -> list:
        """Get all files for a specific date."""
        date_dir = self.get_date_directory(date)
        
        if not os.path.exists(date_dir):
            return []
        
        files = []
        for filename in os.listdir(date_dir):
            file_path = os.path.join(date_dir, filename)
            if os.path.isfile(file_path):
                files.append({
                    'name': filename,
                    'path': file_path,
                    'size': os.path.getsize(file_path),
                    'modified': datetime.fromtimestamp(os.path.getmtime(file_path))
                })
        
        return sorted(files, key=lambda x: x['modified'], reverse=True)