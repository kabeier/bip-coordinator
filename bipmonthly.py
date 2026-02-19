from datetime import datetime
import pytz
from app import bolt_app
from utility import get_user_name_and_email
from models import *
from sqlalchemy import func

# Month starts on the first day of the current month
def start_of_month():
    today = datetime.now(pytz.utc)
    start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    return start

@bolt_app.command("/bipmonth")
def handle_bipmonth_command(ack, body, client):
    ack()
    channel_id = body["channel_id"]

    start_of_this_month = start_of_month()
    current_time = datetime.now(pytz.utc)

    try:
        with session_scope() as session:
            # Query to get the total points per user for the current month
            monthly_points = (
                session.query(UserActivity.user_id, func.sum(Activity.points))
                .join(Activity)
                .filter(UserActivity.date_achieved >= start_of_this_month)
                .filter(UserActivity.date_achieved <= current_time)
                .group_by(UserActivity.user_id)
                .order_by(func.sum(Activity.points).desc())
                .limit(20)
                .all()
            )

            # Build the leaderboard blocks
            blocks = [{"type": "section", "text": {"type": "mrkdwn", "text": "*Monthly Leaderboard*"}}]
            for rank, (user_id, points) in enumerate(monthly_points, start=1):
                user_info = get_user_name_and_email(user_id)
                user_name = user_info[0] if user_info else "Unknown User"
                blocks.append({
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"{rank}. {user_name} - {round(points,2)} points"}
                })

            # Send ephemeral message
            client.chat_postEphemeral(channel=channel_id, user=body["user_id"], blocks=blocks)

    except Exception as e:
        print(f"Error processing /bipmonth command: {e}")
        client.chat_postEphemeral(channel=channel_id, user=body["user_id"], text="Error processing your request.")

