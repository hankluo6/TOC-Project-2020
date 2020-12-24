import os

from linebot import LineBotApi, WebhookParser
from linebot.models import MessageEvent, TextMessage, TextSendMessage, FlexSendMessage

channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", None)


def send_text_message(reply_token, text):
    line_bot_api = LineBotApi(channel_access_token)
    line_bot_api.reply_message(reply_token, TextSendMessage(text=text))

    return "OK"


def push_text_message(user_id, text):
    line_bot_api = LineBotApi(channel_access_token)
    line_bot_api.push_message(user_id, TextSendMessage(text=text))

    return "OK"


def send_flex_message(reply_token, contents):
    line_bot_api = LineBotApi(channel_access_token)
    line_bot_api.reply_message(
        reply_token,
        FlexSendMessage(
            alt_text='有新訊息',
            contents=contents
        )
    )
    return "OK"


def push_flex_message(user_id, contents):
    line_bot_api = LineBotApi(channel_access_token)
    line_bot_api.push_message(
        user_id,
        FlexSendMessage(
            alt_text='有新訊息',
            contents=contents
        )
    )
    return "OK"


"""
def send_image_url(id, img_url):
    pass

def send_button_message(id, text, buttons):
    pass
"""
