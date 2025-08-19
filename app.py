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
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False
    if st.session_state.password_correct:
        return True
    with st.form("login"):
        st.title("Login")
        st.write("Please enter the password to access the application.")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Submit")
        if submitted:
            if password == st.secrets.get("password"):
                st.session_state.password_correct = True
                st.rerun()
            else:
                st.error("😕 Incorrect password")
    return False

# --- Custom CSS ---
def local_css():
    st.markdown("""
    <style>
        .stApp { background-color: #f5f5f5; }
        .header { background: linear-gradient(135deg, #2c3e50, #3498db); color: white; padding: 25px; border-radius: 8px; margin-bottom: 25px; text-align: center; }
        .header h1, .header p { margin: 0; padding: 0; }
        .stDataFrame { border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .st-emotion-cache-r421ms { border-radius: 8px; border: none; }
        .stExpander { border-radius: 8px !important; border: 1px solid #ddd !important; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .stButton>button { width: 100%; border-radius: 5px; padding: 10px 0; margin-bottom: 10px; }
        .stDownloadButton>button { background-color: #27ae60; color: white; }
        .stDownloadButton>button:hover { background-color: #229954; color: white; border-color: #27ae60; }
    </style>
    """, unsafe_allow_html=True)

# --- Data Handling Functions ---

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Verification Log')
    return output.getvalue()

def generate_pdf(project_info, df, checklist_items, notes, signatures):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)

    # Helper function to sanitize text for PDF generation
    def sanitize_text(text):
        return str(text).encode('latin-1', 'replace').decode('latin-1')

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
        pdf.cell(40, 8, sanitize_text(key) + ":", 0, 0)
        pdf.cell(0, 8, sanitize_text(value), 0, 1)
    
    # Verification Table
    pdf.ln(10)
    pdf.set_font("Helvetica", 'B', size=14)
    pdf.cell(0, 10, "Verification Entries", 0, 1, 'L')
    
    # Table Header
    pdf.set_font("Helvetica", 'B', size=8)
    col_widths = [20, 15, 25, 55, 20, 20, 20, 25]
    for i, header in enumerate(df.columns):
        pdf.cell(col_widths[i], 8, sanitize_text(header), 1, 0, 'C')
    pdf.ln()
    
    # Table Rows
    pdf.set_font("Helvetica", size=7)
    for _, row in df.iterrows():
        y_before = pdf.get_y()
        max_height = 0
        for i, item in enumerate(row):
            x_pos = pdf.get_x()
            pdf.multi_cell(col_widths[i], 8, sanitize_text(item), border=1, align='L')
            if pdf.get_y() - y_before > max_height:
                max_height = pdf.get_y() - y_before
            pdf.set_xy(x_pos + col_widths[i], y_before)
        pdf.set_y(y_before + max_height)

    # Checklist
    pdf.ln(10)
    pdf.set_font("Helvetica", 'B', size=14)
    pdf.cell(0, 10, "Verification Checklist", 0, 1, 'L')
    pdf.set_font("Helvetica", size=11)
    for item, checked in checklist_items.items():
        status = "[X]" if checked else "[ ]"
        pdf.cell(0, 8, f"{status} {sanitize_text(item)}", 0, 1)
        
    # Notes
    pdf.ln(5)
    pdf.set_font("Helvetica", 'B', size=14)
    pdf.cell(0, 10, "Overall Verification Notes", 0, 1, 'L')
    pdf.set_font("Helvetica", size=11)
    pdf.multi_cell(0, 5, sanitize_text(notes))
    
    # Signatures
    pdf.ln(10)
    pdf.set_font("Helvetica", 'B', size=14)
    pdf.cell(0, 10, "Verification Sign-off", 0, 1, 'L')
    pdf.set_font("Helvetica", size=11)
    for title, info in signatures.items():
        date_str = info['date'].strftime('%Y-%m-%d') if info['date'] else 'N/A'
        signature_line = f"{sanitize_text(title)}: {sanitize_text(info['name'])} (Date: {date_str})"
        pdf.cell(0, 8, signature_line, 0, 1)

    # *** PRIMARY FIX: Convert bytearray to bytes for Streamlit ***
    return bytes(pdf.output())

