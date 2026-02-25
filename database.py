import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

@st.cache_resource
def connect_to_sheets():
    scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    credentials = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]),
        scopes=scopes
    )
    client = gspread.authorize(credentials)
    return client.open("Semear Mentoria")

@st.cache_data(ttl=600)
def fetch_sheet_data("Semear Mentoria"):
    sh = connect_to_sheets()
    worksheet = sh.worksheet("Semear Mentoria")
    raw_data = worksheet.get_all_values()
    
    if not raw_data:
        return pd.DataFrame()
        
    headers = [h.strip() for h in raw_data[0]]
    return pd.DataFrame(raw_data[1:], columns=headers)
