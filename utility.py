import requests
import time
from config import *
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

def get_user_id_from_email(client: WebClient, email: str):
    try:
        # Fetch user info based on email
        user_info = client.users_lookupByEmail(email=email)
        # Extract user ID from the response
        user_id = user_info.get('user', {}).get('id')
        return user_id
    except SlackApiError as e:
        print(f"Error fetching user ID for email {email}: {e}")
        return None

def is_bip_admin(email):
    return email in BIP_ADMINS


def make_slack_api_request(url, headers):
    """Make a Slack API request with rate limit handling."""
    for _ in range(3):  # Retry up to 3 times
        response = requests.get(url, headers=headers)
        if response.status_code == 429:  # Rate limit exceeded
            retry_after = int(response.headers.get("Retry-After", 60))  # Use 60 seconds if header is missing
            print(f"Rate limit exceeded. Retrying after {retry_after} seconds.")
            time.sleep(retry_after)
            continue
        return response.json()
    return None


def get_user_name_and_email(user_id):
    from app import bolt_app
    user_profile = bolt_app.client.users_profile_get(user=user_id)
    tagged_user_email = user_profile["profile"]["email"]
    user_name = user_profile["profile"].get("real_name") or user_profile["profile"].get("display_name")
    return user_name, tagged_user_email