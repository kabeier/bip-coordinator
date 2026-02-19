from models import session_scope, Activity
from slack_sdk.errors import SlackApiError
from config import *
from utility import get_user_name_and_email, is_bip_admin
from app import bolt_app


#### CREATE
@bolt_app.shortcut("new_activity_submission")
def handle_command(ack, shortcut, client):
    ack()
    print("new_activity_submission triggered")
    user_id = shortcut["user"]["id"]
    _, email = get_user_name_and_email(user_id)
    if not is_bip_admin(email):
        print("Triggered by a non admin")
        client.chat_postEphemeral(
            channel=shortcut["channel"]["id"],
            user=user_id,
            text="You do not have permission to use this command"
        )
        return
    try:
        client.views_open(
            trigger_id=shortcut["trigger_id"],
            view={
                "type": "modal",
                "callback_id": "new_activity_submission",
                "title": {"type": "plain_text", "text": "Submit a Activity"},
                "submit": {"type": "plain_text", "text": "Submit"},
                "blocks": [
                    {
                        "type": "input",
                        "block_id": "points_block",
                        "element": {"type": "plain_text_input", "action_id": "points"},
                        "label": {"type": "plain_text", "text": "Points"}
                    },
                    {
                        "type": "input",
                        "block_id": "emoji_block",
                        "element": {"type": "plain_text_input", "action_id": "emoji"},
                        "label": {"type": "plain_text", "text": "Emoji"}
                    },
                    {
                        "type": "input",
                        "block_id": "title_block",
                        "element": {"type": "plain_text_input", "action_id": "title"},
                        "label": {"type": "plain_text", "text": "Title of Activity"}
                    },
                    {
                        "type": "input",
                        "block_id": "description_block",
                        "element": {"type": "plain_text_input", "action_id": "description"},
                        "label": {"type": "plain_text", "text": "Brief Description"}
                    },
                    {
                        "type": "input",
                        "block_id": "message_block",
                        "element": {"type": "plain_text_input", "action_id": "message"},
                        "label": {"type": "plain_text", "text": "Students Claim Message"}
                    },
                    {
                        "type": "input",
                        "block_id": "admin_award_block",
                        "element": {
                            "type": "radio_buttons",
                            "options": [
                                {
                                    "text": {
                                        "type": "plain_text",
                                        "text": "Yes"
                                    },
                                    "value": "yes"
                                },
                                {
                                    "text": {
                                        "type": "plain_text",
                                        "text": "No"
                                    },
                                    "value": "no"
                                }
                            ],
                            "action_id": "admin_award"
                        },
                        "label": {"type": "plain_text", "text": "Awarded by Admin"}
                    },
                    {
                        "type": "input",
                        "block_id": "rewards_to_block",
                        "element": {
                            "type": "radio_buttons",
                            "options": [
                                {
                                    "text": {
                                        "type": "plain_text",
                                        "text": "Posted"
                                    },
                                    "value": "yes"
                                },
                                {
                                    "text": {
                                        "type": "plain_text",
                                        "text": "Emoji-ed"
                                    },
                                    "value": "no"
                                }
                            ],
                            "action_id": "rewards_to"
                        },
                        "label": {"type": "plain_text", "text": "Rewards the Person who:"}
                    }

                ]
            }
        )
    except SlackApiError as e:
        print(f"Error opening modal: {e}")

@bolt_app.view("new_activity_submission")
def handle_view_events(ack, body, view, client):
    ack()
    
    user_id = body["user"]["id"]
    values = view["state"]["values"]

    points = values["points_block"]["points"]["value"]
    emoji = values["emoji_block"]["emoji"]["value"]

    title = values["title_block"]["title"]["value"]
    description = values["description_block"]["description"]["value"]

    emoji=emoji.strip(": ")

    message = values["message_block"]["message"]["value"]

    admin_award_values = values["admin_award_block"]["admin_award"].get("selected_options", [])
    admin_reward = any(option['value'] == 'awarded_by_admin' for option in admin_award_values)

    rewards_to_poster_values = values["rewards_to_block"]["rewards_to"].get("selected_options", [])
    rewards_to_poster = any(option['value'] == 'Rewards the Person who:' for option in rewards_to_poster_values)

    with session_scope() as session:
        existing_activity = session.query(Activity).filter(Activity.emoji == emoji).first()

        if existing_activity:
            # Emoji already exists, handle accordingly
            client.chat_postEphemeral(
                channel=body["channel"]["id"],
                user=user_id,
                text=f"The emoji :{emoji}: is already in use for another activity."
            )
            return

    try:
        with session_scope() as session:
            new_prize = Activity(
                points=float(points),  
                emoji=emoji,
                message=message,
                admin_reward=admin_reward,
                title=title,
                description=description,
                rewards_to_poster=rewards_to_poster
            )
            session.add(new_prize)

        client.chat_postEphemeral(
            channel=user_id,  
            user=user_id,
            text=f"Successfully added activity with emoji {emoji}"
        )
    except Exception as e:
        client.chat_postEphemeral(
            channel=user_id,  
            user=user_id,
            text=f"Failed to add prize: {str(e)}"
        )


