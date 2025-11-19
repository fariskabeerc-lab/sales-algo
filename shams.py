import streamlit as st
import pandas as pd
import plotly.express as px

# ===========================================================
# --- Page Setup ---
# ===========================================================
st.set_page_config(page_title="Sales Insights Dashboard", layout="wide")

# ===========================================================
# --- Authentication ---
# ===========================================================
def login():
    st.title("🔐 Login to Sales Insights Dashboard")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        if username == "almadina" and password == "12345":
            st.session_state["authenticated"] = True
            st.success("✅ Login successful!")
            st.experimental_rerun()
        else:
            st.error("❌ Invalid username or password")

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    login()
    st.stop()

# ===========================================================
# --- Load Data ---
# ===========================================================
st.title("📊 Shams Sales Analysis (Jan 11–15, 2025)")
df = pd.read_excel("anniversary sales shams.Xlsx")  # replace with your file path

# Ensure numeric columns
numeric_cols = ["Qty Sold", "Total Sales", "Total Profit"]
for col in numeric_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

df["GP%"] = (df["Total Profit"] / df["Total Sales"]) * 100

category_col = "Category"
subcategory_col = "Category4"

# ===========================================================
# --- Sidebar Filters ---
# ===========================================================
categories = ["All"] + sorted(df[category_col].dropna().unique().tolist())
selected_category = st.sidebar.selectbox("📂 Select Category", categories)

if selected_category != "All":
    df = df[df[category_col] == selected_category]

subcategories = ["All"] + sorted(df[subcategory_col].dropna().unique().tolist())
selected_subcat = st.sidebar.selectbox("🔖 Select Subcategory", subcategories)

if selected_subcat != "All":
    df = df[df[subcategory_col] == selected_subcat]

# ===========================================================
# --- Aggregate per Item ---
# ===========================================================
item_summary = (
    df.groupby(["Item Code", "Items", category_col, subcategory_col], dropna=False)
    .agg({
        "Qty Sold": "sum",
        "Total Sales": "sum",
        "Total Profit": "sum"
    })
    .reset_index()
)
item_summary["GP%"] = (item_summary["Total Profit"] / item_summary["Total Sales"]) * 100

# ===========================================================
# --- Search Filter ---
# ===========================================================
search_query = st.text_input("🔍 Search Item / Item Code")
filtered_summary = item_summary.copy()

if search_query:
    filtered_summary = filtered_summary[
        filtered_summary["Items"].str.contains(search_query, case=False, na=False) |
        filtered_summary["Item Code"].astype(str).str.contains(search_query, case=False, na=False)
    ]

# ===========================================================
# --- KPIs ---
# ===========================================================
st.markdown("### 📌 Key Highlights")
total_sales = filtered_summary["Total Sales"].sum()
total_profit = filtered_summary["Total Profit"].sum()
total_qty = filtered_summary["Qty Sold"].sum()
gp_percent = (total_profit / total_sales) * 100 if total_sales != 0 else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("💰 Total Sales", f"{total_sales:,.0f}")
col2.metric("📈 Total Profit", f"{total_profit:,.0f}")
col3.metric("📦 Total Qty Sold", f"{total_qty:,.0f}")
col4.metric("📊 GP%", f"{gp_percent:.2f}%")

# ===========================================================
# --- Category & Subcategory Charts ---
# ===========================================================
st.markdown("## 📊 Category & Subcategory Analysis")

# Category-wise
cat_summary = (
    filtered_summary.groupby(category_col)
    .agg({
        "Qty Sold": "sum",
        "Total Sales": "sum",
        "Total Profit": "sum"
    })
    .reset_index()
)
cat_summary["GP%"] = (cat_summary["Total Profit"] / cat_summary["Total Sales"]) * 100

