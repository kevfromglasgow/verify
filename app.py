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
        # Initialize with the example data from your HTML
        initial_data = {
            'Diary Date': [datetime(2025, 8, 15).date()],
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

    # Header Section
    st.markdown("""
    <div class="header">
        <h1>Site Diary Verification Log</h1>
        <p>Beauly - Peterhead Package 2 - Investigation Works</p>
    </div>
    """, unsafe_allow_html=True)

    # Project Info Section
    with st.container():
        st.subheader("Project Details")
        cols = st.columns(4)
        project_no = cols[0].text_input("Project No:", value="CGN/05281", disabled=True)
        scheme = cols[1].text_input("Scheme:", value="Beauly - Peterhead Package 2")
        verifier = cols[2].text_input("Verifier:", placeholder="Your Name")
        verification_date = cols[3].date_input("Verification Date:", value=datetime.today())

        project_info_data = {
            "Project No": project_no,
            "Scheme": scheme,
            "Verifier": verifier,
            "Verification Date": verification_date.strftime("%Y-%m-%d")
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
        sig_cols = st.columns(3)
        with sig_cols[0]:
            st.markdown("**Client Verifier**")
            client_name = st.text_input("Print Name", key="client_name")
            client_date = st.date_input("Date", key="client_date")
        with sig_cols[1]:
            st.markdown("**Project Manager**")
            pm_name = st.text_input("Print Name", key="pm_name")
            pm_date = st.date_input("Date", key="pm_date")
        with sig_cols[2]:
            st.markdown("**Senior Engineer**")
            se_name = st.text_input("Print Name", key="se_name")
            se_date = st.date_input("Date", key="se_date")

        signature_data = {
            "Client Verifier": {"name": client_name, "date": client_date},
            "Project Manager": {"name": pm_name, "date": pm_date},
            "Senior Engineer": {"name": se_name, "date": se_date}
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
