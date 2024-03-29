import os
import io
import pandas as pd
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account

import gspread

from sqlalchemy import create_engine

import streamlit as st

scope = ['https://www.googleapis.com/auth/drive.readonly']
credentials = service_account.Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)

def find_file_id(q=""):
    service = build('drive', 'v3', credentials=credentials)
    files = []
    page_token = None
    while True:
        # pylint: disable=maybe-no-member
        response = service.files().list(q=q,
                                        spaces='drive',
                                        fields='nextPageToken, '
                                            'files(id, name)',
                                        pageToken=page_token).execute()
        for file in response.get('files', []):
            # Process change
            print(f'Found file: {file.get("name")}, {file.get("id")}')
        files.extend(response.get('files', []))
        page_token = response.get('nextPageToken', None)
        if page_token is None:
            break
    return files

# https://developers.google.com/drive/api/guides/manage-downloads
def download_file(file_id):
    """Downloads a file
    Args:
        real_file_id: ID of the file to download
    Returns : IO object with location.

    Load pre-authorized user credentials from the environment.
    TODO(developer) - See https://developers.google.com/identity
    for guides on implementing OAuth2 for the application.
    """
    try:
        # create drive api client
        service = build('drive', 'v3', credentials=credentials)

        request = service.files().get_media(fileId=file_id)

        file = io.BytesIO()
        downloader = MediaIoBaseDownload(file, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            print('ok')
            print(F'Download {int(status.progress() * 100)}.')

    except HttpError as error:
        print(F'An error occurred: {error}')
        file = None

    return file

def load_gsheet(file_id, sheet_name):
    gc = gspread.authorize(credentials)
    sheet = gc.open_by_key(file_id)
    worksheet = sheet.worksheet(sheet_name)
    return pd.DataFrame(worksheet.get_all_records())

def get_cockroachdb_conn(database: str): 
    # Download certificate if not already present
    certificate_path = os.path.expanduser(os.path.join('~', '.postgresql', 'root.crt'))
    if not os.path.exists(certificate_path):
        os.system(f"curl --create-dirs -o {certificate_path} -O {st.secrets['get_certificate_cockroachdb']}")

    # Edit connexion string to point to the right database
    connexion_string = st.secrets["cockroach_connexion_string"]
    connexion_string = connexion_string.replace('database_name', database)

    # Connexion to the database   
    engine = create_engine(connexion_string)
    conn = engine.connect()

    return conn

@st.cache(ttl=60*60*12)
def get_garmin_data(query):
    conn = get_cockroachdb_conn('garmin')
    df = pd.read_sql(query, conn)
    conn.close()
    return df
    

def load_css():
    return st.markdown(
        """
        <style>
        div[data-testid="metric-container"] {
        background-color: rgba(59, 151, 243, 0.05);
        border: 1px solid rgba(59, 151, 243, 0.25);
        padding: 5% 5% 5% 10%;
        border-radius: 5px;
        }

        div[data-testid="metric-container"] > div[style*="color: rgb(9, 171, 59);"] {
           overflow-wrap: break-word;
           white-space: break-spaces;
            color: #3B97F3 !important;
        }

        div[data-testid="metric-container"] > div[style*="color: rgb(255, 43, 43);"] {
           overflow-wrap: break-word;
           white-space: break-spaces;
            color: #F27716 !important;
        }

        div[data-baseweb="tab-list"] > button[data-baseweb="tab"] {
           overflow-wrap: break-word;
           white-space: break-spaces;
            color: white !important;
        }

        div[data-baseweb="tab-list"] > div[data-baseweb="tab-highlight"] {
           overflow-wrap: break-word;
           white-space: break-spaces;
           background-color: #3B97F3 !important;
        }

        # div[class*="stSelectbox"] > div[aria-expanded="trus"] > div {
        #    overflow-wrap: break-word;
        #    white-space: break-spaces;
        #    background-color: #3B97F3 !important;
        # }
        .st-dr{
            border-color: #3B97F3
        }

        </style>
        """,
        unsafe_allow_html=True
    )