st.subheader("📂 Category-wise Quantity Sold")
fig_cat = px.bar(
    cat_summary,
    x="Qty Sold",
    y=category_col,
    orientation="h",
    text="Qty Sold",
    color="Qty Sold",
    color_continuous_scale="Blues",
    hover_data={
        "Total Sales": ":,.0f",
        "Total Profit": ":,.0f",
        "GP%": ":.2f"
    }
)
fig_cat.update_traces(texttemplate='%{text:,.0f}', textposition="outside")
fig_cat.update_layout(height=600, margin=dict(l=10, r=10, t=40, b=10), coloraxis_showscale=False)
st.plotly_chart(fig_cat, use_container_width=True)

st.write("### 📋 Category Summary Table")
st.dataframe(cat_summary.sort_values("Qty Sold", ascending=False), use_container_width=True)

# Subcategory-wise
if selected_category != "All":
    st.subheader(f"🔖 Subcategory-wise Quantity Sold ({selected_category})")
    subcat_summary = (
        filtered_summary.groupby([category_col, subcategory_col])
        .agg({
            "Qty Sold": "sum",
            "Total Sales": "sum",
            "Total Profit": "sum"
        })
        .reset_index()
    )
    subcat_summary["GP%"] = (subcat_summary["Total Profit"] / subcat_summary["Total Sales"]) * 100
    subcat_summary = subcat_summary[subcat_summary[category_col] == selected_category]

    fig_subcat = px.bar(
        subcat_summary,
        x="Qty Sold",
        y=subcategory_col,
        orientation="h",
        text="Qty Sold",
        color="Qty Sold",
        color_continuous_scale="Viridis",
        hover_data={
            "Total Sales": ":,.0f",
            "Total Profit": ":,.0f",
            "GP%": ":.2f"
        }
    )
    fig_subcat.update_traces(texttemplate='%{text:,.0f}', textposition="outside")
    fig_subcat.update_layout(height=700, margin=dict(l=10, r=10, t=40, b=20), coloraxis_showscale=False)
    st.plotly_chart(fig_subcat, use_container_width=True)
    st.write("### 📋 Subcategory Summary Table")
    st.dataframe(subcat_summary.sort_values("Qty Sold", ascending=False), use_container_width=True)
else:
    st.info("ℹ️ Select a category to view subcategory-wise details.")

st.markdown("---")

# ===========================================================
# --- Top N Charts Function ---
# ===========================================================
def plot_top(df, metric, color, n=50):
    top = df.sort_values(metric, ascending=False).head(n)
    fig = px.bar(
        top,
        x=metric,
        y="Items",
        orientation="h",
        text=metric,
        color=metric,
        color_continuous_scale=color,
        hover_data={
            "Item Code": True,
            "Category": True,
            "Category4": True,
            "Qty Sold": ":,.0f",
            "Total Sales": ":,.0f",
            "Total Profit": ":,.0f",
            "GP%": ":.2f"
        }
    )
    fig.update_traces(texttemplate='%{text:,.0f}', textposition="outside")
    fig.update_layout(height=600, yaxis=dict(autorange="reversed"), margin=dict(l=10, r=10, t=40, b=10), coloraxis_showscale=False)
    return fig, top

# ===========================================================
# --- Tabs with charts and tables ---
# ===========================================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "💰 Sales",
    "📈 Profit",
    "📦 Quantity",
    "⚠️ High Sales, Low Profit",
    "💡 Low Sales, High Profit"
])

# --- Tab 1: Sales ---
with tab1:
    fig_sales, top_sales = plot_top(filtered_summary, "Total Sales", "Blues", n=50)
    st.plotly_chart(fig_sales, use_container_width=True)
    
    st.markdown("### 📋 Top 50 Items by Sales")
    table_sales = top_sales.copy()
    table_sales["Qty Sold"] = table_sales["Qty Sold"].map("{:,.0f}".format)
    table_sales["Total Sales"] = table_sales["Total Sales"].map("{:,.0f}".format)
    table_sales["Total Profit"] = table_sales["Total Profit"].map("{:,.0f}".format)
    table_sales["GP%"] = table_sales["GP%"].map("{:.2f}%".format)
    st.dataframe(table_sales[["Item Code","Items",category_col,subcategory_col,"Qty Sold","Total Sales","Total Profit","GP%"]], use_container_width=True)

