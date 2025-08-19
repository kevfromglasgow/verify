import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
from fpdf import FPDF

# --- Page Configuration ---
st.set_page_config(
    page_title="Site Diary Verification Log",
    layout="wide",
    initial_sidebar_state="collapsed" # Start with sidebar collapsed
)

# --- Password Protection ---
def check_password():
    """Returns `True` if the user had the correct password."""

    # Use a session state variable to track password correctness
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False

    # If the password is correct, we're done
    if st.session_state.password_correct:
        return True

    # Show a login form
    with st.form("login"):
        st.title("Login")
        st.write("Please enter the password to access the application.")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Submit")

        if submitted:
            # Check if the entered password matches the one in secrets
            if password == st.secrets.get("password"):
                st.session_state.password_correct = True
                st.rerun()  # Rerun the app to show the main content
            else:
                st.error("😕 Incorrect password")
    
    return False

# --- Custom CSS to replicate your HTML style ---
def local_css():
    st.markdown("""
    <style>
        /* Main body and headers */
        .stApp {
            background-color: #f5f5f5;
        }
        .header {
            background: linear-gradient(135deg, #2c3e50, #3498db);
            color: white;
            padding: 25px;
            border-radius: 8px;
            margin-bottom: 25px;
            text-align: center;
        }
        .header h1, .header p {
            margin: 0;
            padding: 0;
        }
        
        /* Data editor table styling */
        .stDataFrame {
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        /* Styling for containers and expanders */
        .st-emotion-cache-r421ms { /* Main block container */
            border-radius: 8px;
            border: none;
        }
        .stExpander {
            border-radius: 8px !important;
            border: 1px solid #ddd !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        /* Button styling in sidebar */
        .stButton>button {
            width: 100%;
            border-radius: 5px;
            padding: 10px 0;
            margin-bottom: 10px;
        }
        .stDownloadButton>button {
            background-color: #27ae60;
            color: white;
        }
        .stDownloadButton>button:hover {
            background-color: #229954;
            color: white;
            border-color: #27ae60;
        }
    </style>
    """, unsafe_allow_html=True)

# --- Data Handling Functions ---

# Function to convert DataFrame to Excel in memory
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Verification Log')
    processed_data = output.getvalue()
    return processed_data

# Function to generate a PDF report from the current data
def generate_pdf(project_info, df, checklist_items, notes, signatures):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)

    # Header
    pdf.set_fill_color(44, 62, 80)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 15, "Site Diary Verification Log", 1, 1, 'C', 1)
    pdf.set_text_color(0, 0, 0)
    
    # Project Info
    pdf.ln(10)
    pdf.set_font("Helvetica", 'B', size=14)
    pdf.cell(0, 10, "Project Information", 0, 1, 'L')
    pdf.set_font("Helvetica", size=11)
    for key, value in project_info.items():
        pdf.cell(40, 8, f"{key}:", 0, 0)
        pdf.cell(0, 8, str(value), 0, 1)
    
    # Verification Table
    pdf.ln(10)
    pdf.set_font("Helvetica", 'B', size=14)
    pdf.cell(0, 10, "Verification Entries", 0, 1, 'L')
    
    # Table Header
    pdf.set_font("Helvetica", 'B', size=8)
    col_widths = [20, 15, 25, 55, 20, 20, 20, 25] # Approximate widths
    for i, header in enumerate(df.columns):
        pdf.cell(col_widths[i], 8, header, 1, 0, 'C')
    pdf.ln()
    
    # Table Rows
    pdf.set_font("Helvetica", size=7)
    for index, row in df.iterrows():
        for i, item in enumerate(row):
             pdf.cell(col_widths[i], 8, str(item), 1, 0)
        pdf.ln()

    # Checklist
    pdf.ln(10)
    pdf.set_font("Helvetica", 'B', size=14)
    pdf.cell(0, 10, "Verification Checklist", 0, 1, 'L')
    pdf.set_font("Helvetica", size=11)
    for item, checked in checklist_items.items():
        status = "[X]" if checked else "[ ]"
        pdf.cell(0, 8, f"{status} {item}", 0, 1)
        
    # Notes
    pdf.ln(5)
    pdf.set_font("Helvetica", 'B', size=14)
    pdf.cell(0, 10, "Overall Verification Notes", 0, 1, 'L')
    pdf.set_font("Helvetica", size=11)
    pdf.multi_cell(0, 5, notes)
    
    # Signatures
    pdf.ln(10)
    pdf.set_font("Helvetica", 'B', size=14)
    pdf.cell(0, 10, "Verification Sign-off", 0, 1, 'L')
    pdf.set_font("Helvetica", size=11)
    for title, info in signatures.items():
        pdf.cell(0, 8, f"{title}: {info['name']} (Date: {info['date'].strftime('%Y-%m-%d') if info['date'] else 'N/A'})", 0, 1)

    return pdf.output(dest='S').encode('latin-1')

