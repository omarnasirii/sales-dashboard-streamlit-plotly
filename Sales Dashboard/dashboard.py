from datetime import date
import streamlit as st
import plotly.express as px
import pandas as pd
import os
import warnings
import plotly.figure_factory as ff

# Suppress warnings
warnings.filterwarnings("ignore")

# Set page configuration
st.set_page_config(page_title="Superstore!!!", page_icon=":bar_chart:", layout="wide")

# Title for the Streamlit app
st.markdown("""
    <style>
        .css-18e3th9 {
            padding-top: 2rem;  /* Increase the top padding to make room for the title */
            font-size: 36px;    /* Reduce the font size of the title */
            font-weight: bold;
            text-align: center;
        }
    </style>
""", unsafe_allow_html=True)

st.title(":bar_chart: Sample Superstore EDA")

st.markdown("<style>div.block-container {padding-top:1rem;}</style>", unsafe_allow_html=True)

# File uploader
fl = st.file_uploader(":file_folder: Upload a file", type=["csv", "txt", "xlsx", "xls"])

# Initialize df as None to handle errors
df = None

try:
    if fl is not None:
        # Read the uploaded file
        df = pd.read_csv(fl, encoding="ISO-8859-1")
    else:
        # Use default file path relative to the script directory
        default_file_path = os.path.join(os.path.dirname(__file__), "Superstore.csv")
        if os.path.exists(default_file_path):
            df = pd.read_csv(default_file_path, encoding="ISO-8859-1")
        else:
            st.error("No file uploaded, and the default dataset is missing. Please upload a file to proceed.")
            st.stop()
    
    # Check if the DataFrame is empty or invalid
    if df is None or df.empty:
        st.error("The dataset is empty or invalid. Please upload a valid file.")
        st.stop()

    # Ensure "Order Date" column exists in the DataFrame
    if "Order Date" not in df.columns:
        st.error("The dataset is missing the 'Order Date' column. Please upload a valid dataset.")
        st.stop()

    # Convert "Order Date" to datetime and drop invalid rows
    df["Order Date"] = pd.to_datetime(df["Order Date"], errors="coerce")
    df.dropna(subset=["Order Date"], inplace=True)

except Exception as e:
    st.error(f"An unexpected error occurred: {e}")
    st.stop()

