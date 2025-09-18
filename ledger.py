
import streamlit as st
import sqlite3
import os
from typing import List, Dict, Any
from itertools import count

st.set_page_config(page_title="Simple Ledger", layout="wide")

# Database setup
DB_FILE = "ledger.db"

def init_database():
    """Initialize the SQLite database with required tables."""
    conn = sqlite3.connect(DB_FILE)
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
            FOREIGN KEY (account) REFERENCES accounts (name)
        )
    ''')
    
    conn.commit()
    conn.close()

def load_accounts() -> List[str]:
    """Load accounts from database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM accounts ORDER BY name")
    accounts = [row[0] for row in cursor.fetchall()]
    conn.close()
    return accounts

def load_items() -> List[Dict[str, Any]]:
    """Load items from database."""
    conn = sqlite3.connect(DB_FILE)
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

def save_account(name: str):
    """Save account to database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO accounts (name) VALUES (?)", (name,))
        conn.commit()
    except sqlite3.IntegrityError:
        pass  # Account already exists
    conn.close()

def remove_account(name: str):
    """Remove account and its items from database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM items WHERE account = ?", (name,))
    cursor.execute("DELETE FROM accounts WHERE name = ?", (name,))
    conn.commit()
    conn.close()

def update_account_name(old_name: str, new_name: str):
    """Update account name in database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE accounts SET name = ? WHERE name = ?", (new_name, old_name))
    cursor.execute("UPDATE items SET account = ? WHERE account = ?", (new_name, old_name))
    conn.commit()
    conn.close()

def save_item(account: str, description: str, price: float) -> int:
    """Save item to database and return its ID."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO items (account, description, price) VALUES (?, ?, ?)", 
                   (account, description, price))
    item_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return item_id

def remove_item(item_id: int):
    """Remove item from database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM items WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()

def update_item(item_id: int, description: str, price: float, account: str):
    """Update item in database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE items SET description = ?, price = ?, account = ? WHERE id = ?", 
                   (description, price, account, item_id))
    conn.commit()
    conn.close()

# Initialize database
init_database()

# Initialize session state
if "accounts" not in st.session_state:
    st.session_state.accounts: List[str] = load_accounts()
if "items" not in st.session_state:
    st.session_state.items: List[Dict[str, Any]] = load_items()

def add_account(name: str):
    name = name.strip()
    if name and name not in st.session_state.accounts:
        st.session_state.accounts.append(name)
        save_account(name)

def delete_account(name: str):
    # Remove account and any items belonging to it
    st.session_state.accounts = [c for c in st.session_state.accounts if c != name]
    st.session_state.items = [it for it in st.session_state.items if it["account"] != name]
    remove_account(name)

def rename_account(old: str, new: str):
    new = new.strip()
    if not new or (new != old and new in st.session_state.accounts):
        return
    idx = st.session_state.accounts.index(old)
    st.session_state.accounts[idx] = new
    for it in st.session_state.items:
        if it["account"] == old:
            it["account"] = new
    update_account_name(old, new)

def add_item(account: str, description: str, price: float):
    if not account or account not in st.session_state.accounts:
        st.warning("Select or create an account first.")
        return
    description = description.strip()
    if not description:
        st.warning("Description cannot be empty.")
        return
    item_id = save_item(account, description, price)
    st.session_state.items.append({
        "id": item_id,
        "account": account,
        "description": description,
        "price": float(price),
    })

def delete_item(item_id: int):
    st.session_state.items = [it for it in st.session_state.items if it["id"] != item_id]
    remove_item(item_id)

def edit_item(item_id: int, new_desc: str, new_price: float, new_acc: str):
    for it in st.session_state.items:
        if it["id"] == item_id:
            it["description"] = new_desc.strip()
            it["price"] = float(new_price)
            it["account"] = new_acc
            break
    update_item(item_id, new_desc.strip(), new_price, new_acc)

def currency(v: float) -> str:
    return f"$ {v:,.2f}"

st.title("Simple Ledger")

# Sidebar: Account management
st.sidebar.header("Accounts")

with st.sidebar.expander("Add account", expanded=True):
    new_acc = st.text_input("Name", key="new_acc_input")
    if st.button("Add", use_container_width=True):
        add_account(new_acc)
        st.session_state.new_acc_input = ""

if st.session_state.accounts:
    st.sidebar.write("Existing accounts")
    for acc in st.session_state.accounts:
        cols = st.sidebar.columns([1, 1, 1.2, 1])
        cols[0].markdown(f"**{acc}**")

        with cols[1]:
            if st.button("Rename", key=f"rename_{acc}"):
                st.session_state[f"renaming_{acc}"] = True
        with cols[3]:
            if st.button("Delete", key=f"del_{acc}"):
                delete_account(acc)
                st.experimental_rerun()
        if st.session_state.get(f"renaming_{acc}"):
            new_name = st.text_input(f"New name for '{acc}'", key=f"new_name_{acc}")
            cols2 = st.sidebar.columns([1,1])
            with cols2[0]:
                if st.button("Save", key=f"save_{acc}"):
                    rename_account(acc, new_name)
                    st.session_state[f"renaming_{acc}"] = False
                    st.experimental_rerun()
            with cols2[1]:
                if st.button("Cancel", key=f"cancel_{acc}"):
                    st.session_state[f"renaming_{acc}"] = False

# Main area
st.subheader("Add item")
col_acc, col_desc, col_price, col_add = st.columns([1.2, 3, 1, 1])
with col_acc:
    acc_choice = st.selectbox("Account", options=[""] + st.session_state.accounts, index=0, help="Choose an account")
with col_desc:
    desc = st.text_input("Description")
with col_price:
    price = st.number_input("Price", min_value=0.0, step=0.01, format="%.2f")
with col_add:
    st.write("")
    st.write("")
    if st.button("Add item"):
        add_item(acc_choice, desc, price)

st.divider()

# Filters
left, right = st.columns([2,1])
with left:
    selected_acc = st.selectbox("Filter by account", options=["All"] + st.session_state.accounts, index=0)
with right:
    show_totals = st.checkbox("Show totals", value=True)

# Filter items
items = st.session_state.items
if selected_acc != "All":
    filtered_items = [it for it in items if it["account"] == selected_acc]
else:
    filtered_items = items

# Display items
if not filtered_items:
    st.info("No items to show yet.")
else:
    # Table header
    hdr = st.columns([0.6, 2.8, 1, 1.2, 1.2])
    hdr[0].markdown("**ID**")
    hdr[1].markdown("**Description**")
    hdr[2].markdown("**Price**")
    hdr[3].markdown("**Account**")
    hdr[4].markdown("**Actions**")

    for it in filtered_items:
        cols = st.columns([0.6, 2.8, 1, 1.2, 1.2])
        cols[0].text(it["id"])

        if st.session_state.get(f"editing_{it['id']}", False):
            new_desc = cols[1].text_input("Desc", value=it["description"], key=f"desc_{it['id']}")
            new_price = cols[2].number_input("Price", min_value=0.0, step=0.01, format="%.2f", value=float(it["price"]), key=f"price_{it['id']}")
            new_acc = cols[3].selectbox("Account", options=st.session_state.accounts, index=st.session_state.accounts.index(it["account"]), key=f"acc_{it['id']}")
            with cols[4]:
                if st.button("Save", key=f"save_item_{it['id']}"):
                    edit_item(it["id"], new_desc, new_price, new_acc)
                    st.session_state[f"editing_{it['id']}"] = False
                if st.button("Cancel", key=f"cancel_item_{it['id']}"):
                    st.session_state[f"editing_{it['id']}"] = False
        else:
            cols[1].text(it["description"])
            cols[2].text(currency(it["price"]))
            cols[3].text(it["account"])
            with cols[4]:
                edit_key = f"edit_{it['id']}"
                del_key = f"delete_{it['id']}"
                if st.button("Edit", key=edit_key):
                    st.session_state[f"editing_{it['id']}"] = True
                if st.button("Delete", key=del_key):
                    delete_item(it["id"])
                    st.experimental_rerun()

# Totals
if show_totals and st.session_state.items:
    st.divider()
    st.subheader("Totals")
    by_acc = {}
    for it in st.session_state.items:
        by_acc[it["account"]] = by_acc.get(it["account"], 0.0) + float(it["price"])
    total_cols = st.columns([1,1,1,1,1,1])
    i = 0
    for acc, val in sorted(by_acc.items()):
        total_cols[i % 6].metric(acc, currency(val))
        i += 1
    grand_total = sum(by_acc.values())
    st.metric("Grand Total", currency(grand_total))
