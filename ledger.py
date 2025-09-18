import tkinter as tk
from tkinter import ttk
from typing import List, Optional
from database import DatabaseManager
from models import Item
from widgets import AccountListWidget, ItemEntryWidget, ItemsDisplayWidget
from dialogs import EditItemDialog, ask_account_name, confirm_delete, show_warning, show_error

class LedgerApp:
    """Main ledger application class."""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Simple Ledger")
        self.root.geometry("1000x700")
        self.root.configure(bg='#f0f0f0')
        
        # Initialize database
        self.db = DatabaseManager()
        
        # Load data
        self.accounts = self.db.load_accounts()
        self.items = [Item.from_dict(item_dict) for item_dict in self.db.load_items()]
        
        # Initialize widgets
        self.account_widget = None
        self.item_entry_widget = None
        self.items_display_widget = None
        self.status_var = None
        
        # Create GUI
        self.create_widgets()
        self.refresh_displays()
    
    def create_widgets(self):
        """Create the main GUI widgets."""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Create widgets
        self.create_account_widget(main_frame)
        self.create_item_entry_widget(main_frame)
        self.create_items_display_widget(main_frame)
        self.create_status_bar(main_frame)
    
    def create_account_widget(self, parent: ttk.Frame):
        """Create the account management widget."""
        self.account_widget = AccountListWidget(
            parent=parent,
            accounts=self.accounts,
            on_add=self.add_account,
            on_rename=self.rename_account,
            on_delete=self.delete_account
        )
        
        account_frame = self.account_widget.create()
        account_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N), padx=(0, 5))
    
    def create_item_entry_widget(self, parent: ttk.Frame):
        """Create the item entry widget."""
        self.item_entry_widget = ItemEntryWidget(
            parent=parent,
            accounts=self.accounts,
            on_add=self.add_item
        )
        
        item_frame = self.item_entry_widget.create()
        item_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N), padx=(5, 0))
    
    def create_items_display_widget(self, parent: ttk.Frame):
        """Create the items display widget."""
        self.items_display_widget = ItemsDisplayWidget(
            parent=parent,
            accounts=self.accounts,
            on_edit=self.edit_item,
            on_delete=self.delete_item,
            on_filter_change=self.filter_items
        )
        
        display_frame = self.items_display_widget.create()
        display_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
    
    def create_status_bar(self, parent: ttk.Frame):
        """Create the status bar."""
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(parent, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))
    
    def add_account(self, name: str):
        """Add a new account."""
        if not name:
            show_warning("Warning", "Account name cannot be empty.")
            return
        
        if name in self.accounts:
            show_warning("Warning", "Account already exists.")
            return
        
        self.accounts.append(name)
        self.db.save_account(name)
        self.refresh_displays()
        self.status_var.set(f"Added account: {name}")
    
    def rename_account(self, old_name: str, _: str):
        """Rename an existing account."""
        new_name = ask_account_name("Rename Account", f"Enter new name for '{old_name}':", old_name)
        
        if not new_name or new_name == old_name:
            return
        
        if new_name in self.accounts:
            show_error("Error", "Account name already exists.")
            return
        
        # Update in memory
        idx = self.accounts.index(old_name)
        self.accounts[idx] = new_name
        
        # Update items
        for item in self.items:
            if item.account == old_name:
                item.account = new_name
        
        # Update database
        self.db.update_account_name(old_name, new_name)
        self.refresh_displays()
        self.status_var.set(f"Renamed account: {old_name} → {new_name}")
    
    def delete_account(self, account_name: str):
        """Delete an account and all its items."""
        # Check if account has items
        has_items = any(item.account == account_name for item in self.items)
        if has_items:
            if not confirm_delete("Confirm Delete", 
                                f"Account '{account_name}' has items. Delete account and all its items?"):
                return
        
        # Remove from memory
        self.accounts.remove(account_name)
        self.items = [item for item in self.items if item.account != account_name]
        
        # Remove from database
        self.db.remove_account(account_name)
        self.refresh_displays()
        self.status_var.set(f"Deleted account: {account_name}")
    
    def add_item(self, account: str, description: str, price: float):
        """Add a new item."""
        if not account:
            show_warning("Warning", "Please select an account.")
            return
        
        if not description:
            show_warning("Warning", "Description cannot be empty.")
            return
        
        # Save to database and get ID
        item_id = self.db.save_item(account, description, price)
        
        # Add to memory
        new_item = Item(id=item_id, account=account, description=description, price=price)
        self.items.append(new_item)
        
        # Clear form and refresh
        self.item_entry_widget.clear_form()
        self.refresh_items_display()
        self.status_var.set(f"Added item: {description}")
    
    def edit_item(self, dummy_item: Item):
        """Edit an existing item."""
        # Find the real item
        item = next((item for item in self.items if item.id == dummy_item.id), None)
        if not item:
            show_warning("Warning", "Please select an item to edit.")
            return
        
        def on_save(updated_item: Item):
            # Update in memory
            for i, existing_item in enumerate(self.items):
                if existing_item.id == updated_item.id:
                    self.items[i] = updated_item
                    break
            
            # Update database
            self.db.update_item(updated_item.id, updated_item.description, 
                              updated_item.price, updated_item.account)
            
            self.refresh_items_display()
            self.status_var.set(f"Updated item: {updated_item.description}")
        
        dialog = EditItemDialog(self.root, item, self.accounts, on_save)
        dialog.show()
    
    def delete_item(self, dummy_item: Item):
        """Delete an item."""
        # Find the real item
        item = next((item for item in self.items if item.id == dummy_item.id), None)
        if not item:
            show_warning("Warning", "Please select an item to delete.")
            return
        
        if confirm_delete("Confirm Delete", f"Delete item '{item.description}'?"):
            # Remove from memory
            self.items = [existing_item for existing_item in self.items if existing_item.id != item.id]
            
            # Remove from database
            self.db.remove_item(item.id)
            
            self.refresh_items_display()
            self.status_var.set(f"Deleted item: {item.description}")
    
    def filter_items(self, filter_account: str):
        """Filter items by account."""
        self.refresh_items_display()
    
    def refresh_displays(self):
        """Refresh all displays."""
        self.account_widget.refresh(self.accounts)
        self.item_entry_widget.refresh_accounts(self.accounts)
        self.items_display_widget.refresh_filter_options(self.accounts)
        self.refresh_items_display()
    
    def refresh_items_display(self):
        """Refresh the items display."""
        # Get filter value
        filter_account = self.items_display_widget.filter_var.get() if self.items_display_widget.filter_var else "All"
        
        # Filter items
        if filter_account == "All" or not filter_account:
            filtered_items = self.items
        else:
            filtered_items = [item for item in self.items if item.account == filter_account]
        
        # Display items and totals
        self.items_display_widget.display_items(filtered_items)
        self.items_display_widget.display_totals(self.items)  # Always show totals for all items

def main():
    """Main entry point."""
    root = tk.Tk()
    app = LedgerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()