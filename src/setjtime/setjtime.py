import os
import sys
import argparse
import requests
from datetime import date
from requests.auth import HTTPBasicAuth
from colored import Fore, Style

sys.stdout.reconfigure(encoding="utf-8")  # type: ignore
sys.stderr.reconfigure(encoding="utf-8")  # type: ignore

JIRA_DOMAIN = os.getenv("JIRA_DOMAIN", "")
JIRA_EMAIL = os.getenv("JIRA_EMAIL", "")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN", "")

TODAY = date.today().strftime("%d/%m/%Y")
PROJECT_KEY = "TDRGDL" #issue key prefix for the Jira project
ISSUE_KEY = f"{PROJECT_KEY}-{{}}"

URL = "https://{0}/rest/api/3/issue/{1}/worklog"
HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
}

check_env_vars = [JIRA_DOMAIN, JIRA_EMAIL, JIRA_API_TOKEN]
if not all(var != "" for var in check_env_vars):
    print(f"{Fore.RED}Error: One or more required environment variables are missing.{Style.reset}")
    print(f"{Fore.YELLOW}Please set JIRA_DOMAIN, JIRA_EMAIL, and JIRA_API_TOKEN.{Style.reset}")
    sys.exit(1)

def parse_args():
    parser = argparse.ArgumentParser(description="Add a worklog entry to a Jira issue.")
    parser.add_argument("issue_id", type=int, help="Issue number (example: 6552 for TDRGDL-6552).")
    parser.add_argument("-t", "--time", type=str, required=True, default="0h", help="Time spent to log, e.g. 1h, 30m, 2d.")
    parser.add_argument("-c", "--comment", type=str, required=False, default="", help="Optional worklog comment.")
    return parser.parse_args()

def to_adf(text: str) -> dict:
    """
    Convert a plain text string into Atlassian Document Format (ADF) for Jira worklog comments.
    """
    lines = text.splitlines() or [""]
    content = []

    for line in lines:
        if line.strip():
            content.append({
                "type": "paragraph",
                "content": [{"type": "text", "text": line}]
            })
        else:
            content.append({"type": "paragraph"})

    return {
        "type": "doc",
        "version": 1,
        "content": content
    }

def create_payload(args: argparse.Namespace) -> dict:
    spent_time = args.time
    comment_text = ""

    if args.comment:
        comment_text = str(args.comment).replace(";", "\n")

    full_comment = f"[{spent_time}] - {comment_text} Logged on *{TODAY}*".strip()

    return {
        "timeSpent": spent_time,
        "comment": to_adf(full_comment)
    }


def connect_jira(payload: dict, issue_id: int):
    ticket_key = ISSUE_KEY.format(issue_id)
    url = URL.format(JIRA_DOMAIN, ticket_key)

    auth = HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN)
    response = requests.post(url, auth=auth, headers=HEADERS, json=payload)

    if response.status_code == 201:
        print(f"Worklog entry added successfully to {ticket_key}.")
    else:
        print(f"Failed to add worklog entry to {ticket_key}. Status code: {response.status_code}")
        print("Response:", response.text)

def run():
    args = parse_args()
    payload = create_payload(args)
    connect_jira(payload, args.issue_id)

if __name__ == "__main__": # python command line entry point compatibility.
    run()