from slack_bolt import App
from config import *

bolt_app = App(token=SLACK_TOKEN, signing_secret=SLACK_SIGNING_SECRET)