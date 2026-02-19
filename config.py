import os

MONITORED_CHANNELS_NAMES = ["bip-testing", "bip-student-hype"]
SLACK_TOKEN = os.environ.get('SLACK_TOKEN')
SLACK_SIGNING_SECRET = os.environ.get('SLACK_SIGNING_SECRET')
SLACK_BOT_OAUTH = os.environ.get('SLACK_BOT_OAUTH')
BIP_ADMINS=[
    'email1@codingtemple.com',
    'email2@codingtemple.com',
    'email3@codingtemple.com'
    ]
MONITORED_CHANNELS=[]
WELCOME_ACTIVITY_ID=777
