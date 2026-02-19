from models import session_scope, Activity, User, UserActivity
from slack_sdk.errors import SlackApiError
from config import *
from utility import get_user_name_and_email
from app import bolt_app

from datetime import datetime
import pytz



@bolt_app.event("reaction_added")
def handle_reaction_added(event, context, client):
    channel = event['item']['channel']
    user_id = event['user']
    reaction = event['reaction']
    print(channel)
    if channel in MONITORED_CHANNELS:
        print("BIP reaction_added", reaction)

        process_reaction(event, context, client, reaction, user_id, True)
    else:
        print("non BIP reaction_added")

@bolt_app.event("reaction_removed")
def handle_reaction_removed(event, context, client):
    channel = event['item']['channel']
    user_id = event['user']
    reaction = event['reaction']
    print("removing emoji attempted on", reaction)
    if channel in MONITORED_CHANNELS:
        print("BIP reaction_removed")
        process_reaction(event, context, client, reaction, user_id, False)

def process_reaction(event, context, client, reaction, user_id, add_reaction):
    with session_scope() as session:
        activity = session.query(Activity).filter(Activity.emoji == reaction).first()
        if activity:
            # only admins can remove admin activities
            if activity.admin_reward and not get_user_name_and_email(user_id)[1] in BIP_ADMINS:
                return

            # Check if reaction is from an admin for admin_reward activities
            if activity.admin_reward and not get_user_name_and_email(user_id)[1] in BIP_ADMINS:
                return
            
            reacting_user = session.query(User).filter(User.id == user_id).first()
            if not reacting_user:
                # If user not found, create a new user
                user_info = get_user_name_and_email(user_id)
                if user_info:
                    reacting_user = User(
                        id=user_id,
                        full_name=user_info[0],
                        email=user_info[1]
                    )
                    session.add(reacting_user)
                else:
                    send_error_message(client, user_id, "Unable to process your reaction at this time.")

            # If rewards_to_poster is True, find the original poster of the message
            if activity.rewards_to_poster:
                item_user_id = event['item_user']
                post_user = session.query(User).filter(User.id == item_user_id).first()
                if not post_user:
                    # Handle case where post user is not found in the database
                    return
                user_to_reward = post_user
            else:
                user_to_reward = reacting_user
            
            user_activity_record=None
            
            if add_reaction:
                # user_to_reward.activities.append(activity)
                item_ts = event['item']['ts']  # Timestamp of the item the reaction is attached to
                user_activity = UserActivity(user_id=user_to_reward.id, activity_id=activity.id, reaction_item_ts=item_ts)
                session.add(user_activity)
                
                send_dm(client, user_to_reward.id, f"{activity.message}.\n You now have {round(user_to_reward.total_points(session),2)} points")
            else:
                # user_activity_record = session.query(UserActivity).filter(
                #     UserActivity.user_id == user_to_reward.id,
                #     UserActivity.activity_id == activity.id
                # ).first() 
                item_ts = event['item']['ts']  # Timestamp of the item the reaction was attached to
                user_activity_record = session.query(UserActivity).filter(
                    UserActivity.user_id == user_to_reward.id,
                    UserActivity.activity_id == activity.id,
                    UserActivity.reaction_item_ts == item_ts
                ).first()

                if user_activity_record:
                    session.delete(user_activity_record)
                    send_dm(client, user_id, f"{activity.title}.\n You now have {round(user_to_reward.total_points(session),2)} points")


            # if user_activity_record:
            #     session.delete(user_activity_record)
            #     # Remove activity from user's activities if it exists
            #     if activity in user_to_reward.activities:
            #         user_to_reward.activities.remove(activity)

            session.commit()

def send_error_message(client, user_id, message):
    try:
        client.chat_postEphemeral(channel=user_id, user=user_id, text=message)
    except SlackApiError as e:
        print(f"Error sending error message: {e}")


def send_dm(client, user_id, message):
    try:
        client.chat_postMessage(channel=user_id, text=message)
    except SlackApiError as e:
        print(f"Error sending DM: {e}")