# --- Tab 2: Profit ---
with tab2:
    fig_profit, top_profit = plot_top(filtered_summary, "Total Profit", "Greens", n=50)
    st.plotly_chart(fig_profit, use_container_width=True)
    
    st.markdown("### 📋 Top 50 Items by Profit")
    table_profit = top_profit.copy()
    table_profit["Qty Sold"] = table_profit["Qty Sold"].map("{:,.0f}".format)
    table_profit["Total Sales"] = table_profit["Total Sales"].map("{:,.0f}".format)
    table_profit["Total Profit"] = table_profit["Total Profit"].map("{:,.0f}".format)
    table_profit["GP%"] = table_profit["GP%"].map("{:.2f}%".format)
    st.dataframe(table_profit[["Item Code","Items",category_col,subcategory_col,"Qty Sold","Total Sales","Total Profit","GP%"]], use_container_width=True)

# --- Tab 3: Quantity ---
with tab3:
    fig_qty, top_qty = plot_top(filtered_summary, "Qty Sold", "Oranges", n=50)
    st.plotly_chart(fig_qty, use_container_width=True)
    
    st.markdown("### 📋 Top 50 Items by Quantity Sold")
    table_qty = top_qty.copy()
    table_qty["Qty Sold"] = table_qty["Qty Sold"].map("{:,.0f}".format)
    table_qty["Total Sales"] = table_qty["Total Sales"].map("{:,.0f}".format)
    table_qty["Total Profit"] = table_qty["Total Profit"].map("{:,.0f}".format)
    table_qty["GP%"] = table_qty["GP%"].map("{:.2f}%".format)
    st.dataframe(table_qty[["Item Code","Items",category_col,subcategory_col,"Qty Sold","Total Sales","Total Profit","GP%"]], use_container_width=True)

# --- Tab 4: High Sales, Low Profit ---
with tab4:
    qty_high = filtered_summary["Qty Sold"].quantile(0.75)
    profit_low = filtered_summary["Total Profit"].quantile(0.25)
    problem_items = filtered_summary[
        (filtered_summary["Qty Sold"] >= qty_high) &
        (filtered_summary["Total Profit"] <= profit_low)
    ]
    st.subheader("⚠️ High Sales but Low Profit")
    st.dataframe(problem_items.sort_values("Qty Sold", ascending=False), use_container_width=True)

# --- Tab 5: Low Sales, High Profit ---
with tab5:
    qty_low = filtered_summary["Qty Sold"].quantile(0.25)
    profit_high = filtered_summary["Total Profit"].quantile(0.75)
    strong_items = filtered_summary[
        (filtered_summary["Qty Sold"] <= qty_low) &
        (filtered_summary["Total Profit"] >= profit_high)
    ]
    st.subheader("💡 Low Sales but High Profit")
    st.dataframe(strong_items.sort_values("Total Profit", ascending=False), use_container_width=True)

# ===========================================================
# --- Full Item-wise Table ---
# ===========================================================
st.markdown("---")
st.markdown("## 🧾 Full Item-wise Table")

formatted = filtered_summary.copy().sort_values("Total Sales", ascending=False)
formatted["Qty Sold"] = formatted["Qty Sold"].map("{:,.0f}".format)
formatted["Total Sales"] = formatted["Total Sales"].map("{:,.0f}".format)
formatted["Total Profit"] = formatted["Total Profit"].map("{:,.0f}".format)
formatted["GP%"] = formatted["GP%"].map("{:.2f}%".format)

st.dataframe(formatted[["Item Code","Items",category_col,subcategory_col,"Qty Sold","Total Sales","Total Profit","GP%"]],
             use_container_width=True)

csv = filtered_summary.to_csv(index=False).encode('utf-8')
st.download_button(
    label="📥 Download CSV",
    data=csv,
    file_name="Filtered_Itemwise_Sales.csv",
    mime="text/csv"
)
