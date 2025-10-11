import streamlit as st
import pandas as pd
import plotly.express as px

# ===========================================================
# --- Page Setup ---
# ===========================================================
st.set_page_config(page_title="Sales Insights Dashboard", layout="wide")

# ===========================================================
# --- Authentication Setup ---
# ===========================================================
def login():
    st.title("🔐 Login to Sales Insights Dashboard")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username == "almadina" and password == "12345":
            st.session_state["authenticated"] = True
            st.success("✅ Login successful! Access granted.")
            st.rerun()
        else:
            st.error("❌ Invalid username or password")

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    login()
    st.stop()

# ===========================================================
# --- Dashboard Code ---
# ===========================================================
st.title("📊 SAFA Oud Mehta Sales Insights")

# --- Load Data ---
df = pd.read_excel("sub cat(1).Xlsx")  # Change filename as needed

# Ensure numeric columns
numeric_cols = ["Qty Sold", "Total Sales", "Total Profit"]
for col in numeric_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

# Add GP%
df["GP%"] = (df["Total Profit"] / df["Total Sales"]) * 100

# ===========================================================
# --- Filters for Category & Subcategory ---
# ===========================================================
category_col = "Category"
subcategory_col = "Category4"  # Subcategory

if category_col in df.columns:
    categories = ["All"] + sorted(df[category_col].dropna().unique().tolist())
    selected_category = st.sidebar.selectbox("📂 Select Category", categories)

    if selected_category != "All":
        df = df[df[category_col] == selected_category]

    if subcategory_col in df.columns:
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
# --- KPIs ---
# ===========================================================
total_sales = item_summary["Total Sales"].sum()
total_profit = item_summary["Total Profit"].sum()
total_qty = item_summary["Qty Sold"].sum()

st.markdown("### 📌 Key Highlights")
col1, col2, col3 = st.columns(3)
col1.metric("💰 Total Sales", f"{total_sales:,.0f}")
col2.metric("📈 Total Profit", f"{total_profit:,.0f}")
col3.metric("📦 Total Quantity Sold", f"{total_qty:,.0f}")

st.markdown("---")

