from app import bolt_app
from utility import get_user_name_and_email
from models import *
from sqlalchemy import func

@bolt_app.command("/bipalltime")
def handle_bipalltime_command(ack, body, client):
    ack()
    channel_id = body["channel_id"]

    try:
        with session_scope() as session:
            # Query to get the total points per user for all time
            all_time_points = (
                session.query(UserActivity.user_id, func.sum(Activity.points))
                .join(Activity)
                .group_by(UserActivity.user_id)
                .order_by(func.sum(Activity.points).desc())
                .limit(20)
                .all()
            )

            # Build the leaderboard blocks
            blocks = [{"type": "section", "text": {"type": "mrkdwn", "text": "*All-Time Leaderboard*"}}]
            for rank, (user_id, points) in enumerate(all_time_points, start=1):
                user_info = get_user_name_and_email(user_id)
                user_name = user_info[0] if user_info else "Unknown User"
                blocks.append({
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"{rank}. {user_name} - {round(points,2)} points"}
                })

            # Send ephemeral message
            client.chat_postEphemeral(channel=channel_id, user=body["user_id"], blocks=blocks)

    except Exception as e:
        print(f"Error processing /bipalltime command: {e}")
        client.chat_postEphemeral(channel=channel_id, user=body["user_id"], text="Error processing your request.")

