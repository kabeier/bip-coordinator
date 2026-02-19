# Load in env
from dotenv import load_dotenv
load_dotenv()

# Load packages
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk.errors import SlackApiError
import re
from config import *
import time

# Load App
from app import bolt_app

# Load Components
import crud_activity, crud_prize, emoji_monitoring, prize_claim, mybip, bipwelcome 
import bipweekly, bipmonthly, bipalltime, bip_help

print("Running BIP coordinator.py")

# Dummy Response For Testing
# @bolt_app.message(re.compile(r""))
# def handle_message(client, message, say, context):
#     print("triggered")
#     try:
#         channel_id = message["channel"]
#         channel_info = bolt_app.client.conversations_info(channel=channel_id)

#         sender_name, email=get_user_name_and_email(context["user_id"])
#         say(f"hello {sender_name} from BIP Bot I can send you an email at {email}")

#     except Exception as e:
#         print(f"Unexpected error handling message: {str(e)}")

def configure_monitored_channels():
    try:
        cursor = None
        while True:
            try:
                result = bolt_app.client.conversations_list(
                    types="public_channel,private_channel",
                    cursor=cursor
                )

                for channel in result["channels"]:
                    if channel["name"] in MONITORED_CHANNELS_NAMES:
                        MONITORED_CHANNELS.append(channel["id"])
                        print("Linking",channel["name"])

                cursor = result.get('response_metadata', {}).get('next_cursor')
                if not cursor:
                    break

            except SlackApiError as e:
                if e.response["error"] == "ratelimited":
                    retry_after = int(e.response.headers.get("Retry-After", 60))
                    print(f"Rate limited. Retrying after {retry_after} seconds.")
                    time.sleep(retry_after)  
                    continue  
                else:
                    print(f"Error fetching channel IDs: {e}")
                    break

    except Exception as e:
        print(f"Unexpected error: {e}")


    

def main():
    try:
        print("configuring channels...")
        configure_monitored_channels()
        print("Configured Monitored Channels:", MONITORED_CHANNELS)
        print("App running")
        handler = SocketModeHandler(bolt_app, SLACK_BOT_OAUTH)
        handler.start()
    except Exception as e:

        print(f"Startup error: {e}")
        
if __name__ == '__main__':
    main()