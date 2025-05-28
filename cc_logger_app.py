
import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
import base64
import requests
from openpyxl import load_workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.styles import Font
from openpyxl.worksheet.table import Table, TableStyleInfo

# Dropdown options
options = ["", "Tracked", "Needs Tracked", "Pulley Noise", "Inspected"]
cc_list = [f"CC{i}" for i in range(1, 78)]

# Initialize session state
if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame({
        "CC#": cc_list,
        "(A)-1": ["" for _ in cc_list],
        "2": ["" for _ in cc_list],
        "3": ["" for _ in cc_list],
        "4-(B)": ["" for _ in cc_list],
        "COMMENTS": ["" for _ in cc_list],
    })

st.title("Collection Conveyor Tracker – Indy")

edited_df = st.session_state.df.copy()
for i, cc in enumerate(cc_list):
    col1, col2, col3, col4, col5, col6 = st.columns([1.2, 1, 1, 1, 1, 2])
    col1.write(cc)
    edited_df.at[i, "(A)-1"] = col2.selectbox("", options, index=options.index(edited_df.at[i, "(A)-1"]), key=f"{cc}_b")
    edited_df.at[i, "2"] = col3.selectbox("", options, index=options.index(edited_df.at[i, "2"]), key=f"{cc}_c")
    edited_df.at[i, "3"] = col4.selectbox("", options, index=options.index(edited_df.at[i, "3"]), key=f"{cc}_d")
    edited_df.at[i, "4-(B)"] = col5.selectbox("", options, index=options.index(edited_df.at[i, "4-(B)"]), key=f"{cc}_e")
    edited_df.at[i, "COMMENTS"] = col6.text_input("", value=edited_df.at[i, "COMMENTS"], key=f"{cc}_f")

# GitHub credentials
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
REPO_OWNER = st.secrets["REPO_OWNER"]
REPO_NAME = st.secrets["REPO_NAME"]

GITHUB_FILE = "CC Inspection Indy.xlsx"

def auto_format_worksheet(ws, df):
    # Apply table formatting and column width auto-sizing
    tab = Table(displayName="InspectionLog", ref=ws.dimensions)
    style = TableStyleInfo(name="TableStyleMedium9", showRowStripes=True, showColumnStripes=False)
    tab.tableStyleInfo = style
    ws.add_table(tab)
    for col in ws.columns:
        max_length = max(len(str(cell.value)) if cell.value is not None else 0 for cell in col)
        ws.column_dimensions[col[0].column_letter].width = max_length + 2

def get_github_file():
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{GITHUB_FILE}"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        content = base64.b64decode(resp.json()["content"])
        sha = resp.json()["sha"]
        return BytesIO(content), sha
    return None, None

def push_to_github(updated_buffer, sha=None):
    b64_content = base64.b64encode(updated_buffer.getvalue()).decode()
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{GITHUB_FILE}"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }
    payload = {
        "message": f"Update sheet for {datetime.now().date()}",
        "content": b64_content,
        "branch": "main"
    }
    if sha:
        payload["sha"] = sha
    response = requests.put(url, headers=headers, json=payload)
    return response.status_code, response.json()

def save_and_upload_to_github(df):
    today = datetime.now().strftime("%Y-%m-%d")
    buffer = BytesIO()
    existing_file, sha = get_github_file()

    if existing_file:
        book = load_workbook(existing_file)
    else:
        from openpyxl import Workbook
        book = Workbook()
        book.remove(book.active)

    if today in book.sheetnames:
        del book[today]
    sheet = book.create_sheet(title=today)
    for r in dataframe_to_rows(df, index=False, header=True):
        sheet.append(r)
    auto_format_worksheet(sheet, df)
    book.save(buffer)
    buffer.seek(0)
    return push_to_github(buffer, sha), buffer

# GitHub Push Button
if st.button("Save to GitHub"):
    (status, response), out_buffer = save_and_upload_to_github(edited_df)
    if status in [200, 201]:
        st.success("✅ Workbook updated on GitHub!")
        st.download_button("📥 Download This Version", out_buffer, file_name="CC Inspection Indy.xlsx")
    else:
        st.error(f"❌ Failed to upload: {response}")
