import base64
import json
import os.path
from collections import defaultdict

import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pytest_check as check

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://mail.google.com/"]


def gmail_login():
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
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return creds


def get_emails(creds):
    service = build("gmail", "v1", credentials=creds)
    results = service.users().messages().list(userId='me', q='in:inbox from:shay@droxi.ai').execute()
    messages = results.get('messages', [])

    emails_by_subject = defaultdict(list)

    for msg in messages:
        msg_detail = service.users().messages().get(userId='me', id=msg['id']).execute()
        headers = msg_detail['payload'].get('headers', [])
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '(no subject)')
        body = get_body_from_payload(msg_detail['payload'])
        emails_by_subject[subject].append(body)

    return emails_by_subject


def get_body_from_payload(payload):
    body = ""
    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain':
                data = part['body'].get('data', '')
                body += base64.urlsafe_b64decode(data.encode()).decode('utf-8').strip()
    elif payload.get('body', {}).get('data'):
        data = payload['body']['data']
        body = base64.urlsafe_b64decode(data.encode()).decode('utf-8').strip()
    return body


def print_labels(creds):
    try:
        # Call the Gmail API
        service = build("gmail", "v1", credentials=creds)
        results = service.users().labels().list(userId="me").execute()

        labels = results.get("labels", [])

        if not labels:
            print("No labels found.")
            return
        print("Labels:")
        for label in labels:
            print(label["name"])

    except HttpError as error:
        # TODO(developer) - Handle errors from gmail API.
        print(f"An error occurred: {error}")


def main():
    """Shows basic usage of the Gmail API.
  Lists the user's Gmail labels.
  """

    creds: Credentials = gmail_login()
    return print_labels(creds)


with open("Trello_creds.json") as f:
    config = json.load(f)

TRELLO_API_KEY = config["trello"]["api_key"]
TRELLO_API_TOKEN = config["trello"]["api_token"]
BOARD_ID = config["trello"]["board_id"]
TRELLO_BASE = config["trello"]["base_url"]


def get_cards():
    url = f"{TRELLO_BASE}/boards/{BOARD_ID}/cards"
    params = {
        "key": TRELLO_API_KEY,
        "token": TRELLO_API_TOKEN,
        "fields": "name,desc,idLabels"
    }
    res = requests.get(url, params=params)
    return res.json()


def get_labels():
    url = f"{TRELLO_BASE}/boards/{BOARD_ID}/labels"
    params = {
        "key": TRELLO_API_KEY,
        "token": TRELLO_API_TOKEN
    }
    res = requests.get(url, params=params)
    return {label['id']: label['name'] for label in res.json()}


def validate_urgent_cards(gmail_data, trello_cards, label_map):
    print("\n Validating Urgent Emails → Trello Cards")
    for subject, bodies in gmail_data.items():
        for body in bodies:
            if "urgent" in body.lower():
                card = next((c for c in trello_cards if c['name'] == subject), None)
                assert card is not None, f"Missing card for Urgent email with subject: {subject}"
                label_names = [label_map[lid] for lid in card['idLabels']]
                assert "Urgent" in label_names, f"Card '{subject}' missing 'Urgent' label"
                print(f"Urgent card '{subject}' found with label.")


def validate_merging(gmail_data, trello_cards):
    print("\n Validating Email Merging Logic")
    for subject, bodies in gmail_data.items():
        if len(bodies) > 1:
            seen = set()
            processed_bodies = []

            for b in reversed(bodies):
                b_clean = b.strip()
                if not b_clean:
                    processed_bodies.append("")
                elif b_clean in seen:
                    processed_bodies.append("")
                else:
                    seen.add(b_clean)
                    processed_bodies.append(b_clean)

            expected_description = "\n".join(processed_bodies).replace("\r\n", "\n", 1)
            # expected_description=expected_description
            clean_subject = subject.replace('Task:', '').strip().lower()

            card = next(
                (c for c in trello_cards if c['name'].strip().lower() == clean_subject),
                None
            )
            assert card is not None, f"Missing merged card for subject: {subject}"
            actual = card['desc'].strip()
            check.equal(actual, expected_description, (
                f"Card '{subject}' has incorrect merged description:\nExpected:\n{expected_description}\n\nActual:\n{actual}"
            ))


def run_sync_validation():
    creds = gmail_login()
    print("Fetching Gmail emails...")
    gmail_data = get_emails(creds)

    print("Fetching Trello cards...")
    trello_cards = get_cards()

    print("Fetching Trello labels...")
    label_map = get_labels()

    validate_urgent_cards(gmail_data, trello_cards, label_map)
    validate_merging(gmail_data, trello_cards)
    print("\nAll sync checks passed!")


if __name__ == "__main__":
    main()