#### EDIT
@bolt_app.shortcut("edit_activities")
def handle_edit_activity_shortcut(ack, shortcut, client):
    ack()
    print("edit menu triggered")
    user_id = shortcut["user"]["id"]
    _, email = get_user_name_and_email(user_id)
    if not is_bip_admin(email):
        client.chat_postEphemeral(
            channel=shortcut["channel"]["id"],
            user=user_id,
            text="You do not have permission to use this command"
        )
        return

    try:
        with session_scope() as session:
            activities = session.query(Activity).all()

            blocks = []
            for activity in activities:
                blocks.append({
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*{activity.title}* - :{activity.emoji}: - Points: {activity.points}"},
                    "accessory": {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Edit"},
                        "value": str(activity.id),
                        "action_id": "edit_activity"
                    }
                })

            client.views_open(
                trigger_id=shortcut["trigger_id"],
                view={
                    "type": "modal",
                    "callback_id": "list_activities_modal",
                    "title": {"type": "plain_text", "text": "Edit Activities"},
                    "blocks": blocks
                }
            )
    except SlackApiError as e:
        print(f"Error opening modal: {e}")

@bolt_app.action("edit_activity")
def open_edit_activity_modal(ack, body, client, action):
    ack()
    print("Edit Activity Triggered step 2")
    activity_id = action["value"]
    view_id = body["view"]["id"]
    try:
        with session_scope() as session:
            activity = session.get(Activity, activity_id)
            print("activity", activity.to_dict())
            if activity:
                
                res=client.views_push(
                    view_id=view_id,
                    trigger_id=body["trigger_id"],
                    view={
                        "type": "modal",
                        "callback_id": "edit_activity_modal",
                        "private_metadata": str(activity.id),
                        "title": {"type": "plain_text", "text": f"Edit: {activity.title[:9]}"},
                        "blocks": [
                            {
                                "type": "input",
                                "block_id": "title_block",
                                "element": {"type": "plain_text_input", "action_id": "title", "initial_value": activity.title},
                                "label": {"type": "plain_text", "text": "Title of Activity"}
                            },
                            {
                                "type": "input",
                                "block_id": "emoji_block",
                                "element": {"type": "plain_text_input", "action_id": "emoji", "initial_value": activity.emoji.strip(":")},
                                "label": {"type": "plain_text", "text": "Emoji"}
                            },
                            {
                                "type": "input",
                                "block_id": "points_block",
                                "element": {"type": "plain_text_input", "action_id": "points", "initial_value": str(activity.points)},
                                "label": {"type": "plain_text", "text": "Points"}
                            },
                            {
                                "type": "input",
                                "block_id": "description_block",
                                "element": {"type": "plain_text_input", "action_id": "description", "multiline": True, "initial_value": activity.description or ""},
                                "label": {"type": "plain_text", "text": "Brief Description"}
                            },
                            {
                                "type": "input",
                                "block_id": "message_block",
                                "element": {"type": "plain_text_input", "action_id": "message", "initial_value": activity.message or ""},
                                "label": {"type": "plain_text", "text": "Message"}
                            },
                            {
                                "type": "input",
                                "block_id": "admin_reward_block",
                                "element": {
                                    "type": "radio_buttons",
                                    "action_id": "admin_reward",
                                    "initial_option": {
                                        "text": {"type": "plain_text", "text": "Yes" if activity.admin_reward else "No"},
                                        "value": "yes" if activity.admin_reward else "no"
                                    },
                                    "options": [
                                        {
                                            "text": {"type": "plain_text", "text": "Yes"},
                                            "value": "yes"
                                        },
                                        {
                                            "text": {"type": "plain_text", "text": "No"},
                                            "value": "no"
                                        }
                                    ]
                                },
                                "label": {"type": "plain_text", "text": "Awarded by Admin"}
                            },
                            {
                                "type": "input",
                                "block_id": "rewards_to_block",
                                "element": {
                                    "type": "radio_buttons",
                                    "initial_option": {
                                        "text": {"type": "plain_text", "text": "Posted" if activity.rewards_to_poster else "Emoji-ed"},
                                        "value": "yes" if activity.rewards_to_poster else "no"
                                    },
                                    "options": [
                                        {
                                            "text": {
                                                "type": "plain_text",
                                                "text": "Posted"
                                            },
                                            "value": "yes"
                                        },
                                        {
                                            "text": {
                                                "type": "plain_text",
                                                "text": "Emoji-ed"
                                            },
                                            "value": "no"
                                        }
                                    ],
                                    "action_id": "rewards_to"
                                },
                                "label": {"type": "plain_text", "text": "Rewards the Person who:"}
                            }

                        ],
                        "submit": {"type": "plain_text", "text": "Update"},

                    }
                )
                print("res", res)
    except SlackApiError as e:
        print(f"Error opening edit modal: {e}")

