
import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
import base64
import requests
from openpyxl import load_workbook
from openpyxl.worksheet.table import Table, TableStyleInfo

st.set_page_config(page_title="CC Tracker – Indy", layout="wide")

# Simple login system
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔐 Login Required")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username == "maint" and password == "mars":
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect username or password.")
    st.stop()

# Main App starts after login
options = ["", "Tracked", "Needs Tracked", "Pulley Noise", "Inspected"]
cc_list = [f"CC{i}" for i in range(1, 78)]

if "form_data" not in st.session_state:
    st.session_state.form_data = {}

st.title("Collection Conveyor Tracker – Indy")

for cc in cc_list:
    with st.container():
        st.subheader(cc)
        col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 3])
        with col1:
            a1 = st.selectbox("(A)-1", options, key=f"{cc}-a1")
        with col2:
            b2 = st.selectbox("2", options, key=f"{cc}-2")
        with col3:
            b3 = st.selectbox("3", options, key=f"{cc}-3")
        with col4:
            b4 = st.selectbox("4-(B)", options, key=f"{cc}-4")
        with col5:
            comment = st.text_input("COMMENTS", key=f"{cc}-comment")
        st.session_state.form_data[cc] = [a1, b2, b3, b4, comment]

# GitHub secrets
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO_OWNER = st.secrets["REPO_OWNER"]
REPO_NAME = st.secrets["REPO_NAME"]
GITHUB_FILE = "CC Inspection Indy.xlsx"

def auto_format_worksheet(ws):
    tab = Table(displayName="InspectionLog", ref=ws.dimensions)
    style = TableStyleInfo(name="TableStyleMedium9", showRowStripes=True)
    tab.tableStyleInfo = style
    ws.add_table(tab)
    for col in ws.columns:
        max_len = max(len(str(c.value)) if c.value else 0 for c in col)
        ws.column_dimensions[col[0].column_letter].width = max_len + 2

def get_github_file():
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{GITHUB_FILE}"
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github+json"}
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        content = base64.b64decode(resp.json()["content"])
        sha = resp.json()["sha"]
        return BytesIO(content), sha
    return None, None

def push_to_github(buf, sha=None):
    b64 = base64.b64encode(buf.getvalue()).decode()
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{GITHUB_FILE}"
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}", "Accept": "application/vnd.github+json"}
    payload = {
        "message": f"Update sheet for {datetime.now().date()}",
        "content": b64,
        "branch": "main"
    }
    if sha:
        payload["sha"] = sha
    return requests.put(url, headers=headers, json=payload)

def save_and_upload():
    today = datetime.now().strftime("%Y-%m-%d")
    buf = BytesIO()
    file, sha = get_github_file()
    if file:
        book = load_workbook(file)
    else:
        from openpyxl import Workbook
        book = Workbook()
        book.remove(book.active)
    if today in book.sheetnames:
        del book[today]
    ws = book.create_sheet(title=today)
    ws.append(["CC#", "(A)-1", "2", "3", "4-(B)", "COMMENTS"])
    for cc in cc_list:
        ws.append([cc] + st.session_state.form_data[cc])
    auto_format_worksheet(ws)
    book.save(buf)
    buf.seek(0)
    return push_to_github(buf, sha), buf

if st.button("Save to GitHub"):
    resp, out_buf = save_and_upload()
    if resp.status_code in [200, 201]:
        st.success("✅ Workbook updated on GitHub!")
        st.session_state.download_buffer = out_buf
    else:
        st.error(f"❌ Failed to upload: {resp.json()}")
        st.session_state.download_buffer = None

# Always visible download
if "download_buffer" not in st.session_state:
    _, out_buf = save_and_upload()
    st.session_state.download_buffer = out_buf

st.download_button("📥 Download Current Workbook", st.session_state.download_buffer, file_name="CC Inspection Indy.xlsx")