# --- Main Application Logic ---
def main_app():
    local_css()

    if 'diary_entries' not in st.session_state:
        empty_data = {
            'Diary Date': pd.Series(dtype='datetime64[ns]'),
            'Engineer': pd.Series(dtype='str'),
            'Location/BH ID': pd.Series(dtype='str'),
            'Activities Summary': pd.Series(dtype='str'),
            'Verification Status': pd.Series(dtype='str'),
            'Verified By': pd.Series(dtype='str'),
            'Verification Date': pd.Series(dtype='datetime64[ns]'),
            'Issues/Notes': pd.Series(dtype='str')
        }
        st.session_state.diary_entries = pd.DataFrame(empty_data)

    scheme_title = st.session_state.get('scheme_name', 'Site Diary Verification Log')
    st.markdown(f'<div class="header"><h1>{scheme_title}</h1><p>Site Diary Verification Log</p></div>', unsafe_allow_html=True)

    with st.container():
        st.subheader("Project Details")
        cols = st.columns(4)
        project_no = cols[0].selectbox("Project No:", options=["LT037", "LT359"], key="project_no")
        scheme_name = "Beauly to Blackhillock" if project_no == "LT037" else "Blackhillock to Peterhead"
        st.session_state['scheme_name'] = scheme_name
        cols[1].text_input("Scheme:", value=scheme_name, disabled=True)
        gi_package = cols[2].selectbox("GI Package:", options=["Package 1", "Package 2", "Package 3", "Package 4", "Package 5"], key="gi_package")
        subcontractor_map = {"Package 1": "Natural Power", "Package 2": "CGL", "Package 3": "IGNE", "Package 4": "CGL", "Package 5": "IGNE"}
        subcontractor_name = subcontractor_map.get(gi_package, "")
        cols[3].text_input("Subcontractor:", value=subcontractor_name, disabled=True)
        project_info_data = {"Project No": project_no, "Scheme": scheme_name, "GI Package": gi_package, "Subcontractor": subcontractor_name}

    st.subheader("Site Diary Verification Entries")
    edited_df = st.data_editor(
        st.session_state.diary_entries,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Diary Date": st.column_config.DateColumn("Diary Date", format="YYYY-MM-DD", required=True),
            "Verification Status": st.column_config.SelectboxColumn("Verification Status", options=["PENDING", "VERIFIED", "ISSUES FOUND"], required=True),
            "Verification Date": st.column_config.DateColumn("Verification Date", format="YYYY-MM-DD")
        },
        key="data_editor"
    )
    st.session_state.diary_entries = edited_df

    with st.expander("Show Verification Checklist & Notes", expanded=True):
        st.subheader("Verification Checklist")
        checklist_options = {
            "Time records are consistent and realistic": False, "Activities align with project schedule and scope": False,
            "Equipment lists are accurate and complete": False, "Personnel records match expected crew": False,
            "Weather conditions are appropriately recorded": False, "Safety activities (toolbox talks, briefings) are documented": False,
            "Progress notes are detailed and accurate": False, "All required signatures are present": False,
        }
        checklist_state = {}
        cols = st.columns(2)
        for i, option in enumerate(checklist_options.keys()):
            with cols[i % 2]:
                checklist_state[option] = st.checkbox(option, value=False, key=f"check_{i}")
        st.subheader("Overall Verification Notes")
        overall_notes = st.text_area("...", height=150, label_visibility="collapsed")

    with st.container():
        st.subheader("Verification Sign-off")
        st.markdown("**Site Engineer**")
        se_name = st.text_input("Print Name", key="se_name")
        se_date = st.date_input("Date", key="se_date", value=datetime.now())
        signature_data = {"Site Engineer": {"name": se_name, "date": se_date}}

    st.sidebar.title("Export Report")
    st.sidebar.info("Download a copy of the current report in your desired format.")
    df_for_download = st.session_state.diary_entries.copy()
    for col in ['Diary Date', 'Verification Date']:
        if col in df_for_download.columns and not df_for_download[col].isnull().all():
            df_for_download[col] = pd.to_datetime(df_for_download[col]).dt.strftime('%d.%m.%Y')
    
    excel_data = to_excel(df_for_download)
    st.sidebar.download_button(label="📥 Download as XLSX", data=excel_data, file_name=f"Site_Diary_Log_{datetime.now().strftime('%Y-%m-%d')}.xlsx', mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    
    pdf_data = generate_pdf(project_info_data, df_for_download, checklist_state, overall_notes, signature_data)
    st.sidebar.download_button(label="📄 Download as PDF", data=pdf_data, file_name=f"Site_Diary_Log_{datetime.now().strftime('%Y-%m-%d')}.pdf", mime="application/pdf")

# --- App Execution ---
if check_password():
    main_app()
