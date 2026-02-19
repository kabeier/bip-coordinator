from models import session_scope, Prize
from slack_sdk.errors import SlackApiError
from config import *
from utility import get_user_name_and_email, is_bip_admin
from app import bolt_app

#### CREATE
@bolt_app.shortcut("new_prize_submission")
def handle_command(ack, shortcut, client):
    ack()
    print("new_prize_submission triggered")
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
                "callback_id": "new_prize_submission",
                "title": {"type": "plain_text", "text": "Submit a Prize"},
                "submit": {"type": "plain_text", "text": "Submit"},
                "blocks": [
                    {
                        "type": "input",
                        "block_id": "cost_block",
                        "element": {"type": "plain_text_input", "action_id": "cost"},
                        "label": {"type": "plain_text", "text": "Cost"}
                    },
                    {
                        "type": "input",
                        "block_id": "name_block",
                        "element": {"type": "plain_text_input", "action_id": "name"},
                        "label": {"type": "plain_text", "text": "Name of Prize"}
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
                    

                ]
            }
        )
    except SlackApiError as e:
        print(f"Error opening modal: {e}")

@bolt_app.view("new_prize_submission")
def handle_view_events(ack, body, view, client):
    ack()
    
    user_id = body["user"]["id"]
    values = view["state"]["values"]

    cost = values["cost_block"]["cost"]["value"]

    name = values["name_block"]["name"]["value"]
    description = values["description_block"]["description"]["value"]

    message = values["message_block"]["message"]["value"]

    try:
        with session_scope() as session:
            new_prize = Prize(
                cost=int(cost),  
                win_message=message,
                name=name,
                description=description
            )
            session.add(new_prize)

        client.chat_postEphemeral(
            channel=user_id,  
            user=user_id,
            text=f"Successfully added prize: {name}"
        )
    except Exception as e:
        client.chat_postEphemeral(
            channel=user_id,  
            user=user_id,
            text=f"Failed to add prize: {str(e)}"
        )


#### EDIT
@bolt_app.shortcut("edit_prizes")
def handle_edit_prize_shortcut(ack, shortcut, client):
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
            prizes = session.query(Prize).all()

            blocks = []

            for prize in prizes:
                # Section block for prize information
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*{prize.name}* - Cost: {prize.cost}"
                    }
                })

                # Actions block for Edit and Delete buttons
                blocks.append({
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "Edit"},
                            "value": str(prize.id),
                            "action_id": "edit_prize"
                        },
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "Delete"},
                            "value": str(prize.id),
                            "action_id": "delete_prize",
                            "style": "danger",
                            "confirm": {
                                "title": {"type": "plain_text", "text": "Confirm Delete"},
                                "text": {"type": "mrkdwn", "text": "Are you sure you want to delete this prize?"},
                                "confirm": {"type": "plain_text", "text": "Yes, delete it"},
                                "deny": {"type": "plain_text", "text": "No, cancel"}
                            }
                        }
                    ]
                })

            


            client.views_open(
                trigger_id=shortcut["trigger_id"],
                view={
                    "title": {"type": "plain_text", "text": "Edit a Prize"},

                    "type": "modal",
                    "callback_id": "list_prizes_modal",
                    "blocks": blocks
                }
            )
    except SlackApiError as e:
        print(f"Error opening modal: {e}")

@bolt_app.action("edit_prize")
def open_edit_prize_modal(ack, body, client, action):
    ack()
    print("Edit Prize Triggered step 2")
    prize_id = action["value"]
    view_id = body["view"]["id"]
    try:
        with session_scope() as session:
            prize = session.get(Prize, prize_id)
            print("prize", prize)
            if prize:
                
                res=client.views_push(
                    view_id=view_id,
                    trigger_id=body["trigger_id"],
                    view={
                        "type": "modal",
                        "callback_id": "edit_prize_modal",
                        "private_metadata": str(prize.id),
                        "title": {"type": "plain_text", "text": f"Edit: {prize.name[:9]}"},
                        "blocks": [
                            {
                                "type": "input",
                                "block_id": "name_block",
                                "element": {"type": "plain_text_input", "action_id": "name", "initial_value": prize.name},
                                "label": {"type": "plain_text", "text": "Name of Prize"}
                            },

                            {
                                "type": "input",
                                "block_id": "cost_block",
                                "element": {"type": "plain_text_input", "action_id": "cost", "initial_value": str(prize.cost)},
                                "label": {"type": "plain_text", "text": "Cost"}
                            },
                            {
                                "type": "input",
                                "block_id": "description_block",
                                "element": {"type": "plain_text_input", "action_id": "description", "multiline": True, "initial_value": prize.description or ""},
                                "label": {"type": "plain_text", "text": "Brief Description"}
                            },
                            {
                                "type": "input",
                                "block_id": "message_block",
                                "element": {"type": "plain_text_input", "action_id": "message", "initial_value": prize.win_message or ""},
                                "label": {"type": "plain_text", "text": "Message"}
                            },

                        ],
                        "submit": {"type": "plain_text", "text": "Update"},

                    }
                )
                print("res", res)
    except SlackApiError as e:
        print(f"Error opening edit modal: {e}")

