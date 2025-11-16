import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO

st.title("Inventory Optimization: ROP & EOQ Calculator")
st.write("Manage SKUs, calculate reorder points, and economic order quantities interactively.")

# ------------------------
# Initialize dataset
# ------------------------
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame({
        "SKU": ['A 101', 'B 101'],
        "Class": ["A", "B"],
        "Average_Daily_Demand": [50, 30],
        "Lead_Time_Days": [10, 5],
        "Safety_Stock": [100, 50],
        "Order_Cost": [200, 150],
        "Holding_Cost": [2, 1.5]
    })

# ------------------------
# Functions
# ------------------------
def calculate_metrics(df):
    df["ROP"] = (df["Average_Daily_Demand"] * df["Lead_Time_Days"]) + df["Safety_Stock"]
    df["Annual_Demand"] = df["Average_Daily_Demand"] * 365
    df["EOQ"] = np.sqrt((2 * df["Annual_Demand"] * df["Order_Cost"]) / df["Holding_Cost"])
    df["Total_Cost"] = (df["EOQ"]/2 * df["Holding_Cost"]) + (df["Annual_Demand"]/df["EOQ"] * df["Order_Cost"])
    return df

def download_excel(df):
    buffer = BytesIO()
    df.to_excel(buffer, index=False)
    buffer.seek(0)
    return buffer

def apply_scenario(df, scenario):
    df = df.copy()
    if scenario == "High Demand (+20%)":
        df["Average_Daily_Demand"] = df["Average_Daily_Demand"] * 1.2
    elif scenario == "Supply Delay (+3 days)":
        df["Lead_Time_Days"] = df["Lead_Time_Days"] + 3
    elif scenario == "High Demand + Supply Delay":
        df["Average_Daily_Demand"] = df["Average_Daily_Demand"] * 1.2
        df["Lead_Time_Days"] = df["Lead_Time_Days"] + 3
    return calculate_metrics(df)

def generate_sku_label(sku_class, sku_number):
    return f'{sku_class} {sku_number}'

# ------------------------
# Sidebar Options
# ------------------------
option = st.sidebar.selectbox("Select Action", 
    ["View SKUs", "Add SKU", "Update SKU", "Delete SKU", "Upload Data", "Download Data"])

# ------------------------
# CRUD Operations + File Handling
# ------------------------
if option == "View SKUs":
    st.subheader("Scenario Analysis for SKUs")
    
    scenario = st.selectbox("Select Scenario", 
                            ["Base Case", "High Demand (+20%)", "Supply Delay (+3 days)", "High Demand + Supply Delay"])
    
    df_scenario = apply_scenario(st.session_state.data, scenario)
    st.dataframe(df_scenario)
    
    # Visualization: ROP vs EOQ scatter plot
    st.subheader(f"ROP vs EOQ Chart ({scenario})")
    fig, ax = plt.subplots(figsize=(6,4))
    ax.scatter(df_scenario["ROP"], df_scenario["EOQ"], s=100, alpha=0.7)
    for i, sku in enumerate(df_scenario["SKU"]):
        ax.text(df_scenario["ROP"][i]+5, df_scenario["EOQ"][i], sku, fontsize=8)
    ax.set_xlabel("Reorder Point (Units)")
    ax.set_ylabel("Economic Order Quantity (Units)")
    ax.set_title(f"ROP vs EOQ - {scenario}")
    st.pyplot(fig)
    
    # Class-wise summary
    st.subheader("Class-wise Summary")
    class_summary = df_scenario.groupby("Class")[["ROP","EOQ","Total_Cost"]].sum().reset_index()
    st.table(class_summary)

elif option == "Add SKU":
    st.subheader("Add a New SKU")
    sku_class = st.selectbox("Product Class", ["A", "B", "C", "D"])
    sku_number = st.text_input("SKU Number (e.g., 101)")
    demand = st.number_input("Average Daily Demand", 1)
    lead = st.number_input("Lead Time (Days)", 1)
    safety = st.number_input("Safety Stock", 1)
    order_cost = st.number_input("Order Cost", 1.0)
    holding_cost = st.number_input("Holding Cost", 0.1)

    if st.button("Add SKU"):
        sku_label = generate_sku_label(sku_class, sku_number)
        new_row = pd.DataFrame([[sku_label, sku_class, demand, lead, safety, order_cost, holding_cost]],
                               columns=st.session_state.data.columns)
        st.session_state.data = pd.concat([st.session_state.data, new_row], ignore_index=True)
        st.success(f'SKU {sku_label} added successfully!')

elif option == "Update SKU":
    st.subheader("Update an Existing SKU")
    sku_list = st.session_state.data["SKU"].tolist()
    selected = st.selectbox("Select SKU to Update", sku_list)

    if selected:
        idx = st.session_state.data[st.session_state.data["SKU"] == selected].index[0]
        current_class = st.session_state.data.loc[idx, "Class"]
        current_number = st.session_state.data.loc[idx, "SKU"].split(" ")[1]  # <-- fixed

        sku_class = st.selectbox("Product Class", ["A", "B", "C", "D"], 
                                 index=["A","B","C","D"].index(current_class))
        sku_number = st.text_input("SKU Number", value=current_number)
        
        demand = st.number_input("Average Daily Demand", value=float(st.session_state.data.loc[idx, "Average_Daily_Demand"]))
        lead = st.number_input("Lead Time (Days)", value=float(st.session_state.data.loc[idx, "Lead_Time_Days"]))
        safety = st.number_input("Safety Stock", value=float(st.session_state.data.loc[idx, "Safety_Stock"]))
        order_cost = st.number_input("Order Cost", value=float(st.session_state.data.loc[idx, "Order_Cost"]))
        holding_cost = st.number_input("Holding Cost", value=float(st.session_state.data.loc[idx, "Holding_Cost"]))

        if st.button("Update SKU"):
            sku_label = generate_sku_label(sku_class, sku_number)
            st.session_state.data.loc[idx] = [sku_label, sku_class, demand, lead, safety, order_cost, holding_cost]
            st.success(f'SKU {sku_label} updated successfully!')

elif option == "Delete SKU":
    st.subheader("Delete an SKU")
    sku_list = st.session_state.data["SKU"].tolist()
    selected = st.selectbox("Select SKU to Delete", sku_list)

    if st.button("Delete SKU"):
        st.session_state.data = st.session_state.data[st.session_state.data["SKU"] != selected]
        st.success("SKU deleted successfully!")

elif option == "Upload Data":
    st.subheader("Upload an Excel or CSV File")
    file = st.file_uploader("Choose a file", type=["csv", "xlsx"])

    if file is not None:
        if file.name.endswith(".csv"):
            uploaded_df = pd.read_csv(file)
        else:
            uploaded_df = pd.read_excel(file)

        # Ensure required columns exist
        required_cols = st.session_state.data.columns.tolist()
        if all(col in uploaded_df.columns for col in required_cols):
            st.session_state.data = uploaded_df
            st.success("Data uploaded successfully!")
        else:
            st.error(f"File must include these columns: {required_cols}")

elif option == "Download Data":
    st.subheader("Download Current Data")
    df = calculate_metrics(st.session_state.data.copy())
    excel_data = download_excel(df)
    st.download_button(
        label="Download as Excel",
        data=excel_data,
        file_name="inventory_data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
