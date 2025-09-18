
import streamlit as st
from typing import List, Dict, Any
from itertools import count

st.set_page_config(page_title="Simple Ledger", layout="wide")

# Initialize session state
if "categories" not in st.session_state:
    st.session_state.categories: List[str] = []
if "items" not in st.session_state:
    st.session_state.items: List[Dict[str, Any]] = []
if "id_counter" not in st.session_state:
    st.session_state.id_counter = count(1)

def add_category(name: str):
    name = name.strip()
    if name and name not in st.session_state.categories:
        st.session_state.categories.append(name)

def delete_category(name: str):
    # Remove category and any items belonging to it
    st.session_state.categories = [c for c in st.session_state.categories if c != name]
    st.session_state.items = [it for it in st.session_state.items if it["category"] != name]

def rename_category(old: str, new: str):
    new = new.strip()
    if not new or (new != old and new in st.session_state.categories):
        return
    idx = st.session_state.categories.index(old)
    st.session_state.categories[idx] = new
    for it in st.session_state.items:
        if it["category"] == old:
            it["category"] = new

def add_item(category: str, description: str, price: float):
    if not category or category not in st.session_state.categories:
        st.warning("Select or create a category first.")
        return
    description = description.strip()
    if not description:
        st.warning("Description cannot be empty.")
        return
    item_id = next(st.session_state.id_counter)
    st.session_state.items.append({
        "id": item_id,
        "category": category,
        "description": description,
        "price": float(price),
    })

def delete_item(item_id: int):
    st.session_state.items = [it for it in st.session_state.items if it["id"] != item_id]

def edit_item(item_id: int, new_desc: str, new_price: float, new_cat: str):
    for it in st.session_state.items:
        if it["id"] == item_id:
            it["description"] = new_desc.strip()
            it["price"] = float(new_price)
            it["category"] = new_cat
            break

def currency(v: float) -> str:
    return f"$ {v:,.2f}"

st.title("Simple Ledger (no persistence)")

# Sidebar: Category management
st.sidebar.header("Categories")

with st.sidebar.expander("Add category", expanded=True):
    new_cat = st.text_input("Name", key="new_cat_input")
    if st.button("Add", use_container_width=True):
        add_category(new_cat)
        st.session_state.new_cat_input = ""

if st.session_state.categories:
    st.sidebar.write("Existing categories")
    for cat in st.session_state.categories:
        cols = st.sidebar.columns([1, 1, 1.2, 1])
        cols[0].markdown(f"**{cat}**")

        with cols[1]:
            if st.button("Rename", key=f"rename_{cat}"):
                st.session_state[f"renaming_{cat}"] = True
        with cols[3]:
            if st.button("Delete", key=f"del_{cat}"):
                delete_category(cat)
                st.experimental_rerun()
        if st.session_state.get(f"renaming_{cat}"):
            new_name = st.text_input(f"New name for '{cat}'", key=f"new_name_{cat}")
            cols2 = st.sidebar.columns([1,1])
            with cols2[0]:
                if st.button("Save", key=f"save_{cat}"):
                    rename_category(cat, new_name)
                    st.session_state[f"renaming_{cat}"] = False
                    st.experimental_rerun()
            with cols2[1]:
                if st.button("Cancel", key=f"cancel_{cat}"):
                    st.session_state[f"renaming_{cat}"] = False

# Main area
st.subheader("Add item")
col_cat, col_desc, col_price, col_add = st.columns([1.2, 3, 1, 1])
with col_cat:
    cat_choice = st.selectbox("Category", options=[""] + st.session_state.categories, index=0, help="Choose a category")
with col_desc:
    desc = st.text_input("Description")
with col_price:
    price = st.number_input("Price", min_value=0.0, step=0.01, format="%.2f")
with col_add:
    st.write("")
    st.write("")
    if st.button("Add item"):
        add_item(cat_choice, desc, price)

st.divider()

# Filters
left, right = st.columns([2,1])
with left:
    selected_cat = st.selectbox("Filter by category", options=["All"] + st.session_state.categories, index=0)
with right:
    show_totals = st.checkbox("Show totals", value=True)

# Filter items
items = st.session_state.items
if selected_cat != "All":
    items = [it for it in items if it["category"] == selected_cat]

# Display items
if not items:
    st.info("No items to show yet.")
else:
    # Table header
    hdr = st.columns([0.6, 2.8, 1, 1.2, 1.2])
    hdr[0].markdown("**ID**")
    hdr[1].markdown("**Description**")
    hdr[2].markdown("**Price**")
    hdr[3].markdown("**Category**")
    hdr[4].markdown("**Actions**")

    for it in items:
        cols = st.columns([0.6, 2.8, 1, 1.2, 1.2])
        cols[0].text(it["id"])

        if st.session_state.get(f"editing_{it['id']}", False):
            new_desc = cols[1].text_input("Desc", value=it["description"], key=f"desc_{it['id']}")
            new_price = cols[2].number_input("Price", min_value=0.0, step=0.01, format="%.2f", value=float(it["price"]), key=f"price_{it['id']}")
            new_cat = cols[3].selectbox("Category", options=st.session_state.categories, index=st.session_state.categories.index(it["category"]), key=f"cat_{it['id']}")
            with cols[4]:
                if st.button("Save", key=f"save_item_{it['id']}"):
                    edit_item(it["id"], new_desc, new_price, new_cat)
                    st.session_state[f"editing_{it['id']}"] = False
                if st.button("Cancel", key=f"cancel_item_{it['id']}"):
                    st.session_state[f"editing_{it['id']}"] = False
        else:
            cols[1].text(it["description"])
            cols[2].text(currency(it["price"]))
            cols[3].text(it["category"])
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
    by_cat = {}
    for it in st.session_state.items:
        by_cat[it["category"]] = by_cat.get(it["category"], 0.0) + float(it["price"])
    total_cols = st.columns([1,1,1,1,1,1])
    i = 0
    for cat, val in sorted(by_cat.items()):
        total_cols[i % 6].metric(cat, currency(val))
        i += 1
    grand_total = sum(by_cat.values())
    st.metric("Grand Total", currency(grand_total))
