import os
import shutil
from datetime import datetime
from typing import Optional
from tkinter import filedialog, messagebox

class FileManager:
    """Manages file operations for bill imports."""
    
    def __init__(self, base_data_dir: str = "data"):
        self.base_data_dir = base_data_dir
        
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
    
    def import_file(self, source_path: str, date: datetime = None) -> Optional[str]:
        """
        Import a file to the appropriate date directory.
        Returns the new file path if successful, None otherwise.
        """
        try:
            # Ensure the date directory exists
            date_dir = self.ensure_date_directory_exists(date)
            
            # Get the filename
            filename = os.path.basename(source_path)
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
    
    def select_and_import_file(self, date: datetime = None) -> Optional[str]:
        """
        Open file dialog to select and import a file.
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
        destination_path = self.import_file(source_path, date)
        
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