# Now continue with your other logic after df is guaranteed to be valid.
if df is not None and not df.empty:

    col1, col2 = st.columns(2)

    # Handle Order Date conversion and missing values
    if "Order Date" in df.columns:
        df["Order Date"] = pd.to_datetime(df["Order Date"], errors="coerce")
        df.dropna(subset=["Order Date"], inplace=True)  # Remove rows with invalid dates
    else:
        st.error("The dataset is missing the 'Order Date' column.")
        st.stop()

    # Get min and max date
    startDate = df["Order Date"].min()
    endDate = df["Order Date"].max()

    with col1:
        date1 = st.date_input("Start Date", startDate)
        date1 = pd.to_datetime(date1)

    with col2:
        date2 = st.date_input("End Date", endDate)
        date2 = pd.to_datetime(date2)

    df = df[(df["Order Date"] >= date1) & (df["Order Date"] <= date2)].copy()

    if df.empty:
        st.warning("No data available for the selected date range. Please adjust your filters.")
        st.stop()

    # Sidebar filters
    st.sidebar.header("Choose your filter: ")

    # Filter by Region
    region = st.sidebar.multiselect("Pick your Region", df["Region"].unique())
    df_region = df[df["Region"].isin(region)] if region else df

    # Filter by State
    state = st.sidebar.multiselect("Pick the State", df_region["State"].unique())
    df_state = df_region[df_region["State"].isin(state)] if state else df_region

    # Filter by City
    city = st.sidebar.multiselect("Pick the City", df_state["City"].unique())
    filtered_df = df_state[df_state["City"].isin(city)] if city else df_state

    if filtered_df.empty:
        st.warning("No data available after applying the selected filters. Please adjust your filters.")
        st.stop()

    # Aggregated sales by Category
    category_df = filtered_df.groupby(by=["Category"], as_index=False)["Sales"].sum()

    # Visualization
    with col1:
        st.subheader("Category-wise Sales")
        fig = px.bar(
            category_df,
            x="Category",
            y="Sales",
            text=[f'${x:,.2f}' for x in category_df["Sales"]],
            template="seaborn",
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Region-wise Sales")
        fig = px.pie(
            filtered_df, 
            values="Sales", 
            names="Region", 
            hole=0.5
        )
        st.plotly_chart(fig, use_container_width=True)

    cl1, cl2 = st.columns(2)

    # Category Data View with Download
    with cl1:
        with st.expander("Category Data View"):
            try:
                st.write(category_df.style.background_gradient(cmap="Blues"))
            except ImportError:
                st.write("Matplotlib is required for background gradients. Please install it.")
            if not category_df.empty:
                csv = category_df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "Download Category Data", 
                    data=csv, 
                    file_name="Category_Sales.csv", 
                    mime="text/csv",
                    help="Click to download the category sales data."
                )
            else:
                st.warning("No data available for category sales.")

    # Region Data View with Download
    with cl2:
        with st.expander("Region Data View"):
            region_sales = filtered_df.groupby(by="Region", as_index=False)["Sales"].sum()
            try:
                st.write(region_sales.style.background_gradient(cmap="Oranges"))
            except ImportError:
                st.write("Matplotlib is required for background gradients. Please install it.")
            if not region_sales.empty:
                csv = region_sales.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "Download Region Data", 
                    data=csv, 
                    file_name="Region_Sales.csv", 
                    mime="text/csv",
                    help="Click to download the region sales data."
                )
            else:
                st.warning("No data available for region sales.")

    # Time Series Analysis
    filtered_df["month_year"] = filtered_df["Order Date"].dt.to_period("M")
    st.subheader("Time Series Analysis")
    linechart = pd.DataFrame(
        filtered_df.groupby(filtered_df["month_year"].dt.strftime("%Y-%b"))["Sales"].sum()
    ).reset_index()
    linechart.rename(columns={"month_year": "Month_Year"}, inplace=True)

    fig2 = px.line(
        linechart, 
        x="Month_Year", 
        y="Sales", 
        labels={"Sales": "Amount"}, 
        height=500, 
        template="gridon"
    )
    st.plotly_chart(fig2, use_container_width=True)

    with st.expander("View Time Series Data"):
        st.write(linechart.T.style.background_gradient(cmap="Blues"))
        csv = linechart.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download Time Series Data", 
            data=csv, 
            file_name="TimeSeries_Sales.csv", 
            mime="text/csv"
        )

    # Create a treemap based on Region, Category, and Sub-Category
    st.subheader("Hierarchical View of Sales Using Treemap")
    fig3 = px.treemap(
        filtered_df, 
        path=["Region", "Category", "Sub-Category"], 
        values="Sales", 
        hover_data=["Sales"], 
        color="Sub-Category"
    )
    fig3.update_layout(width=800, height=650)
    st.plotly_chart(fig3, use_container_width=True)

    chart1, chart2 = st.columns(2)
    with chart1:
        st.subheader('Segment wise Sales')
        fig = px.pie(filtered_df, values = "Sales", names = "Segment", template = "plotly_dark")
        fig.update_traces(text = filtered_df["Segment"], textposition = "inside")
        st.plotly_chart(fig, use_container_width=True)

    with chart2:
        st.subheader('Category wise Sales')
        fig = px.pie(filtered_df, values = "Sales", names = "Category", template = "gridon")
        fig.update_traces(text = filtered_df["Category"], textposition = "inside")
        st.plotly_chart(fig, use_container_width=True)

    st.subheader(":point_right: Month-wise Sub-Category Sales Summary")
    with st.expander("Summary_Table"):
        df_sample = df[0:5][["Region", "State", "City", "Category", "Sales", "Profit", "Quantity"]]
        fig = ff.create_table(df_sample, colorscale = "Cividis")
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("Month wise Sub-Category Table")
        filtered_df["month"] = filtered_df["Order Date"].dt.month_name()
        sub_category_Year = pd.pivot_table(data = filtered_df, values = "Sales", index = ["Sub-Category"], columns = "month")
        st.write(sub_category_Year.style.background_gradient(cmap = "Blues"))

    # Create a Scatter Plot 
    data1 = px.scatter(filtered_df, x = "Sales", y = "Profit", size = "Quantity")
    data1['layout'].update(title="Relationship between Sales and Profits using Scatter Plot",
                            titlefont = dict(size=20), xaxis = dict(title="Sales", titlefont = dict(size=19)), 
                            yaxis = dict(title = "Profit", titlefont = dict(size=19)))
    st.plotly_chart(data1, use_container_width = True)

    with st.expander("View Data"):
        st.write(filtered_df.iloc[:500, 1:20:2].style.background_gradient(cmap = "Oranges"))

    # Download Original Dataset
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button('Download Data', data = csv, file_name = "Data.csv", mime = "text/csv" )

