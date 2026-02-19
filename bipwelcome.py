
from app import bolt_app
from models import User, UserActivity, UserPrize, Activity, Prize, session_scope
from utility import get_user_name_and_email
from config import MONITORED_CHANNELS, WELCOME_ACTIVITY_ID

# welcome_message_blocks= [
#             {
#                 "type": "section",
#                 "text": {
#                     "type": "mrkdwn",
#                     "text": (
#                         "Welcome to BIP Slack Channel. This is the channel you’ll use to amplify your BIP posts, "
#                         "and earn and manage your BIP rewards points.\n\n"
#                         "*Please see the following key for earning points*\n"
#                         "Rules:\n"
#                         "- Do not share multiple posts in one message. Send one slack message for each post. "
#                         "This is to ensure that engagement activity and points are tracked properly.\n\n"
#                         "- Follow us on LinkedIn using the button below."
#                     )
#                 }
#             },
#             {
#                 "type": "actions",
#                 "elements": [
#                     {
#                         "type": "button",
#                         "text": {"type": "plain_text", "text": "Follow on LinkedIn"},
#                         "url": "https://www.linkedin.com/school/coding-temple/",
#                         "action_id": "follow_linkedin"
#                     }
#                 ]
#             }
#         ]
welcome_message_blocks = [
    {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": (
                "_Welcome to your Building In Public Hype Slack Channel! This is the channel you’ll use to share your BIP posts,_ "
                "_earn/manage your BIP rewards points, and claim prizes from those points. *BIP reward points are digital points you earn_ "
                "_when you participate and engage in our Building In Public Program (AKA being active on LinkedIn), in which you can use to claim prizes._*\n\n"
                "*1. See the <https://ct-buildinginpublic.notion.site/Building-In-Public-Student-Rewards-Guide-eebeb2f6d21042dda5b735348d3672dd|Building In Public Student Rewards Guide> to understand*\n"
                "\t• How to properly earn and accumulate reward points\n"
                "\t• How to track and manage your reward points/prizes\n"
                "\t• How to claim prizes with your points (gift cards, CT store promos, etc)\n\n"
                "*2. See the <https://ct-buildinginpublic.notion.site/Building-In-Public-Student-Rewards-Bank-8b16d6da15f94a8784a3a5f8c22ecf51|Building In Public Student Rewards Bank> to understand *\n"
                "\t• What kinds of reward challenges you can complete + the # of points they’re worth\n"
                "\t• What kinds of prizes you can claim + the # of points they’ll cost\n\n"
                "*_Please make sure you send only one slack message for each BIP LinkedIn post link you share. (Example: you want to share 3 posts, you will send 3 separate slack messages for each link). This is to ensure that engagement activity and points are tracked properly!_*\n\n"
                "_Most importantly, we want you to have fun with this!_ \n _This is our way of rewarding you for the time and effort you choose to invest into building your LinkedIn, and expanding your professional network/portfolio._ \n\n *For 2 FREE POINTS follow Coding Temple on LinkedIn and add us to your LinkedIn education!* :rocket:"
            )
        }
    },
    {
        "type": "actions",
        "elements": [
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "Follow on LinkedIn"},
                "url": "https://www.linkedin.com/school/coding-temple/",
                "action_id": "follow_linkedin"
            }
        ]
    }
]


@bolt_app.event({"type": "message", "subtype": "channel_join"})
def handle_member_joined_channel(event, client):
    user_id = event["user"]
    channel_id = event["channel"]

    if channel_id in MONITORED_CHANNELS:

        client.chat_postEphemeral(
            channel=channel_id,
            user=user_id,
            blocks=welcome_message_blocks,
            text="Welcome to the BIP Slack Channel!"  # Fallback text for notifications
        )
        res = client.conversations_open(users=[user_id])
        dm_channel_id = res["channel"]["id"]

        client.chat_postMessage(
            channel=dm_channel_id,
            blocks=welcome_message_blocks,
            text="Welcome to the BIP Slack Channel!"  # Fallback text for notifications
        )
@bolt_app.command("/welcomebip")
def handle_welcomebip_command(ack, body, client):
    ack()
    user_id = body["user_id"]

    client.views_open(
        trigger_id=body["trigger_id"],
        view={
            "type": "modal",
            "title": {"type": "plain_text", "text": "Welcome to BIP!"},
            "blocks": welcome_message_blocks
        }
    )

@bolt_app.action("follow_linkedin")
def handle_follow_linkedin(ack, body, client):
    ack()
    user_id = body["user"]["id"]

    try:
        with session_scope() as session:
            # Assuming the activity with ID 678 exists
            activity = session.query(Activity).filter(Activity.id == WELCOME_ACTIVITY_ID).first()
            if activity:
                user = session.query(User).filter(User.id == user_id).first()
                if not user:
                    user_info = get_user_name_and_email(user_id)
                    if user_info:
                        reacting_user = User(
                            id=user_id,
                            full_name=user_info[0],
                            email=user_info[1]
                        )
                        session.add(reacting_user)
                        reacting_user.activities.append(activity)
                        session.commit()
                                        # Send a confirmation message
                        client.chat_postMessage(
                            channel=user_id,
                            text=f"Thank you for following us on LinkedIn! You've earned points for activity: {activity.title}."
                        )
            else:    
                user.activities.append(activity)
                session.commit()

                # Send a confirmation message
                client.chat_postMessage(
                    channel=user_id,
                    text=f"Thank you for following us on LinkedIn! You've earned points for activity: {activity.title}."
                )
    except Exception as e:
        print(f"Error handling LinkedIn follow: {e}")
        # Handle error
