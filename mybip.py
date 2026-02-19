from app import bolt_app
from models import User, UserActivity, UserPrize, Activity, Prize, session_scope

ITEMS_PER_PAGE = 10

@bolt_app.command("/mybip")
def handle_mybip_command(ack, body, client):
    ack()
    user_id = body["user_id"]
    open_mybip_view(client, user_id, 1, body["trigger_id"])

def open_mybip_view(client, user_id, page, trigger_id):
    try:
        with session_scope() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                # Open a modal to inform the user
                blocks = [{
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "You haven't started doing activities yet. Start participating in activities and come back here to see your stats!"
                    }
                }]
                client.views_open(
                    trigger_id=trigger_id,
                    view={
                        "type": "modal",
                        "title": {"type": "plain_text", "text": "My BIP Stats"},
                        "blocks": blocks
                    }
                )
                return

            total_points = user.total_points(session)
            activities = session.query(UserActivity).filter(UserActivity.user_id == user_id).order_by(UserActivity.date_achieved.desc()).all()
            prizes = session.query(UserPrize).filter(UserPrize.user_id == user_id).order_by(UserPrize.date_claimed.desc()).all()

            blocks = create_paginated_blocks(session, activities, prizes, total_points, page)

            client.views_open(
                trigger_id=trigger_id,
                view={
                    "type": "modal",
                    "title": {"type": "plain_text", "text": "My BIP Stats"},
                    "blocks": blocks
                }
            )
    except Exception as e:
        print(f"Error opening My BIP view: {e}")
        # Handle error



def update_mybip_view(client, user_id, page, body):
    try:
        with session_scope() as session:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                channel_id = body.get("channel", {}).get("id")
                if channel_id:
                    client.chat_postEphemeral(channel=channel_id, user=user_id, text="User not found.")
                return

            total_points = user.total_points(session)
            activities = session.query(UserActivity).filter(UserActivity.user_id == user_id).order_by(UserActivity.date_achieved.desc()).all()
            prizes = session.query(UserPrize).filter(UserPrize.user_id == user_id).order_by(UserPrize.date_claimed.desc()).all()

            blocks = create_paginated_blocks(session, activities, prizes, total_points, page)
            view_id = body.get("view", {}).get("id")
            if not view_id:
                print("Error: View ID not found in body.")
                return  # Optionally, handle this situation differently

            client.views_update(
                trigger_id=body["trigger_id"],
                view_id=view_id,
                view={
                    "type": "modal",
                    "title": {"type": "plain_text", "text": "My BIP Stats"},
                    "blocks": blocks
                }
            )
    except Exception as e:
        print(f"Error updating My BIP view: {e}")
        channel_id = body.get("channel", {}).get("id")
        if channel_id:
            client.chat_postEphemeral(channel=channel_id, user=user_id, text="Error updating view.")

def create_paginated_blocks(session, activity_claims, prize_claims, total_points, page):
    # Combine and sort activity and prize claims
    combined_claims = sorted(
        [{'type': 'activity', 'claim': claim} for claim in activity_claims] +
        [{'type': 'prize', 'claim': claim} for claim in prize_claims],
        key=lambda x: x['claim'].date_claimed if x['type'] == 'prize' else x['claim'].date_achieved,
        reverse=True
    )

    start_index = (page - 1) * ITEMS_PER_PAGE
    end_index = start_index + ITEMS_PER_PAGE
    displayed_claims = combined_claims[start_index:end_index]

    blocks = [{"type": "section", "text": {"type": "mrkdwn", "text": f"*Your Total Points:* {round(total_points,2)}"}}]

    # Create blocks for each displayed claim
    for claim_dict in displayed_claims:
        if claim_dict['type'] == 'activity':
            activity = session.query(Activity).filter(Activity.id == claim_dict['claim'].activity_id).first()
            if activity:
                blocks.append({
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f":{activity.emoji}: {activity.title} - {activity.points} points (Awarded on {claim_dict['claim'].date_achieved.strftime('%m-%d-%y')})"}
                })
        elif claim_dict['type'] == 'prize':
            prize = session.query(Prize).filter(Prize.id == claim_dict['claim'].prize_id).first()
            if prize:
                blocks.append({
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f":gift: {prize.name} - {prize.cost} points (Claimed on {claim_dict['claim'].date_claimed.strftime('%m-%d-%y')})"}
                })

    # Add pagination buttons
    total_items = len(combined_claims)
    max_page = (total_items + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    if page < max_page:
        blocks.append({
            "type": "actions",
            "elements": [
                {"type": "button", "text": {"type": "plain_text", "text": "Next Page"}, "value": str(page + 1), "action_id": "next_page"}
            ]
        })
    if page > 1:
        blocks.append({
            "type": "actions",
            "elements": [
                {"type": "button", "text": {"type": "plain_text", "text": "Previous Page"}, "value": str(page - 1), "action_id": "prev_page"}
            ]
        })

    return blocks


# Handlers for next_page and prev_page actions
@bolt_app.action("next_page")
def handle_next_page(ack, body, client, action):
    ack()
    user_id = body["user"]["id"]
    page = int(action["value"])
    update_mybip_view(client, user_id, page, body)

@bolt_app.action("prev_page")
def handle_prev_page(ack, body, client, action):
    ack()
    user_id = body["user"]["id"]
    page = int(action["value"])
    update_mybip_view(client, user_id, page, body)
