import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
from fpdf import FPDF
import json
import glob
import os

# --- Page Configuration ---
st.set_page_config(
    page_title="Daily Site Diary",
    layout="wide",
    initial_sidebar_state="expanded"
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
        .st-emotion-cache-r421ms { border-radius: 8px; border: none; }
        .stExpander { border-radius: 8px !important; border: 1px solid #ddd !important; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .stButton>button { width: 100%; border-radius: 5px; padding: 10px 0; margin-bottom: 10px; }
        .stDownloadButton>button { background-color: #27ae60; color: white; }
        .stDownloadButton>button:hover { background-color: #229954; color: white; border-color: #27ae60; }
    </style>
    """, unsafe_allow_html=True)

# --- Data Handling Functions ---
def get_name_from_filename(filename):
    if filename:
        return os.path.splitext(os.path.basename(filename))[0].split('_', 1)[-1]
    return ""

def to_excel(daily_data):
    df = pd.DataFrame([daily_data])
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name=daily_data.get('Diary Date', 'Report'))
    return output.getvalue()

def generate_pdf(project_info, daily_data, checklist_items, notes, signatures):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    def sanitize_text(text):
        return str(text).encode('latin-1', 'replace').decode('latin-1')

    pdf.set_fill_color(44, 62, 80)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 15, "Daily Site Diary Verification Report", 1, 1, 'C', 1)
    pdf.set_text_color(0, 0, 0)
    
    pdf.ln(8)
    pdf.set_font("Helvetica", 'B', size=14)
    pdf.cell(0, 10, "Project Information", 0, 1, 'L')
    pdf.set_font("Helvetica", size=11)
    for key, value in project_info.items():
        pdf.cell(40, 8, sanitize_text(key) + ":", 0, 0)
        pdf.cell(0, 8, sanitize_text(value), 0, 1)

    pdf.ln(8)
    pdf.set_font("Helvetica", 'B', size=14)
    pdf.cell(0, 10, "Daily Entry Details", 0, 1, 'L')
    
    # --- FIX for FPDFException ---
    # This block now properly handles the layout for multi-line values.
    for key, value in daily_data.items():
        y_before = pdf.get_y()
        pdf.set_font("Helvetica", 'B', size=11)
        pdf.multi_cell(45, 8, sanitize_text(key) + ":", align='L')
        
        pdf.set_xy(pdf.l_margin + 45, y_before)
        
        pdf.set_font("Helvetica", '', size=11)
        pdf.multi_cell(0, 8, sanitize_text(value), align='L')
    # --- END FIX ---
    
    pdf.ln(8)
    pdf.set_font("Helvetica", 'B', size=14)
    pdf.cell(0, 10, "Verification Checklist", 0, 1, 'L')
    pdf.set_font("Helvetica", size=11)
    for item, checked in checklist_items.items():
        status = "[X]" if checked else "[ ]"
        pdf.cell(0, 8, f"{status} {sanitize_text(item)}", 0, 1)
    
    pdf.ln(5)
    pdf.set_font("Helvetica", 'B', size=14)
    pdf.cell(0, 10, "Overall Verification Notes", 0, 1, 'L')
    pdf.set_font("Helvetica", size=11)
    pdf.multi_cell(0, 5, sanitize_text(notes))
    
    pdf.ln(10)
    pdf.set_font("Helvetica", 'B', size=14)
    pdf.cell(0, 10, "Verification Sign-off", 0, 1, 'L')
    pdf.set_font("Helvetica", size=11)
    for title, info in signatures.items():
        date_str = info['date'] if isinstance(info['date'], str) else info['date'].strftime('%Y-%m-%d')
        signature_line = f"{sanitize_text(title)}: {sanitize_text(info['name'])} (Date: {date_str})"
        pdf.cell(0, 8, signature_line, 0, 1)
        
    return bytes(pdf.output())

# --- Main Application Logic ---
def main_app():
    local_css()

    if 'app_loaded' not in st.session_state:
        st.session_state.daily_entry = {
            "Diary Date": datetime.now().date(), "Engineer": "", "Location/BH ID": "", "Activities Summary": "",
            "Verification Status": "PENDING", "Verified By": "", "Verification Date": datetime.now().date(), "Issues/Notes": ""
        }
        st.session_state.checklist_state = {key: False for key in ["Time records are consistent and realistic", "Activities align with project schedule and scope", "Equipment lists are accurate and complete", "Personnel records match expected crew", "Weather conditions are appropriately recorded", "Safety activities (toolbox talks, briefings) are documented", "Progress notes are detailed and accurate", "All required signatures are present"]}
        st.session_state.overall_notes = ""
        st.session_state.se_name = ""
        st.session_state.se_date = datetime.now().date()
        st.session_state.app_loaded = True

    with st.sidebar:
        st.title("Actions")
        st.header("Save & Load Report")
        
        saved_files = sorted(glob.glob("*.json"), reverse=True)
        if saved_files:
            selected_file_to_load = st.selectbox("Select a report to load:", [""] + saved_files, key="load_selector")
            if st.button("Load Selected Report"):
                with open(selected_file_to_load, 'r') as f:
                    state = json.load(f)
                    
                    # --- FIX for KeyError ---
                    # Safely get the data, show error if it's an old format
                    daily_entry_data = state.get('daily_entry')
                    if daily_entry_data is None:
                        st.error(f"Error: '{selected_file_to_load}' is an old, incompatible file format. Please delete it and create a new report.")
                    else:
                        st.session_state.daily_entry = daily_entry_data
                        st.session_state.daily_entry['Diary Date'] = datetime.strptime(st.session_state.daily_entry['Diary Date'], '%Y-%m-%d').date()
                        st.session_state.daily_entry['Verification Date'] = datetime.strptime(st.session_state.daily_entry['Verification Date'], '%Y-%m-%d').date()
                        st.session_state.checklist_state = state['checklist_state']
                        st.session_state.overall_notes = state['overall_notes']
                        st.session_state.se_name = get_name_from_filename(selected_file_to_load)
                        st.session_state.se_date = datetime.strptime(state['signature_data']['Site Engineer']['date'], '%Y-%m-%d').date()
                        st.session_state.project_no = state['project_info']['Project No']
                        st.session_state.gi_package = state['project_info']['GI Package']
                        st.success(f"Successfully loaded '{selected_file_to_load}'")
                        st.rerun()

        diary_date_str = st.session_state.daily_entry['Diary Date'].strftime('%Y-%m-%d')
        file_to_save = st.text_input("Enter your name to save file:", f"{st.session_state.se_name or 'Your Name'}")
        
        if st.button("Save Current Report"):
            verifier_name = file_to_save.strip()
            if verifier_name and verifier_name != "Your Name":
                st.session_state.se_name = verifier_name
                if not st.session_state.daily_entry['Engineer']: st.session_state.daily_entry['Engineer'] = verifier_name
                if not st.session_state.daily_entry['Verified By']: st.session_state.daily_entry['Verified By'] = verifier_name
                entry_to_save = st.session_state.daily_entry.copy()
                entry_to_save['Diary Date'] = entry_to_save['Diary Date'].strftime('%Y-%m-%d')
                entry_to_save['Verification Date'] = entry_to_save['Verification Date'].strftime('%Y-%m-%d')
                project_info_data = {"Project No": st.session_state.project_no, "Scheme": st.session_state.scheme_name, "GI Package": st.session_state.gi_package, "Subcontractor": st.session_state.subcontractor_name}
                signature_data = {"Site Engineer": {"name": st.session_state.se_name, "date": st.session_state.se_date.strftime('%Y-%m-%d')}}
                current_state = {
                    'project_info': project_info_data, 'daily_entry': entry_to_save,
                    'checklist_state': st.session_state.checklist_state, 'overall_notes': st.session_state.overall_notes,
                    'signature_data': signature_data
                }
                final_filename = f"{diary_date_str}_{verifier_name}.json"
                with open(final_filename, 'w') as f:
                    json.dump(current_state, f, indent=4)
                st.success(f"Report saved as '{final_filename}'")
                st.rerun()
            else:
                st.warning("Please enter a valid name in the filename box before saving.")

        st.divider()
        st.header("Export Report")
        
        final_project_info = {"Project No": st.session_state.get('project_no'), "Scheme": st.session_state.get('scheme_name'), "GI Package": st.session_state.get('gi_package'), "Subcontractor": st.session_state.get('subcontractor_name')}
        final_signature_data = {"Site Engineer": {"name": st.session_state.get('se_name'), "date": st.session_state.get('se_date')}}
        export_daily_data = st.session_state.daily_entry.copy()
        export_daily_data['Diary Date'] = export_daily_data['Diary Date'].strftime('%d.%m.%Y')
        export_daily_data['Verification Date'] = export_daily_data['Verification Date'].strftime('%d.%m.%Y')
        excel_data = to_excel(export_daily_data)
        st.download_button(label="📥 Download as XLSX", data=excel_data, file_name=f"Daily_Report_{diary_date_str}.xlsx", mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        pdf_data = generate_pdf(final_project_info, export_daily_data, st.session_state.checklist_state, st.session_state.overall_notes, final_signature_data)
        st.download_button(label="📄 Download as PDF", data=pdf_data, file_name=f"Daily_Report_{diary_date_str}.pdf", mime="application/pdf")

    # --- MAIN PAGE LAYOUT ---
    scheme_title = st.session_state.get('scheme_name', 'Site Diary Verification Log')
    st.markdown(f'<div class="header"><h1>{scheme_title}</h1><p>Daily Site Diary</p></div>', unsafe_allow_html=True)

    with st.container(border=True):
        st.subheader("Project Details")
        cols = st.columns(4)
        st.session_state.project_no = cols[0].selectbox("Project No:", options=["LT037", "LT359"], key="project_no_select")
        scheme_name = "Beauly to Blackhillock" if st.session_state.project_no == "LT037" else "Blackhillock to Peterhead"
        st.session_state.scheme_name = scheme_name
        cols[1].text_input("Scheme:", value=scheme_name, disabled=True)
        st.session_state.gi_package = cols[2].selectbox("GI Package:", options=["Package 1", "Package 2", "Package 3", "Package 4", "Package 5"], key="gi_package_select")
        subcontractor_map = {"Package 1": "Natural Power", "Package 2": "CGL", "Package 3": "IGNE", "Package 4": "CGL", "Package 5": "IGNE"}
        subcontractor_name = subcontractor_map.get(st.session_state.gi_package, "")
        st.session_state.subcontractor_name = subcontractor_name
        cols[3].text_input("Subcontractor:", value=subcontractor_name, disabled=True)

    with st.container(border=True):
        st.subheader("Daily Diary Details")
        c1, c2 = st.columns(2)
        st.session_state.daily_entry['Diary Date'] = c1.date_input("Diary Date", value=st.session_state.daily_entry['Diary Date'])
        st.session_state.daily_entry['Engineer'] = c2.text_input("Engineer", value=st.session_state.daily_entry['Engineer'])
        st.session_state.daily_entry['Location/BH ID'] = c1.text_input("Location/BH ID", value=st.session_state.daily_entry['Location/BH ID'])
        st.session_state.daily_entry['Verification Status'] = c2.selectbox("Verification Status", ["PENDING", "VERIFIED", "ISSUES FOUND"], index=["PENDING", "VERIFIED", "ISSUES FOUND"].index(st.session_state.daily_entry['Verification Status']))
        st.session_state.daily_entry['Activities Summary'] = st.text_area("Activities Summary", value=st.session_state.daily_entry['Activities Summary'], height=150)
        
    with st.expander("Show Verification Details & Checklist", expanded=True):
        st.subheader("Verification Details")
        vc1, vc2 = st.columns(2)
        st.session_state.daily_entry['Verified By'] = vc1.text_input("Verified By", value=st.session_state.daily_entry['Verified By'])
        st.session_state.daily_entry['Verification Date'] = vc2.date_input("Verification Date", value=st.session_state.daily_entry['Verification Date'])
        st.session_state.daily_entry['Issues/Notes'] = st.text_area("Issues/Notes for this Entry", value=.session_state.daily_entry['Issues/Notes'])
        st.subheader("Verification Checklist")
        cols = st.columns(2)
        for i, option in enumerate(st.session_state.checklist_state.keys()):
            with cols[i % 2]:
                st.session_state.checklist_state[option] = st.checkbox(option, value=st.session_state.checklist_state[option], key=f"check_{i}")
        st.subheader("Overall Verification Notes")
        st.session_state.overall_notes = st.text_area("...", value=st.session_state.overall_notes, height=150, label_visibility="collapsed", key="notes_area")

    with st.container(border=True):
        st.subheader("Verification Sign-off")
        st.markdown("**Site Engineer**")
        st.session_state.se_name = st.text_input("Print Name", value=st.session_state.se_name, key="se_name_input")
        st.session_state.se_date = st.date_input("Date", value=st.session_state.se_date, key="se_date_input")

# --- App Execution ---
if check_password():
    main_app()
