import os
import sqlite3
from typing import List, Dict, Any

class DatabaseManager:
    def __init__(self, db_file: str = "ledger.db"):
        # Create data directory if it doesn't exist
        data_dir = os.path.join(os.path.dirname(__file__), "data")
        os.makedirs(data_dir, exist_ok=True)
        
        # Set database file path in data directory
        self.db_file = os.path.join(data_dir, db_file)
        self.init_database()
    
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
        """Load all accounts from the database."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM accounts ORDER BY name")
        accounts = [row[0] for row in cursor.fetchall()]
        conn.close()
        return accounts
    
    def load_items(self) -> List[Dict[str, Any]]:
        """Load all items from the database."""
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
        """Save a new account to the database."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO accounts (name) VALUES (?)", (name,))
            conn.commit()
        except sqlite3.IntegrityError:
            pass  # Account already exists
        conn.close()
    
    def remove_account(self, name: str):
        """Remove an account and all its items from the database."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM items WHERE account = ?", (name,))
        cursor.execute("DELETE FROM accounts WHERE name = ?", (name,))
        conn.commit()
        conn.close()
    
    def update_account_name(self, old_name: str, new_name: str):
        """Update an account name in the database."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("UPDATE accounts SET name = ? WHERE name = ?", (new_name, old_name))
        cursor.execute("UPDATE items SET account = ? WHERE account = ?", (new_name, old_name))
        conn.commit()
        conn.close()
    
    def save_item(self, account: str, description: str, price: float) -> int:
        """Save a new item to the database and return its ID."""
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
        """Remove an item from the database."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM items WHERE id = ?", (item_id,))
        conn.commit()
        conn.close()
    
    def update_item(self, item_id: int, description: str, price: float, account: str):
        """Update an item in the database."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE items SET description = ?, price = ?, account = ? WHERE id = ?",
            (description, price, account, item_id)
        )
        conn.commit()
        conn.close()