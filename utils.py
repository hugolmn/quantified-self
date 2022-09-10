import os
import io

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account

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

        # pylint: disable=maybe-no-member
        request = service.files().get_media(fileId=file_id)
        file = io.BytesIO()
        downloader = MediaIoBaseDownload(file, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            print(F'Download {int(status.progress() * 100)}.')

    except HttpError as error:
        print(F'An error occurred: {error}')
        file = None

    return file

def get_cockroachdb_conn(database: str):
    # Download certificate if not already present
    certificate_path = os.path.expanduser('~/.postgresql/root.crt')
    if not os.path.exists(certificate_path):
        os.system(f"curl --create-dirs -o ~/.postgresql/root.crt -O {st.secrets['get_certificate_cockroachdb']}")

    # Edit connexion string to point to the right database
    connexion_string = st.secrets["cockroach_connexion_string"]
    connexion_string = connexion_string.replace('database_name', database)

    # Connexion to the database   
    engine = create_engine(connexion_string)
    conn = engine.connect()

    return conn