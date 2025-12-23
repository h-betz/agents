import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

BASE_URL = "https://docs.googleapis.com"
SCOPES = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive",
]


class GoogleDocsManager:

    def __init__(self):
        self.docs_service = None
        self.drive_service = None
        # Get the directory where this file is located
        self.base_dir = os.path.dirname(os.path.abspath(__file__))

    def __enter__(self):
        creds = None
        token_path = os.path.join(self.base_dir, "token.json")
        credentials_path = os.path.join(self.base_dir, "credentials.json")

        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_path, SCOPES
                )
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(token_path, "w") as token:
                token.write(creds.to_json())

        # Build both Docs and Drive services
        self.docs_service = build("docs", "v1", credentials=creds)
        self.drive_service = build("drive", "v3", credentials=creds)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        print("Exiting context for Google Docs service")
        # Perform teardown actions, e.g., close a file, release a lock
        if exc_type:
            print(f"An exception occurred: {exc_value}")
        return False  # Do not suppress exceptions

    def _format_file_content(self, file_content):
        """
        Docstring for _format_file_content

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

    def create(self, file_metadata, file_content):
        """Create a new Google Doc with formatted content."""
        file_metadata["mimeType"] = (
            file_metadata.get("mimeType") or "application/vnd.google-apps.document"
        )
        # Use Drive API to create the file
        file = self.drive_service.files().create(body=file_metadata, fields="id").execute()
        print(f"Created file {file_metadata.get('name')} with ID {file.get('id')}")

        # Format and insert content using Docs API
        requests = self._format_file_content(file_content)
        self.docs_service.documents().batchUpdate(
            documentId=file.get("id"), body={"requests": requests}
        ).execute()

        return file

    def get(self, document_id):
        """Retrieve a Google Doc by document ID."""
        document = self.docs_service.documents().get(documentId=document_id).execute()
        return document

    def update(self, document_id, data):
        """Update an existing Google Doc with new content."""
        requests = self._format_file_content(data)
        result = (
            self.docs_service.documents()
            .batchUpdate(documentId=document_id, body={"requests": requests})
            .execute()
        )
        return result
