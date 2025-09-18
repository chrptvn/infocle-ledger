import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from typing import List, Optional, Callable
from models import Item
from file_manager import FileManager
import os

class EditItemDialog:
    """Dialog for editing an existing item."""
    
    def __init__(self, parent: tk.Widget, item: Item, accounts: List[str], 
                 on_save: Callable[[Item], None]):
        self.parent = parent
        self.item = item
        self.accounts = accounts
        self.on_save = on_save
        self.dialog = None
        self.file_manager = FileManager()
        
    def show(self):
        """Display the edit dialog."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Edit Item")
        self.dialog.geometry("400x200")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.geometry("+%d+%d" % (
            self.parent.winfo_rootx() + 50, 
            self.parent.winfo_rooty() + 50
        ))
        
        self._create_form()
        
    def _create_form(self):
        """Create the form elements."""
        # Account selection
        ttk.Label(self.dialog, text="Account:").grid(
            row=0, column=0, sticky=tk.W, padx=10, pady=5
        )
        self.account_var = tk.StringVar(value=self.item.account)
        account_combo = ttk.Combobox(
            self.dialog, textvariable=self.account_var, 
            values=self.accounts, state="readonly"
        )
        account_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=10, pady=5)
        
        # Description
        ttk.Label(self.dialog, text="Description:").grid(
            row=1, column=0, sticky=tk.W, padx=10, pady=5
        )
        self.desc_var = tk.StringVar(value=self.item.description)
        desc_entry = ttk.Entry(self.dialog, textvariable=self.desc_var)
        desc_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=10, pady=5)
        
        # Price
        ttk.Label(self.dialog, text="Price:").grid(
            row=2, column=0, sticky=tk.W, padx=10, pady=5
        )
        self.price_var = tk.StringVar(value=str(self.item.price))
        price_entry = ttk.Entry(self.dialog, textvariable=self.price_var)
        price_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=10, pady=5)
        
        # Buttons
        btn_frame = ttk.Frame(self.dialog)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=20)
        
        ttk.Button(btn_frame, text="Save", command=self._save_changes).grid(
            row=0, column=0, padx=5
        )
        ttk.Button(btn_frame, text="Cancel", command=self.dialog.destroy).grid(
            row=0, column=1, padx=5
        )
        ttk.Button(btn_frame, text="Import Bill", command=self._import_bill).grid(
            row=0, column=2, padx=5
        )
        
        self.dialog.columnconfigure(1, weight=1)
        desc_entry.focus()
    
    def _save_changes(self):
        """Validate and save the changes."""
        new_account = self.account_var.get()
        new_description = self.desc_var.get().strip()
        new_price_str = self.price_var.get().strip()
        
        if not new_account or not new_description:
            messagebox.showwarning("Warning", "All fields are required.")
            return
        
        try:
            new_price = float(new_price_str)
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid price.")
            return
        
        # Update the item
        updated_item = Item(
            id=self.item.id,
            account=new_account,
            description=new_description,
            price=new_price
        )
        
        self.on_save(updated_item)
        self.dialog.destroy()
    
    def _import_bill(self):
        """Import a bill file for this item."""
        imported_path = self.file_manager.select_and_import_file(parent_widget=self.dialog)
        if imported_path:
            # Update the description to include reference to the imported file
            filename = os.path.basename(imported_path)
            current_desc = self.desc_var.get().strip()
            if current_desc and not filename in current_desc:
                self.desc_var.set(f"{current_desc} (Bill: {filename})")
            elif not current_desc:
                self.desc_var.set(f"Bill: {filename}")

def ask_account_name(title: str, prompt: str, initial_value: str = "") -> Optional[str]:
    """Ask for an account name using a simple dialog."""
    name = simpledialog.askstring(title, prompt, initialvalue=initial_value)
    if name:
        return name.strip()
    return None

def confirm_delete(title: str, message: str) -> bool:
    """Show a confirmation dialog for delete operations."""
    return messagebox.askyesno(title, message)

def show_warning(title: str, message: str):
    """Show a warning message."""
    messagebox.showwarning(title, message)

def show_error(title: str, message: str):
    """Show an error message."""
    messagebox.showerror(title, message)