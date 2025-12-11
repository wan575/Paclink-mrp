import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- CONFIGURATION ---
CREDS_FILE = "service_account.json" 
SHEET_NAME = "Storage Control System Ver 2.0"  
TAB_NAME = "MRP_Data"

# --- SETUP CONNECTION ---
def get_database_connection():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, scope)
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
        st.info(f"Connected to: {SHEET_NAME}")
        st.write("Welcome to your MRP system.")

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

            # Filter Logic (for viewing only)
            if search_term:
                st.info("⚠️ Editing is disabled while searching. Clear search to edit.")
                mask = df.astype(str).apply(lambda x: x.str.contains(search_term, case=False)).any(axis=1)
                st.dataframe(df[mask], use_container_width=True)
            else:
                # --- EDITABLE TABLE ---
                # This makes the table interactive!
                edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)

                # Save Button
                if not edited_df.equals(df):
                    st.write("Changes detected!")
                    if st.button("💾 Save Changes to Google Sheet"):
                        try:
                            worksheet.clear()
                            # Re-insert headers and data
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
                        # Auto-calculate the next S/N
                        existing_data = worksheet.get_all_values()
                        next_sn = len(existing_data) # Simple logic: Row count
                        
                        # PREPARE THE ROW (Must match your 18 columns exactly)
                        # 1.S/N, 2.Group, 3.CAT, 4.StockCode, 5.Description, 6.T, 7.W, 8.L, 9.UOM
                        # 10.Customer, 11.Sup, 12.Code, 13.Unit UOM, 14.In, 15.Out, 16.Bal, 17.Std, 18.Loose
                        
                        new_row = [
                            next_sn,     # 1. S/N
                            group,       # 2. Group
                            cat,         # 3. CAT
                            stock_code,  # 4. StockCode
                            desc,        # 5. Description
                            t_mm,        # 6. T(mm)
                            w_mm,        # 7. W(mm)
                            0,           # 8. L(M) - default 0
                            uom,         # 9. UOM
                            "",          # 10. Customer - default blank
                            "",          # 11. Sup - default blank
                            "",          # 12. Code - default blank
                            "",          # 13. Unit UOM - default blank
                            0,           # 14. In - default 0
                            0,           # 15. Out - default 0
                            bal,         # 16. Bal
                            0,           # 17. Bal in Standard - default 0
                            0            # 18. Bal in Loose - default 0
                        ]
                        
                        worksheet.append_row(new_row)
                        st.success(f"Success! Added {stock_code} (S/N {next_sn})")
                    except Exception as e:
                        st.error(f"Error: {e}")

except Exception as e:
    st.error(f"An error occurred: {e}")