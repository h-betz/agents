import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

BASE_URL = "https://docs.googleapis.com"


class GoogleDocsManager:

    def __init__(self):
        self.service = None

    def __enter__(self):
        creds = None
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "credentials.json", SCOPES
                )
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open("token.json", "w") as token:
                token.write(creds.to_json())

        self.service = build("docs", "v1", credentials=creds)
        return self.service

    def __exit__(self, exc_type, exc_value, traceback):
        print("Exiting context for Google Docs service")
        # Perform teardown actions, e.g., close a file, release a lock
        if exc_type:
            print(f"An exception occurred: {exc_value}")
        return False  # Do not suppress exceptions


def __format_file_content__(file_content):
    """
        Docstring for __format_file_content__

        :param file_content: Description
        :example
        file_content = {
        "sections": [
            {"text": "Hello, Google Docs API!", "style": "paragraph"},
            {"text": "First item", "style": "bullet"},
            {"text": "Second item", "style": "bullet"},
            {"text": "Step 1", "style": "numbered"},
            {"text": "Step 2", "style": "numbered"}
        ]
    }
    """
    requests = []
    current_idx = 1

    # Step 1: Build all text insertion requests and track indices
    # Store (start_index, end_index, style) for each section
    text_ranges = []

    for section in file_content.get("sections"):
        text = section.get("text", "")
        style = section.get("style", "paragraph")

        # Add newline after each section (except we'll add it before for simplicity)
        if requests:  # Not the first section
            text = "\n" + text

        # Insert text request
        requests.append(
            {"insertText": {"location": {"index": current_idx}, "text": text}}
        )

        # Track the range for this section (for formatting)
        start_index = current_idx
        end_index = current_idx + len(text)
        text_ranges.append((start_index, end_index, style))

        # Move index forward
        current_idx = end_index

    # Step 2: Apply formatting to the text ranges
    for start_index, end_index, style in text_ranges:
        if style == "bullet":
            requests.append(
                {
                    "createParagraphBullets": {
                        "range": {"startIndex": start_index, "endIndex": end_index},
                        "bulletPreset": "BULLET_DISC_CIRCLE_SQUARE",
                    }
                }
            )
        elif style == "numbered":
            requests.append(
                {
                    "createParagraphBullets": {
                        "range": {"startIndex": start_index, "endIndex": end_index},
                        "bulletPreset": "NUMBERED_DECIMAL_ALPHA_ROMAN",
                    }
                }
            )
        elif style == "heading1":
            requests.append(
                {
                    "updateParagraphStyle": {
                        "range": {"startIndex": start_index, "endIndex": end_index},
                        "paragraphStyle": {"namedStyleType": "HEADING_1"},
                        "fields": "namedStyleType",
                    }
                }
            )
        elif style == "heading2":
            requests.append(
                {
                    "updateParagraphStyle": {
                        "range": {"startIndex": start_index, "endIndex": end_index},
                        "paragraphStyle": {"namedStyleType": "HEADING_2"},
                        "fields": "namedStyleType",
                    }
                }
            )

    return requests


def create(file_metadata, file_content):
    with GoogleDocsManager() as service:
        file_metadata["mimeType"] = (
            file_metadata.get("mimeType") or "application/vnd.google-apps.document"
        )
        file = service.files().create(body=file_metadata, fields="id").execute()
        print(f"Created file {file_metadata.get('name')} with ID {file.id}")
        # TODO: we need to take the file content and insert this into the document
        # ideally the file_content will follow a schema and not just be raw strings
        # idea: ingredients are checklists
        # idea: steps are numbered lists
        # requests = [
        #     {
        #         "insertText": {
        #             "location": {
        #                 "index": 1,  # Insert at the beginning of the document
        #             },
        #             "text": "Hello, Google Docs API!",
        #         }
        #     },
        #     {
        #         "insertText": {
        #             "location": {
        #                 "index": 26,  # After the first text
        #             },
        #             "text": "\nThis is a new line of text.",
        #         }
        #     },
        # ]
        requests = __format_file_content__(file_content)
        service.documents().batchUpdate(
            documentId=file.id, body={"requests": requests}
        ).execute()


def get(document_id):
    pass


def update(document_id):
    pass


# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/documents.readonly"]

# The ID of a sample document.
DOCUMENT_ID = "195j9eDD3ccgjQRttHhJPymLJUCOUjs-jmwTrekvdjFE"


def main():
    """Shows basic usage of the Docs API.
    Prints the title of a sample document.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        service = build("docs", "v1", credentials=creds)

        # Retrieve the documents contents from the Docs service.
        document = service.documents().get(documentId=DOCUMENT_ID).execute()

        print(f"The title of the document is: {document.get('title')}")
    except HttpError as err:
        print(err)


if __name__ == "__main__":
    main()