# --- Main Application Logic ---
def main_app():
    # Apply custom CSS
    local_css()

    # --- Session State Initialization ---
    if 'diary_entries' not in st.session_state:
        # Initialize with the example data
        initial_data = {
            'Diary Date': [datetime(2025, 8, 19).date()],
            'Engineer': ['FS'],
            'Location/BH ID': ['CB5-22'],
            'Activities Summary': ['Drilling 14.5m-20.5m, BH completion, install/backfill activities'],
            'Verification Status': ['VERIFIED'],
            'Verified By': [''],
            'Verification Date': [None],
            'Issues/Notes': ['']
        }
        st.session_state.diary_entries = pd.DataFrame(initial_data)

    # --- App Layout ---

    # Get the project title from session state to display in the header, default if not set
    scheme_title = st.session_state.get('scheme_name', 'Site Diary Verification Log')
    
    # Header Section
    st.markdown(f"""
    <div class="header">
        <h1>{scheme_title}</h1>
        <p>Site Diary Verification Log</p>
    </div>
    """, unsafe_allow_html=True)

    # Project Info Section
    with st.container():
        st.subheader("Project Details")
        cols = st.columns(4)

        # Column 1: Project Number Dropdown
        project_no = cols[0].selectbox(
            "Project No:",
            options=["LT037", "LT359"],
            key="project_no"
        )

        # Column 2: Scheme (updates based on Project No)
        scheme_name = "Beauly to Blackhillock" if project_no == "LT037" else "Blackhillock to Peterhead"
        st.session_state['scheme_name'] = scheme_name # Store in session state for header
        cols[1].text_input("Scheme:", value=scheme_name, disabled=True)
        
        # Column 3: GI Package Dropdown
        gi_package = cols[2].selectbox(
            "GI Package:",
            options=["Package 1", "Package 2", "Package 3", "Package 4", "Package 5"],
            key="gi_package"
        )
        
        # Column 4: Subcontractor (updates based on GI Package)
        subcontractor_map = {
            "Package 1": "Natural Power",
            "Package 2": "CGL",
            "Package 3": "IGNE",
            "Package 4": "CGL",
            "Package 5": "IGNE"
        }
        subcontractor_name = subcontractor_map.get(gi_package, "")
        cols[3].text_input("Subcontractor:", value=subcontractor_name, disabled=True)

        project_info_data = {
            "Project No": project_no,
            "Scheme": scheme_name,
            "GI Package": gi_package,
            "Subcontractor": subcontractor_name
        }


    # Verification Table Section
    st.subheader("Site Diary Verification Entries")

    # Use st.data_editor to make the dataframe interactive
    edited_df = st.data_editor(
        st.session_state.diary_entries,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Diary Date": st.column_config.DateColumn(
                "Diary Date",
                format="DD.MM.YYYY",
                required=True
            ),
            "Verification Status": st.column_config.SelectboxColumn(
                "Verification Status",
                options=["PENDING", "VERIFIED", "ISSUES FOUND"],
                required=True
            ),
            "Verification Date": st.column_config.DateColumn(
                "Verification Date",
                format="DD.MM.YYYY"
            )
        },
        key="data_editor"
    )
    st.session_state.diary_entries = edited_df


    # Checklist and Notes Section
    with st.expander("Show Verification Checklist & Notes", expanded=True):
        st.subheader("Verification Checklist")
        
        checklist_options = {
            "Time records are consistent and realistic": False,
            "Activities align with project schedule and scope": False,
            "Equipment lists are accurate and complete": False,
            "Personnel records match expected crew": False,
            "Weather conditions are appropriately recorded": False,
            "Safety activities (toolbox talks, briefings) are documented": False,
            "Progress notes are detailed and accurate": False,
            "All required signatures are present": False,
        }
        
        checklist_state = {}
        cols = st.columns(2)
        i = 0
        for option, default_val in checklist_options.items():
            with cols[i % 2]:
                checklist_state[option] = st.checkbox(option, value=default_val, key=f"check_{i}")
            i += 1

        st.subheader("Overall Verification Notes")
        overall_notes = st.text_area(
            "Enter any overall comments about the diary accuracy, discrepancies found, or additional observations...",
            height=150,
            label_visibility="collapsed"
        )

    # Signature Section
    with st.container():
        st.subheader("Verification Sign-off")
        st.markdown("**Site Engineer**")
        se_name = st.text_input("Print Name", key="se_name")
        se_date = st.date_input("Date", key="se_date")

        signature_data = {
            "Site Engineer": {"name": se_name, "date": se_date}
        }

    # --- Sidebar for Downloads ---
    st.sidebar.title("Export Report")
    st.sidebar.info("Download a copy of the current report in your desired format.")

    # Prepare data for download
    df_for_download = st.session_state.diary_entries.copy()
    # Format dates as strings for cleaner export
    for col in ['Diary Date', 'Verification Date']:
        if col in df_for_download.columns:
            df_for_download[col] = pd.to_datetime(df_for_download[col]).dt.strftime('%d.%m.%Y')

    # XLSX Download Button
    excel_data = to_excel(df_for_download)
    st.sidebar.download_button(
        label="📥 Download as XLSX",
        data=excel_data,
        file_name=f"Site_Diary_Log_{datetime.now().strftime('%Y-%m-%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    # PDF Download Button
    pdf_data = generate_pdf(project_info_data, df_for_download, checklist_state, overall_notes, signature_data)
    st.sidebar.download_button(
        label="📄 Download as PDF",
        data=pdf_data,
        file_name=f"Site_Diary_Log_{datetime.now().strftime('%Y-%m-%d')}.pdf",
        mime="application/pdf",
    )

# --- App Execution ---
if check_password():
    main_app()
