import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- CONFIGURATION ---
SHEET_NAME = "Storage Control System Ver 2.0"
TAB_NAME = "MRP_Data"

# --- SETUP CONNECTION ---
def get_database_connection():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

    # DEBUG: Check if secrets are loaded
    # This tells Python: "If the secret box is NOT empty, use it!"
    if "gcp_service_account" in st.secrets:
        creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(st.secrets["gcp_service_account"]), scope)
    else:
        # Fallback to local file (Only for your Mac)
        creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)

    client = gspread.authorize(creds)
    sheet = client.open(SHEET_NAME)
    return sheet

# --- APP LAYOUT ---
st.set_page_config(page_title="Paclink MRP", layout="wide")
st.title("🏭 Paclink MRP System")

# --- MAIN LOGIC ---
try:
    # 1. Connect
    sheet = get_database_connection()
    worksheet = sheet.worksheet(TAB_NAME)

    # Sidebar Menu
    st.sidebar.header("Navigation")
    menu = st.sidebar.radio("Go to:", ["Dashboard", "Inventory", "Add New Item"])

    if menu == "Dashboard":
        st.subheader("📊 Dashboard")
        st.success(f"✅ Connected to Cloud Database: {SHEET_NAME}")
        st.write("Welcome to your MRP system. Select 'Inventory' to manage stock.")

    elif menu == "Inventory":
        st.subheader("📦 Live Inventory (Editable)")
        
        # Get data
        data = worksheet.get_all_records()
        if data:
            df = pd.DataFrame(data)

            # Search Bar
            col1, col2 = st.columns([3, 1]) 
            with col1:
                search_term = st.text_input("🔍 Search Inventory:")

            # Filter Logic
            if search_term:
                st.info("⚠️ Editing is disabled while searching. Clear search to edit.")
                mask = df.astype(str).apply(lambda x: x.str.contains(search_term, case=False)).any(axis=1)
                st.dataframe(df[mask], use_container_width=True)
            else:
                # --- EDITABLE TABLE ---
                edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)

                # Save Button
                if not edited_df.equals(df):
                    st.write("Changes detected!")
                    if st.button("💾 Save Changes to Google Sheet"):
                        try:
                            worksheet.clear()
                            worksheet.append_row(edited_df.columns.tolist())
                            worksheet.append_rows(edited_df.values.tolist())
                            st.success("✅ Database updated successfully!")
                            st.rerun() 
                        except Exception as e:
                            st.error(f"Error saving: {e}")

        else:
            st.warning("Database is empty.")

    elif menu == "Add New Item":
        st.subheader("➕ Add New Inventory Item")
        
        with st.form("add_item_form"):
            st.write("Enter main details (Others will be set to 0/Blank)")
            col1, col2 = st.columns(2)
            
            with col1:
                group = st.text_input("Group")
                cat = st.text_input("CAT")
                stock_code = st.text_input("StockCode (Required)")
                desc = st.text_input("Description")
            
            with col2:
                uom = st.text_input("UOM")
                bal = st.number_input("Current Balance (Bal)", min_value=0.0)
                t_mm = st.number_input("T (mm)", value=0.0)
                w_mm = st.number_input("W (mm)", value=0.0)

            submitted = st.form_submit_button("💾 Save New Item")
            
            if submitted:
                if not stock_code:
                    st.error("Error: StockCode is required.")
                else:
                    try:
                        existing_data = worksheet.get_all_values()
                        next_sn = len(existing_data) 
                        
                        # PREPARE ROW (18 Columns)
                        new_row = [
                            next_sn, group, cat, stock_code, desc, t_mm, w_mm, 
                            0, uom, "", "", "", "", 0, 0, bal, 0, 0
                        ]
                        
                        worksheet.append_row(new_row)
                        st.success(f"Success! Added {stock_code}")
                    except Exception as e:
                        st.error(f"Error: {e}")

except Exception as e:
    st.error(f"An error occurred: {e}")