# ===========================================================
# --- Function to Plot Top N Items ---
# ===========================================================
def plot_top(df, metric, title, color, n=50):
    top = df.sort_values(metric, ascending=False).head(n)
    fig = px.bar(
        top,
        x=metric,
        y="Items",
        orientation="h",
        text=metric,
        color=metric,
        color_continuous_scale=color,
        title=title,
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
    fig.update_layout(
        height=1200,
        yaxis=dict(autorange="reversed"),
        margin=dict(l=10, r=10, t=40, b=10),
        coloraxis_showscale=False
    )
    return fig, top

# ===========================================================
# --- Category & Subcategory Graphs ---
# ===========================================================
st.markdown("## 📊 Category & Subcategory Analysis")

# Category-wise
cat_summary = (
    df.groupby(category_col)
    .agg({"Qty Sold":"sum", "Total Sales":"sum", "Total Profit":"sum"})
    .reset_index()
)
cat_summary["GP%"] = (cat_summary["Total Profit"] / cat_summary["Total Sales"]) * 100

st.subheader("📂 Category-wise Sales & Profit")
fig_cat = px.bar(
    cat_summary, x="Total Sales", y=category_col, orientation="h",
    color="Total Profit", text="Total Sales",
    color_continuous_scale="Blues", hover_data={"GP%":":.2f"}
)
fig_cat.update_traces(texttemplate='%{text:,.0f}', textposition="outside")
st.plotly_chart(fig_cat, use_container_width=True)

# Subcategory-wise
subcat_summary = (
    df.groupby([category_col, subcategory_col])
    .agg({"Qty Sold":"sum", "Total Sales":"sum", "Total Profit":"sum"})
    .reset_index()
)
subcat_summary["GP%"] = (subcat_summary["Total Profit"] / subcat_summary["Total Sales"]) * 100

st.subheader("🔖 Subcategory-wise Sales & Profit")
fig_subcat = px.bar(
    subcat_summary, x="Total Sales", y=subcategory_col, orientation="h",
    color="Total Profit", text="Total Sales",
    color_continuous_scale="Greens", hover_data={"GP%":":.2f"}
)
fig_subcat.update_traces(texttemplate='%{text:,.0f}', textposition="outside")
st.plotly_chart(fig_subcat, use_container_width=True)

st.markdown("---")

# ===========================================================
# --- Tabs (Sales, Profit, Qty, High/Low Analysis) ---
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
    fig_sales, top_sales = plot_top(item_summary, "Total Sales", "Top 50 Items by Sales", "Blues", n=50)
    st.plotly_chart(fig_sales, use_container_width=True)

# --- Tab 2: Profit ---
with tab2:
    fig_profit, top_profit = plot_top(item_summary, "Total Profit", "Top 50 Items by Profit", "Greens", n=50)
    st.plotly_chart(fig_profit, use_container_width=True)

# --- Tab 3: Quantity ---
with tab3:
    fig_qty, top_qty = plot_top(item_summary, "Qty Sold", "Top 50 Items by Quantity Sold", "Oranges", n=50)
    st.plotly_chart(fig_qty, use_container_width=True)

# --- Tab 4: High Sales, Low Profit ---
with tab4:
    qty_threshold = item_summary["Qty Sold"].quantile(0.75)
    profit_threshold = item_summary["Total Profit"].quantile(0.25)
    problem_items = item_summary[
        (item_summary["Qty Sold"] >= qty_threshold) & 
        (item_summary["Total Profit"] <= profit_threshold)
    ].sort_values("Qty Sold", ascending=False)

    st.subheader("⚠️ Items with High Quantity Sold but Low Profit")
    st.dataframe(problem_items[["Item Code","Items","Category","Category4","Qty Sold","Total Sales","Total Profit","GP%"]])

# --- Tab 5: Low Sales, High Profit ---
with tab5:
    qty_threshold = item_summary["Qty Sold"].quantile(0.25)
    profit_threshold = item_summary["Total Profit"].quantile(0.75)
    strong_items = item_summary[
        (item_summary["Qty Sold"] <= qty_threshold) & 
        (item_summary["Total Profit"] >= profit_threshold)
    ].sort_values("Total Profit", ascending=False)

    st.subheader("💡 Items with Low Sales but High Profit")
    st.dataframe(strong_items[["Item Code","Items","Category","Category4","Qty Sold","Total Sales","Total Profit","GP%"]])

# ===========================================================
# --- Full Itemwise Table (Filtered) ---
# ===========================================================
st.markdown("---")
st.markdown("## 🧾 Full Item-wise Sales Summary (Filtered)")

# Search bar
search_query = st.text_input("🔍 Search Item / Item Code")
filtered_table = item_summary.copy()

if search_query:
    filtered_table = filtered_table[
        filtered_table["Items"].str.contains(search_query, case=False, na=False) |
        filtered_table["Item Code"].astype(str).str.contains(search_query, case=False, na=False)
    ]

# Sort & format
filtered_table = filtered_table.sort_values("Total Sales", ascending=False)
formatted_table = filtered_table.copy()
formatted_table["Qty Sold"] = formatted_table["Qty Sold"].map("{:,.0f}".format)
formatted_table["Total Sales"] = formatted_table["Total Sales"].map("{:,.0f}".format)
formatted_table["Total Profit"] = formatted_table["Total Profit"].map("{:,.0f}".format)
formatted_table["GP%"] = formatted_table["GP%"].map("{:.2f}%".format)

st.dataframe(
    formatted_table[
        ["Item Code", "Items", category_col, subcategory_col, "Qty Sold", "Total Sales", "Total Profit", "GP%"]
    ],
    use_container_width=True,
    hide_index=True
)

# --- Download Filtered Data ---
csv = filtered_table.to_csv(index=False).encode('utf-8')
st.download_button(
    label="📥 Download Filtered Item-wise Data (CSV)",
    data=csv,
    file_name="Filtered_Itemwise_Sales.csv",
    mime="text/csv",
)
