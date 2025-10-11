import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- PAGE CONFIG ---
st.set_page_config(page_title="Healthy Stock Dashboard", layout="wide")

# --- LOAD FILES ---
SALES_FILE = "full sales of 2025 safa.Xlsx"
AGING_FILE = "safa aging.xlsx"

# --- READ DATA ---
if os.path.exists(SALES_FILE):
    sales_df = pd.read_excel(SALES_FILE)
else:
    st.error(f"❌ '{SALES_FILE}' not found. Please add your sales data file.")
    st.stop()

if os.path.exists(AGING_FILE):
    aging_df = pd.read_excel(AGING_FILE)
else:
    st.warning(f"⚠️ '{AGING_FILE}' not found. Aging-related features will be disabled.")
    aging_df = pd.DataFrame()

# --- CLEAN & STANDARDIZE COLUMN NAMES ---
sales_df.columns = sales_df.columns.str.strip().str.replace("\n", " ")
aging_df.columns = aging_df.columns.str.strip().str.replace("\n", " ")

# --- MERGE SALES + AGING DATA ---
merge_keys = ["Item Name", "Category", "Barcode"]
common_keys = [key for key in merge_keys if key in sales_df.columns and key in aging_df.columns]
merged_df = pd.merge(sales_df, aging_df, how="left", on=common_keys)

# --- CALCULATE AVERAGE MONTHLY SALES ---
sales_cols = [col for col in merged_df.columns if "Total Sales" in col]
if sales_cols:
    merged_df["Average Monthly Sales"] = merged_df[sales_cols].mean(axis=1)
else:
    st.error("No 'Total Sales' columns found in sales data.")
    st.stop()

# --- SAFETY FACTOR (Months of Cover) ---
if "Stock" in merged_df.columns:
    merged_df["Safety Factor (Months of Cover)"] = merged_df["Stock"] / merged_df["Average Monthly Sales"]
else:
    st.error("No 'Stock' column found in aging data. Please include stock quantity.")
    st.stop()

# --- FILTERS (SIDEBAR) ---
st.sidebar.header("🔍 Filters")

# Category filter
if "Category" in merged_df.columns:
    categories = ["All"] + sorted(merged_df["Category"].dropna().unique().tolist())
    selected_category = st.sidebar.selectbox("Select Category", categories)
    if selected_category != "All":
        merged_df = merged_df[merged_df["Category"] == selected_category]

# Toggle to show aging data
show_aging = st.sidebar.checkbox("Show Aging Data (Safa Aging.xlsx)", value=False)

# --- MAIN SECTION ---
st.title("📊 Healthy Stock & Safety Factor Dashboard")

st.markdown("""
This dashboard calculates **Safety Factor (Months of Cover)** for each item:
> 🧮 `Months of Cover = Current Stock / Average Monthly Sales`

- **< 1 month:** ⚠️ Low stock (reorder soon)  
- **1–3 months:** ✅ Healthy stock  
- **> 3 months:** 📦 Overstock
""")

# --- TOP 100 ITEMS ---
top_items = merged_df.sort_values("Safety Factor (Months of Cover)", ascending=False).head(100)

# --- HORIZONTAL BAR CHART ---
fig = px.bar(
    top_items,
    x="Safety Factor (Months of Cover)",
    y="Item Name",
    color="Category" if "Category" in top_items.columns else None,
    orientation="h",
    title="Top 100 Items by Safety Factor (Months of Cover)",
    labels={"Safety Factor (Months of Cover)": "Months of Cover", "Item Name": "Item"},
)
fig.update_layout(yaxis={'categoryorder': 'total ascending'}, height=1500)
st.plotly_chart(fig, use_container_width=True)

# --- DATA TABLE ---
st.subheader("📋 Item-wise Safety Factor Data")
st.dataframe(top_items[["Item Name", "Category", "Stock", "Average Monthly Sales", "Safety Factor (Months of Cover)"]])

# --- AGING DATA SECTION ---
if show_aging and not aging_df.empty:
    st.subheader("📅 Safa Stock Aging Report")
    st.dataframe(aging_df)
