import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3
from typing import List, Dict, Any

class LedgerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Simple Ledger")
        self.root.geometry("1000x700")
        self.root.configure(bg='#f0f0f0')
        
        # Database setup
        self.db_file = "ledger.db"
        self.init_database()
        
        # Data storage
        self.accounts = self.load_accounts()
        self.items = self.load_items()
        
        # Create GUI
        self.create_widgets()
        self.refresh_displays()
    
    def init_database(self):
        """Initialize the SQLite database with required tables."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # Create accounts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )
        ''')
        
        # Create items table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account TEXT NOT NULL,
                description TEXT NOT NULL,
                price REAL NOT NULL,
                FOREIGN KEY (account) REFERENCES accounts (name) ON DELETE CASCADE
            )
        ''')
        
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.commit()
        conn.close()
    
    def load_accounts(self) -> List[str]:
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM accounts ORDER BY name")
        accounts = [row[0] for row in cursor.fetchall()]
        conn.close()
        return accounts
    
    def load_items(self) -> List[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT id, account, description, price FROM items ORDER BY id")
        items = []
        for row in cursor.fetchall():
            items.append({
                "id": row[0],
                "account": row[1],
                "description": row[2],
                "price": row[3]
            })
        conn.close()
        return items
    
    def save_account(self, name: str):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO accounts (name) VALUES (?)", (name,))
            conn.commit()
        except sqlite3.IntegrityError:
            pass  # Account already exists
        conn.close()
    
    def remove_account(self, name: str):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM items WHERE account = ?", (name,))
        cursor.execute("DELETE FROM accounts WHERE name = ?", (name,))
        conn.commit()
        conn.close()
    
    def update_account_name(self, old_name: str, new_name: str):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("UPDATE accounts SET name = ? WHERE name = ?", (new_name, old_name))
        cursor.execute("UPDATE items SET account = ? WHERE account = ?", (new_name, old_name))
        conn.commit()
        conn.close()
    
    def save_item(self, account: str, description: str, price: float) -> int:
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO items (account, description, price) VALUES (?, ?, ?)",
            (account, description, price)
        )
        item_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return item_id
    
    def remove_item(self, item_id: int):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM items WHERE id = ?", (item_id,))
        conn.commit()
        conn.close()
    
    def update_item(self, item_id: int, description: str, price: float, account: str):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE items SET description = ?, price = ?, account = ? WHERE id = ?",
            (description, price, account, item_id)
        )
        conn.commit()
        conn.close()
    
    def create_widgets(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Left panel - Account management
        self.create_account_panel(main_frame)
        
        # Right panel - Item management
        self.create_item_panel(main_frame)
        
        # Bottom panel - Items display
        self.create_items_display(main_frame)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))
    
    def create_account_panel(self, parent):
        # Account management frame
        account_frame = ttk.LabelFrame(parent, text="Account Management", padding="10")
        account_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N), padx=(0, 5))
        
        # Add account
        ttk.Label(account_frame, text="New Account:").grid(row=0, column=0, sticky=tk.W)
        self.new_account_var = tk.StringVar()
        account_entry = ttk.Entry(account_frame, textvariable=self.new_account_var, width=20)
        account_entry.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        account_entry.bind('<Return>', lambda e: self.add_account())
        
        ttk.Button(account_frame, text="Add Account", command=self.add_account).grid(row=2, column=0, sticky=(tk.W, tk.E))
        
        # Account list
        ttk.Label(account_frame, text="Existing Accounts:").grid(row=3, column=0, sticky=tk.W, pady=(10, 0))
        
        # Account listbox with scrollbar
        list_frame = ttk.Frame(account_frame)
        list_frame.grid(row=4, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(5, 0))
        
        self.account_listbox = tk.Listbox(list_frame, height=8)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.account_listbox.yview)
        self.account_listbox.configure(yscrollcommand=scrollbar.set)
        
        self.account_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # Account action buttons
        btn_frame = ttk.Frame(account_frame)
        btn_frame.grid(row=5, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        
        ttk.Button(btn_frame, text="Rename", command=self.rename_account).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(btn_frame, text="Delete", command=self.delete_account).grid(row=0, column=1)
        
        account_frame.columnconfigure(0, weight=1)
        account_frame.rowconfigure(4, weight=1)
    
    def create_item_panel(self, parent):
        # Item management frame
        item_frame = ttk.LabelFrame(parent, text="Add Item", padding="10")
        item_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N), padx=(5, 0))
        
        # Account selection
        ttk.Label(item_frame, text="Account:").grid(row=0, column=0, sticky=tk.W)
        self.selected_account_var = tk.StringVar()
        self.account_combo = ttk.Combobox(item_frame, textvariable=self.selected_account_var, state="readonly")
        self.account_combo.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # Description
        ttk.Label(item_frame, text="Description:").grid(row=2, column=0, sticky=tk.W)
        self.description_var = tk.StringVar()
        desc_entry = ttk.Entry(item_frame, textvariable=self.description_var)
        desc_entry.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        desc_entry.bind('<Return>', lambda e: self.add_item())
        
        # Price
        ttk.Label(item_frame, text="Price:").grid(row=4, column=0, sticky=tk.W)
        self.price_var = tk.StringVar()
        price_entry = ttk.Entry(item_frame, textvariable=self.price_var)
        price_entry.grid(row=5, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        price_entry.bind('<Return>', lambda e: self.add_item())
        
        # Add button
        ttk.Button(item_frame, text="Add Item", command=self.add_item).grid(row=6, column=0, sticky=(tk.W, tk.E))
        
        item_frame.columnconfigure(0, weight=1)
    
    def create_items_display(self, parent):
        # Items display frame
        display_frame = ttk.LabelFrame(parent, text="Items", padding="10")
        display_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        
        # Filter frame
        filter_frame = ttk.Frame(display_frame)
        filter_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(filter_frame, text="Filter by Account:").grid(row=0, column=0, padx=(0, 5))
        self.filter_var = tk.StringVar()
        self.filter_combo = ttk.Combobox(filter_frame, textvariable=self.filter_var, state="readonly")
        self.filter_combo.grid(row=0, column=1, padx=(0, 10))
        self.filter_combo.bind('<<ComboboxSelected>>', lambda e: self.refresh_items_display())
        
        # Totals button
        self.show_totals_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(filter_frame, text="Show Totals", variable=self.show_totals_var, 
                       command=self.refresh_totals).grid(row=0, column=2)
        
        # Items treeview
        tree_frame = ttk.Frame(display_frame)
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
        
        # Scrollbars for treeview
        v_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.items_tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.items_tree.xview)
        self.items_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        self.items_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        h_scrollbar.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)
        
        # Item action buttons
        item_btn_frame = ttk.Frame(display_frame)
        item_btn_frame.grid(row=2, column=0, pady=(10, 0))
        
        ttk.Button(item_btn_frame, text="Edit Item", command=self.edit_item).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(item_btn_frame, text="Delete Item", command=self.delete_item).grid(row=0, column=1)
        
        # Totals frame
        self.totals_frame = ttk.LabelFrame(display_frame, text="Totals", padding="10")
        self.totals_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        display_frame.columnconfigure(0, weight=1)
        display_frame.rowconfigure(1, weight=1)
    
    def add_account(self):
        name = self.new_account_var.get().strip()
        if not name:
            messagebox.showwarning("Warning", "Account name cannot be empty.")
            return
        
        if name in self.accounts:
            messagebox.showwarning("Warning", "Account already exists.")
            return
        
        self.accounts.append(name)
        self.save_account(name)
        self.new_account_var.set("")
        self.refresh_displays()
        self.status_var.set(f"Added account: {name}")
    
    def rename_account(self):
        selection = self.account_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an account to rename.")
            return
        
        old_name = self.accounts[selection[0]]
        new_name = simpledialog.askstring("Rename Account", f"Enter new name for '{old_name}':")
        
        if not new_name or new_name.strip() == "":
            return
        
        new_name = new_name.strip()
        if new_name == old_name:
            return
        
        if new_name in self.accounts:
            messagebox.showerror("Error", "Account name already exists.")
            return
        
        # Update in memory
        idx = self.accounts.index(old_name)
        self.accounts[idx] = new_name
        
        # Update items
        for item in self.items:
            if item["account"] == old_name:
                item["account"] = new_name
        
        # Update database
        self.update_account_name(old_name, new_name)
        self.refresh_displays()
        self.status_var.set(f"Renamed account: {old_name} → {new_name}")
    
    def delete_account(self):
        selection = self.account_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an account to delete.")
            return
        
        account_name = self.accounts[selection[0]]
        
        # Check if account has items
        has_items = any(item["account"] == account_name for item in self.items)
        if has_items:
            if not messagebox.askyesno("Confirm Delete", 
                                     f"Account '{account_name}' has items. Delete account and all its items?"):
                return
        
        # Remove from memory
        self.accounts.remove(account_name)
        self.items = [item for item in self.items if item["account"] != account_name]
        
        # Remove from database
        self.remove_account(account_name)
        self.refresh_displays()
        self.status_var.set(f"Deleted account: {account_name}")
    
    def add_item(self):
        account = self.selected_account_var.get()
        description = self.description_var.get().strip()
        price_str = self.price_var.get().strip()
        
        if not account:
            messagebox.showwarning("Warning", "Please select an account.")
            return
        
        if not description:
            messagebox.showwarning("Warning", "Description cannot be empty.")
            return
        
        try:
            price = float(price_str)
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid price.")
            return
        
        # Save to database and get ID
        item_id = self.save_item(account, description, price)
        
        # Add to memory
        self.items.append({
            "id": item_id,
            "account": account,
            "description": description,
            "price": price
        })
        
        # Clear form
        self.description_var.set("")
        self.price_var.set("")
        
        self.refresh_items_display()
        self.refresh_totals()
        self.status_var.set(f"Added item: {description}")
    
    def edit_item(self):
        selection = self.items_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an item to edit.")
            return
        
        item_id = int(self.items_tree.item(selection[0])['values'][0])
        item = next((item for item in self.items if item["id"] == item_id), None)
        
        if not item:
            return
        
        # Create edit dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Item")
        dialog.geometry("400x200")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog
        dialog.geometry("+%d+%d" % (self.root.winfo_rootx() + 50, self.root.winfo_rooty() + 50))
        
        # Form fields
        ttk.Label(dialog, text="Account:").grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        account_var = tk.StringVar(value=item["account"])
        account_combo = ttk.Combobox(dialog, textvariable=account_var, values=self.accounts, state="readonly")
        account_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=10, pady=5)
        
        ttk.Label(dialog, text="Description:").grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        desc_var = tk.StringVar(value=item["description"])
        desc_entry = ttk.Entry(dialog, textvariable=desc_var)
        desc_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=10, pady=5)
        
        ttk.Label(dialog, text="Price:").grid(row=2, column=0, sticky=tk.W, padx=10, pady=5)
        price_var = tk.StringVar(value=str(item["price"]))
        price_entry = ttk.Entry(dialog, textvariable=price_var)
        price_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=10, pady=5)
        
        def save_changes():
            new_account = account_var.get()
            new_description = desc_var.get().strip()
            new_price_str = price_var.get().strip()
            
            if not new_account or not new_description:
                messagebox.showwarning("Warning", "All fields are required.")
                return
            
            try:
                new_price = float(new_price_str)
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid price.")
                return
            
            # Update in memory
            item["account"] = new_account
            item["description"] = new_description
            item["price"] = new_price
            
            # Update database
            self.update_item(item_id, new_description, new_price, new_account)
            
            dialog.destroy()
            self.refresh_items_display()
            self.refresh_totals()
            self.status_var.set(f"Updated item: {new_description}")
        
        # Buttons
        btn_frame = ttk.Frame(dialog)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=20)
        
        ttk.Button(btn_frame, text="Save", command=save_changes).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=dialog.destroy).grid(row=0, column=1, padx=5)
        
        dialog.columnconfigure(1, weight=1)
        desc_entry.focus()
    
    def delete_item(self):
        selection = self.items_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an item to delete.")
            return
        
        item_id = int(self.items_tree.item(selection[0])['values'][0])
        item = next((item for item in self.items if item["id"] == item_id), None)
        
        if not item:
            return
        
        if messagebox.askyesno("Confirm Delete", f"Delete item '{item['description']}'?"):
            # Remove from memory
            self.items = [item for item in self.items if item["id"] != item_id]
            
            # Remove from database
            self.remove_item(item_id)
            
            self.refresh_items_display()
            self.refresh_totals()
            self.status_var.set(f"Deleted item: {item['description']}")
    
    def refresh_displays(self):
        self.refresh_account_list()
        self.refresh_combos()
        self.refresh_items_display()
        self.refresh_totals()
    
    def refresh_account_list(self):
        self.account_listbox.delete(0, tk.END)
        for account in sorted(self.accounts):
            self.account_listbox.insert(tk.END, account)
    
    def refresh_combos(self):
        # Update account combo for adding items
        self.account_combo['values'] = sorted(self.accounts)
        
        # Update filter combo
        filter_options = ["All"] + sorted(self.accounts)
        self.filter_combo['values'] = filter_options
        if not self.filter_var.get():
            self.filter_var.set("All")
    
    def refresh_items_display(self):
        # Clear existing items
        for item in self.items_tree.get_children():
            self.items_tree.delete(item)
        
        # Filter items
        filter_account = self.filter_var.get()
        if filter_account == "All" or not filter_account:
            filtered_items = self.items
        else:
            filtered_items = [item for item in self.items if item["account"] == filter_account]
        
        # Add items to tree
        for item in filtered_items:
            price_str = f"${item['price']:,.2f}"
            self.items_tree.insert('', tk.END, values=(
                item['id'], item['account'], item['description'], price_str
            ))
    
    def refresh_totals(self):
        # Clear existing totals
        for widget in self.totals_frame.winfo_children():
            widget.destroy()
        
        if not self.show_totals_var.get() or not self.items:
            return
        
        # Calculate totals by account
        totals_by_account = {}
        for item in self.items:
            account = item["account"]
            totals_by_account[account] = totals_by_account.get(account, 0) + item["price"]
        
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
            grand_label = ttk.Label(self.totals_frame, text=f"Grand Total: ${grand_total:,.2f}", 
                                  font=('TkDefaultFont', 10, 'bold'))
            grand_label.grid(row=row+1, column=0, columnspan=3, pady=(10, 0))

def main():
    root = tk.Tk()
    app = LedgerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()