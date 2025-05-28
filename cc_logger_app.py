
import streamlit as st
import pandas as pd
from datetime import datetime
import os
import base64
import requests
from io import BytesIO

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

st.title("Collection Conveyor Tracker")

# Form grid
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

def push_to_github(df, filename):
    # Create Excel file in memory
    excel_buffer = BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name="Log")
    excel_content = excel_buffer.getvalue()
    b64_content = base64.b64encode(excel_content).decode()

    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{filename}"

    # Check if file exists
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }
    get_resp = requests.get(url, headers=headers)
    if get_resp.status_code == 200:
        sha = get_resp.json()["sha"]
    else:
        sha = None

    payload = {
        "message": f"Update log for {filename}",
        "content": b64_content,
        "branch": "main"
    }
    if sha:
        payload["sha"] = sha

    resp = requests.put(url, headers=headers, json=payload)
    return resp.status_code, resp.json()

# Save to GitHub button
if st.button("Save and Push to GitHub"):
    today_file = f"CC_Log_{datetime.now().strftime('%Y-%m-%d')}.xlsx"
    status, response = push_to_github(edited_df, today_file)

    if status in [200, 201]:
        st.success(f"✅ Successfully pushed {today_file} to GitHub.")
    else:
        st.error(f"❌ Failed to push file. {response}")