@bolt_app.view("edit_prize_modal")
def handle_edit_prize_submission(ack, body, view, client):
    print("performing Prize edits")
    ack()
    user_id = body["user"]["id"]
    values = view["state"]["values"]
    prize_id = view["private_metadata"] 

    # Extract the fields from the form
    name = values["name_block"]["name"]["value"]
    cost = int(values["cost_block"]["cost"]["value"])
    description = values["description_block"]["description"]["value"]
    message = values["message_block"]["message"]["value"]

    # Update the prize in the database
    try:
        with session_scope() as session:
            prize = session.get(Prize, prize_id)
            if prize:
                prize.name = name
                prize.cost = cost
                prize.description = description
                prize.win_message = message

                session.commit()

            client.chat_postEphemeral(
                channel=user_id,  
                user=user_id,
                text=f"Successfully updated prize '{prize.name}'"
            )
    except Exception as e:
        client.chat_postEphemeral(
            channel=user_id,  
            user=user_id,
            text=f"Failed to update prize: {str(e)}"
        )

#### DELETE
# @bolt_app.shortcut("delete_prizes")
# def handle_delete_prize_shortcut(ack, shortcut, client):
#     ack()
#     print("edit menu triggered")
#     user_id = shortcut["user"]["id"]
#     _, email = get_user_name_and_email(user_id)
#     if not is_bip_admin(email):
#         client.chat_postEphemeral(
#             channel=shortcut["channel"]["id"],
#             user=user_id,
#             text="You do not have permission to use this command"
#         )
#         return

#     try:
#         with session_scope() as session:
#             prizes = session.query(Prize).all()

#             blocks = []
#             for prize in prizes:
#                 blocks.append({
#                     "type": "section",
#                     "text": {"type": "mrkdwn", "text": f"*{prize.name}* - Cost: {prize.cost}"},
#                     "accessory": {
#                         "type": "button",
#                         "text": {"type": "plain_text", "text": "Delete"},
#                         "value": str(prize.id),
#                         "action_id": "delete_prize",
#                         "confirm": {
#                             "title": {"type": "plain_text", "text": "Confirm Delete"},
#                             "text": {"type": "mrkdwn", "text": "Are you sure you want to delete this prize?"},
#                             "confirm": {"type": "plain_text", "text": "Yes, delete it"},
#                             "deny": {"type": "plain_text", "text": "No, cancel"},
#                             "style": "danger"
#                         }
#                     }
#                 })

#             client.views_open(
#                 trigger_id=shortcut["trigger_id"],
#                 view={
#                     "type": "modal",
#                     "callback_id": "list_prizes_delete_modal",
#                     "title": {"type": "plain_text", "text": "Delete Prizes"},
#                     "blocks": blocks
#                 }
#             )
#     except SlackApiError as e:
#         print(f"Error opening modal: {e}")

@bolt_app.action("delete_prize")
def delete_prize(ack, body, client, action):
    ack()
    print("Delete Prize Deleting")
    prize_id = action["value"]
    user_id = body["user"]["id"]
    try:
        with session_scope() as session:
            prize = session.get(Prize, prize_id)
            prize.delete(session)    
            client.chat_postEphemeral(
                channel=user_id,
                user=user_id,
                text=f"Prize '{prize.name}' has been successfully deleted."
                )
    except Exception as e:
        client.chat_postEphemeral(
            channel=user_id,  
            user=user_id,
            text=f"Failed to delete prize: {str(e)}"
        )