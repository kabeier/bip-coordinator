from app import bolt_app
from models import User, Prize, UserPrize, session_scope
from config import BIP_ADMINS
from utility import get_user_id_from_email, get_user_name_and_email
from slack_sdk.errors import SlackApiError


@bolt_app.command("/claimprizes")
def handle_claim_prizes_command(ack, body, client):
    ack()  

    try:
        user_id = body["user_id"]

        with session_scope() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                user_info = get_user_name_and_email(user_id)
                if user_info:
                    user = User(
                        id=user_id,
                        full_name=user_info[0],
                        email=user_info[1]
                    )
                    session.add(user)
                    session.commit()

            total_points = user.total_points(session)
            prizes = session.query(Prize).all()

            blocks = [{
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Your Total Points:* {round(total_points,2)}"}
            }]

            for prize in prizes:
                prize_cost_text = f"Cost: {prize.cost} Points"
                can_claim = prize.cost <= total_points

                blocks.append({
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"*{prize.name}* - {prize_cost_text}"},
                    "accessory": {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "More Info"},
                        "value": str(prize.id),
                        "action_id": "show_prize_info"
                    }
                })

                if can_claim:
                    blocks.append({
                        "type": "actions",
                        "elements": [{
                            "type": "button",
                            "text": {"type": "plain_text", "text": "Claim"},
                            "value": str(prize.id),
                            "action_id": "claim_prize",
                            "style": "primary"
                        }]
                    })
                else:
                    blocks.append({
                        "type": "context",
                        "elements": [{"type": "mrkdwn", "text": "_You do not have enough points to claim this prize._"}]
                    })


            client.views_open(
                trigger_id=body["trigger_id"],
                callback_id= "prize-claims",

                view={
                    "type": "modal",
                    "title": {"type": "plain_text", "text": "Available Prizes"},
                    "blocks": blocks
                }
            )
    except Exception as e:
        print(f"Error handling /claimprizes command: {e}")
        client.chat_postEphemeral(channel=body["channel"]["id"], user=user_id, text="Error processing your request.")

@bolt_app.action("claim_prize")
def handle_claim_prize(ack, body, client, action):
    ack()
    user_id = body["user"]["id"]
    prize_id = action["value"]
    view_id = body["view"]["id"]  # Get the ID of the current view

    try:
        with session_scope() as session:
            prize = session.query(Prize).filter(Prize.id == prize_id).first()
            user = session.query(User).filter(User.id == user_id).first()

            if not user:
                user_info = get_user_name_and_email(user_id)
                if user_info:
                    user = User(
                        id=user_id,
                        full_name=user_info[0],
                        email=user_info[1]
                    )
            if not prize:
                client.chat_postEphemeral(channel=user.id, user=user, text="Error: User or prize not found.")
                return

            # Create a new prize claim record
            user_prize = UserPrize(user_id=user_id, prize_id=prize_id)
            session.add(user_prize)
            session.commit()

            # Push a new view that acknowledges the prize claim
            client.views_update(
                trigger_id=body["trigger_id"],
                view_id=view_id,  # Use the current view ID
                view={
                    "type": "modal",
                    "title": {"type": "plain_text", "text": "Prize Claimed"},
                    "blocks": [
                        {
                            "type": "section",
                            "text": {"type": "mrkdwn", "text": f"You have successfully claimed the prize: {prize.name}. {prize.win_message}"}
                        }
                    ]
                }
            )
            new_total_points = user.total_points(session)
            # Notify student of claim
            client.chat_postMessage(
                channel=user_id,  # User's Slack ID
                text=f"You claimed the prize '{prize.name}' for {prize.cost} points. Your new point total is {new_total_points}."
            )
            # Notify BIP administrators
            for admin_email in BIP_ADMINS:
                admin_user_id = get_user_id_from_email(client, admin_email)  # Assuming you have a function to get the user ID from email
                if admin_user_id:
                    client.chat_postMessage(
                        channel=admin_user_id,  # Admin's Slack ID
                        text=f"<@{user_id}> claimed the prize '{prize.name}'."
                    )

    except Exception as e:
        print(f"Error claiming prize: {e}")
        client.chat_postEphemeral(channel=user_id, user=user_id, text="Error claiming the prize.")

@bolt_app.action("show_prize_info")
def handle_show_prize_info(ack, body, client, action):
    ack()
    prize_id = action["value"]
    view_id = body["view"]["id"]

    try:
        with session_scope() as session:
            prize = session.query(Prize).filter(Prize.id == prize_id).first()
            if prize:
                blocks = [
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": f"*Name:* {prize.name}\n*Cost:* {prize.cost}\n*Description:* {prize.description}"}
                    }
                ]
                client.views_push(
                    view_id=view_id,
                    trigger_id=body["trigger_id"],
                    view={
                        "type": "modal",
                        "title": {"type": "plain_text", "text": "Prize Details"},
                        "blocks": blocks
                    }
                )
            else:
                client.chat_postEphemeral(channel=body["channel"]["id"], user=body["user"]["id"], text="Prize not found.")
    except Exception as e:
        print(f"Error fetching prize details: {e}")
        client.chat_postEphemeral(channel=body["channel"]["id"], user=body["user"]["id"], text="Error fetching prize details.")
