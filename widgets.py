import tkinter as tk
from tkinter import ttk
from typing import List, Callable, Optional
from models import Item
from file_manager import FileManager
from datetime import datetime
from file_manager import FileManager
from datetime import datetime

class AccountListWidget:
    """Widget for managing the list of accounts."""
    
    def __init__(self, parent: tk.Widget, accounts: List[str],
                 on_add: Callable[[str], None],
                 on_rename: Callable[[str, str], None],
                 on_delete: Callable[[str], None]):
        self.parent = parent
        self.accounts = accounts
        self.on_add = on_add
        self.on_rename = on_rename
        self.on_delete = on_delete
        
        self.frame = None
        self.new_account_var = None
        self.account_listbox = None
        
    def create(self) -> ttk.Frame:
        """Create and return the account management frame."""
        self.frame = ttk.LabelFrame(self.parent, text="Account Management", padding="10")
        
        # Add account section
        ttk.Label(self.frame, text="New Account:").grid(row=0, column=0, sticky=tk.W)
        self.new_account_var = tk.StringVar()
        account_entry = ttk.Entry(self.frame, textvariable=self.new_account_var, width=20)
        account_entry.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        account_entry.bind('<Return>', lambda e: self._add_account())
        
        ttk.Button(self.frame, text="Add Account", command=self._add_account).grid(
            row=2, column=0, sticky=(tk.W, tk.E)
        )
        
        # Account list section
        ttk.Label(self.frame, text="Existing Accounts:").grid(
            row=3, column=0, sticky=tk.W, pady=(10, 0)
        )
        
        # Account listbox with scrollbar
        list_frame = ttk.Frame(self.frame)
        list_frame.grid(row=4, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(5, 0))
        
        self.account_listbox = tk.Listbox(list_frame, height=8)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.account_listbox.yview)
        self.account_listbox.configure(yscrollcommand=scrollbar.set)
        
        self.account_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # Action buttons
        btn_frame = ttk.Frame(self.frame)
        btn_frame.grid(row=5, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        
        ttk.Button(btn_frame, text="Rename", command=self._rename_account).grid(
            row=0, column=0, padx=(0, 5)
        )
        ttk.Button(btn_frame, text="Delete", command=self._delete_account).grid(
            row=0, column=1
        )
        
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(4, weight=1)
        
        return self.frame
    
    def refresh(self, accounts: List[str]):
        """Refresh the account list."""
        self.accounts = accounts
        self.account_listbox.delete(0, tk.END)
        for account in sorted(accounts):
            self.account_listbox.insert(tk.END, account)
    
    def _add_account(self):
        """Handle adding a new account."""
        name = self.new_account_var.get().strip()
        if name:
            self.on_add(name)
            self.new_account_var.set("")
    
    def _rename_account(self):
        """Handle renaming an account."""
        selection = self.account_listbox.curselection()
        if selection:
            old_name = self.accounts[selection[0]]
            self.on_rename(old_name, "")  # The callback will handle the dialog
    
    def _delete_account(self):
        """Handle deleting an account."""
        selection = self.account_listbox.curselection()
        if selection:
            account_name = self.accounts[selection[0]]
            self.on_delete(account_name)

class ItemEntryWidget:
    """Widget for entering new items."""
    
    def __init__(self, parent: tk.Widget, accounts: List[str],
                 on_add: Callable[[str, str, float], None]):
        self.parent = parent
        self.accounts = accounts
        self.on_add = on_add
        
        self.frame = None
        self.selected_account_var = None
        self.description_var = None
        self.price_var = None
        self.account_combo = None
        
        # File manager for importing bills
        self.file_manager = FileManager()
        
    def create(self) -> ttk.Frame:
        """Create and return the item entry frame."""
        self.frame = ttk.LabelFrame(self.parent, text="Add Item", padding="10")
        
        # Account selection
        ttk.Label(self.frame, text="Account:").grid(row=0, column=0, sticky=tk.W)
        self.selected_account_var = tk.StringVar()
        self.account_combo = ttk.Combobox(
            self.frame, textvariable=self.selected_account_var, state="readonly"
        )
        self.account_combo.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # Description
        ttk.Label(self.frame, text="Description:").grid(row=2, column=0, sticky=tk.W)
        self.description_var = tk.StringVar()
        desc_entry = ttk.Entry(self.frame, textvariable=self.description_var)
        desc_entry.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        desc_entry.bind('<Return>', lambda e: self._add_item())
        
        # Price
        ttk.Label(self.frame, text="Price:").grid(row=4, column=0, sticky=tk.W)
        self.price_var = tk.StringVar()
        price_entry = ttk.Entry(self.frame, textvariable=self.price_var)
        price_entry.grid(row=5, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        price_entry.bind('<Return>', lambda e: self._add_item())
        
        # Buttons frame
        btn_frame = ttk.Frame(self.frame)
        btn_frame.grid(row=6, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        
        ttk.Button(btn_frame, text="Add Item", command=self._add_item).grid(
            row=0, column=0, sticky=(tk.W, tk.E)
        )
        
        self.frame.columnconfigure(0, weight=1)
        
        return self.frame
    
    def refresh_accounts(self, accounts: List[str]):
        """Refresh the account list in the combo box."""
        self.accounts = accounts
        self.account_combo['values'] = sorted(accounts)
    
    def clear_form(self):
        """Clear the form fields."""
        self.description_var.set("")
        self.price_var.set("")
    
    def _add_item(self):
        """Handle adding a new item."""
        account = self.selected_account_var.get()
        description = self.description_var.get().strip()
        price_str = self.price_var.get().strip()
        
        if not account or not description or not price_str:
            return
        
        try:
            price = float(price_str)
            self.on_add(account, description, price)
        except ValueError:
            pass  # Invalid price, ignore

class ItemsDisplayWidget:
    """Widget for displaying and managing items."""
    
    def __init__(self, parent: tk.Widget, accounts: List[str],
                 on_edit: Callable[[Item], None],
                 on_delete: Callable[[Item], None],
                 on_filter_change: Callable[[str], None]):
        self.parent = parent
        self.accounts = accounts
        self.on_edit = on_edit
        self.on_delete = on_delete
        self.on_filter_change = on_filter_change
        
        self.frame = None
        self.filter_var = None
        self.filter_combo = None
        self.items_tree = None
        self.show_totals_var = None
        self.totals_frame = None
        
        # File manager for importing bills
        self.file_manager = FileManager()
        
    def create(self) -> ttk.Frame:
        """Create and return the items display frame."""
        self.frame = ttk.LabelFrame(self.parent, text="Items", padding="10")
        
        # Filter frame
        filter_frame = ttk.Frame(self.frame)
        filter_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(filter_frame, text="Filter by Account:").grid(row=0, column=0, padx=(0, 5))
        self.filter_var = tk.StringVar()
        self.filter_combo = ttk.Combobox(filter_frame, textvariable=self.filter_var, state="readonly")
        self.filter_combo.grid(row=0, column=1, padx=(0, 10))
        self.filter_combo.bind('<<ComboboxSelected>>', self._on_filter_change)
        
        # Show totals checkbox
        self.show_totals_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(filter_frame, text="Show Totals", variable=self.show_totals_var).grid(
            row=0, column=2
        )
        
        # Items treeview
        tree_frame = ttk.Frame(self.frame)
        tree_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        columns = ('ID', 'Account', 'Description', 'Price')
        self.items_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=15)
        
        # Configure columns
        self.items_tree.heading('ID', text='ID')
        self.items_tree.heading('Account', text='Account')
        self.items_tree.heading('Description', text='Description')
        self.items_tree.heading('Price', text='Price')
        
        self.items_tree.column('ID', width=50, anchor=tk.CENTER)
        self.items_tree.column('Account', width=120)
        self.items_tree.column('Description', width=300)
        self.items_tree.column('Price', width=100, anchor=tk.E)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.items_tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.items_tree.xview)
        self.items_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        self.items_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)
        
        # Action buttons
        btn_frame = ttk.Frame(self.frame)
        btn_frame.grid(row=2, column=0, pady=(10, 0))
        
        ttk.Button(btn_frame, text="Edit Item", command=self._edit_item).grid(
            row=0, column=0, padx=(0, 5)
        )
        ttk.Button(btn_frame, text="Delete Item", command=self._delete_item).grid(
            row=0, column=1
        )
        ttk.Button(btn_frame, text="Import Bill", command=self._import_bill).grid(
            row=0, column=2, padx=(5, 0)
        )
        
        # Totals frame
        self.totals_frame = ttk.LabelFrame(self.frame, text="Totals", padding="10")
        self.totals_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(1, weight=1)
        
        return self.frame
    
    def refresh_filter_options(self, accounts: List[str]):
        """Refresh the filter combo box options."""
        filter_options = ["All"] + sorted(accounts)
        self.filter_combo['values'] = filter_options
        if not self.filter_var.get():
            self.filter_var.set("All")
    
    def display_items(self, items: List[Item]):
        """Display items in the treeview."""
        # Clear existing items
        for item in self.items_tree.get_children():
            self.items_tree.delete(item)
        
        # Add items to tree
        for item in items:
            self.items_tree.insert('', tk.END, values=(
                item.id, item.account, item.description, item.formatted_price()
            ))
    
    def display_totals(self, items: List[Item]):
        """Display totals by account."""
        # Clear existing totals
        for widget in self.totals_frame.winfo_children():
            widget.destroy()
        
        if not self.show_totals_var.get() or not items:
            return
        
        # Calculate totals by account
        totals_by_account = {}
        for item in items:
            account = item.account
            totals_by_account[account] = totals_by_account.get(account, 0) + item.price
        
        # Display totals
        row = 0
        col = 0
        for account, total in sorted(totals_by_account.items()):
            label = ttk.Label(self.totals_frame, text=f"{account}: ${total:,.2f}")
            label.grid(row=row, column=col, padx=10, pady=2, sticky=tk.W)
            
            col += 1
            if col >= 3:  # 3 columns
                col = 0
                row += 1
        
        # Grand total
        grand_total = sum(totals_by_account.values())
        if totals_by_account:
            grand_label = ttk.Label(
                self.totals_frame, 
                text=f"Grand Total: ${grand_total:,.2f}", 
                font=('TkDefaultFont', 10, 'bold')
            )
            grand_label.grid(row=row+1, column=0, columnspan=3, pady=(10, 0))
    
    def get_selected_item_id(self) -> Optional[int]:
        """Get the ID of the currently selected item."""
        selection = self.items_tree.selection()
        if selection:
            return int(self.items_tree.item(selection[0])['values'][0])
        return None
    
    def _on_filter_change(self, event=None):
        """Handle filter change."""
        self.on_filter_change(self.filter_var.get())
    
    def _edit_item(self):
        """Handle edit item button click."""
        item_id = self.get_selected_item_id()
        if item_id:
            # Create a dummy item - the main app will provide the real one
            dummy_item = Item(id=item_id, account="", description="", price=0.0)
            self.on_edit(dummy_item)
    
    def _delete_item(self):
        """Handle delete item button click."""
        item_id = self.get_selected_item_id()
        if item_id:
            # Create a dummy item - the main app will provide the real one
            dummy_item = Item(id=item_id, account="", description="", price=0.0)
            self.on_delete(dummy_item)
    
    def _import_bill(self):
        """Handle import bill button click."""
        imported_path = self.file_manager.select_and_import_file()
        if imported_path:
            # Optionally, you could add logic here to create an item entry
            # based on the imported file
            pass