@bolt_app.view("edit_activity_modal")
def handle_edit_activity_submission(ack, body, view, client):
    print("performing Activity edits")
    ack()
    user_id = body["user"]["id"]
    values = view["state"]["values"]
    activity_id = view["private_metadata"] 

    # Extract the fields from the form
    title = values["title_block"]["title"]["value"]
    emoji = values["emoji_block"]["emoji"]["value"].strip(": ")
    points =float(values["points_block"]["points"]["value"])
    description = values["description_block"]["description"]["value"]
    message = values["message_block"]["message"]["value"]

    admin_reward_selected_option = values["admin_reward_block"]["admin_reward"]["selected_option"]["value"]
    admin_reward = admin_reward_selected_option == "yes"

    rewards_to_poster_values = values["rewards_to_block"]["rewards_to"].get("selected_options", [])
    rewards_to_poster = any(option['value'] == 'Rewards the Person who:' for option in rewards_to_poster_values)

    # Update the activity in the database
    try:
        with session_scope() as session:
            activity = session.get(Activity, activity_id)
            if activity:
                activity.title = title
                activity.emoji = emoji
                activity.points = points
                activity.description = description
                activity.message = message
                activity.admin_reward = admin_reward
                activity.rewards_to_poster = rewards_to_poster
                session.commit()

            client.chat_postEphemeral(
                channel=user_id,  
                user=user_id,
                text=f"Successfully updated activity '{activity.title}'"
            )
    except Exception as e:
        client.chat_postEphemeral(
            channel=user_id,  
            user=user_id,
            text=f"Failed to update activity: {str(e)}"
        )

#### DELETE
@bolt_app.shortcut("delete_activities")
def handle_delete_activity_shortcut(ack, shortcut, client):
    ack()
    print("edit menu triggered")
    user_id = shortcut["user"]["id"]
    _, email = get_user_name_and_email(user_id)
    if not is_bip_admin(email):
        client.chat_postEphemeral(
            channel=shortcut["channel"]["id"],
            user=user_id,
            text="You do not have permission to use this command"
        )
        return

    try:
        with session_scope() as session:
            activities = session.query(Activity).all()

            blocks = []
            for activity in activities:
                blocks.append({
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*{activity.title}* - :{activity.emoji}: - Points: {activity.points}"},
                    "accessory": {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Delete"},
                        "value": str(activity.id),
                        "action_id": "delete_activity",
                        "confirm": {
                            "title": {"type": "plain_text", "text": "Confirm Delete"},
                            "text": {"type": "mrkdwn", "text": "Are you sure you want to delete this activity?"},
                            "confirm": {"type": "plain_text", "text": "Yes, delete it"},
                            "deny": {"type": "plain_text", "text": "No, cancel"},
                            "style": "danger"
                        }
                    }
                })

            client.views_open(
                trigger_id=shortcut["trigger_id"],
                view={
                    "type": "modal",
                    "callback_id": "list_activities_delete_modal",
                    "title": {"type": "plain_text", "text": "Delete Activities"},
                    "blocks": blocks
                }
            )
    except SlackApiError as e:
        print(f"Error opening modal: {e}")

@bolt_app.action("delete_activity")
def delete_activity(ack, body, client, action):
    ack()
    print("Delete Activity Deleting")
    activity_id = action["value"]
    user_id = body["user"]["id"]
    try:
        with session_scope() as session:
            activity = session.get(Activity, activity_id)
            if activity.id==WELCOME_ACTIVITY_ID:
                return

            activity.delete(session) 
     
            client.chat_postEphemeral(
                channel=user_id,
                user=user_id,
                text=f"Activity '{activity.title}' has been successfully deleted."
                )
    except Exception as e:
        client.chat_postEphemeral(
            channel=user_id,  
            user=user_id,
            text=f"Failed to delete activity: {str(e)}"
        )