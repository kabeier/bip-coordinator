from app import bolt_app
from models import session_scope, Activity


@bolt_app.command("/bip_help")  
def bip_help(ack, respond, command, client):
    ack()
    blocks = []
    blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": "*Build In Public*\nHere are the activities you can do to earn points. You can find the prizes by using /claimprizes in the channel. You can find all the commands by finding info page on the BIP-Coordinator in Slack."}
        })
    
    blocks.append({"type": "divider"})
    
    fallback_text = "Build In Public - Activities you can do to earn points."
    
    with session_scope() as session:
        activities = session.query(Activity).all()
        for activity in activities:
            rule_description = ""
            if activity.rewards_to_poster and activity.admin_reward:
                rule_description = f"A BIP Admin will reward you points for this activity by adding this emoji: :{activity.emoji}: {activity.emoji}"
            elif not activity.rewards_to_poster and not activity.admin_reward:
                rule_description = f"Receive points for this activity by using this emoji: :{activity.emoji}: {activity.emoji}"
            elif activity.rewards_to_poster and not activity.admin_reward:
                rule_description = f"Reward a classmate with points for completing this activity by adding this emoji: :{activity.emoji}: {activity.emoji}"
            elif not activity.rewards_to_poster and activity.admin_reward:
                continue  # Greedy admin, no need to show this activity to the users
            
            activity_block = {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*{activity.title}* - {activity.points} points\n{activity.description}\n{rule_description}"}
            }
            blocks.extend([activity_block, {"type": "divider"}])

    if len(blocks) == 2: 
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": "No activities available."}
        })

    client.chat_postEphemeral(
        channel=command["channel_id"],
        user=command["user_id"],
        blocks=blocks,
        text=fallback_text  
    )
