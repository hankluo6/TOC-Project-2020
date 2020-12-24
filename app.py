import os
import sys

from flask import Flask, jsonify, request, abort, send_file
from dotenv import load_dotenv
from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, FlexSendMessage

from fsm import TocMachine

load_dotenv()

machine = TocMachine(
    states=["user", "start",
            "bus_start", "bus_by_stop", "bus_by_stop2", "bus_by_route", "bus_by_route2", "bus_direction", "bus_end",
            "train_start", "train_start_station", "train_end_station", "train_time",
            "hsr_start", "hsr_start_station", "hsr_end_station", "hsr_time"
            ],
    transitions=[
        {
            "trigger": "advance",
            "source": "user",
            "dest": "start",
            "conditions": "is_going_to_start",
        },
        {
            "trigger": "advance",
            "source": "start",
            "dest": "bus_start",
            "conditions": "is_going_to_bus_start",
        },
        {
            "trigger": "advance",
            "source": "bus_start",
            "dest": "bus_by_stop",
            "conditions": "going_bus_by_stop",
        },
        {
            "trigger": "advance",
            "source": "bus_by_stop",
            "dest": "bus_by_stop2",
            "conditions": "going_bus_by_stop2",
        },
        {
            "trigger": "advance",
            "source": "bus_start",
            "dest": "bus_by_route",
            "conditions": "goint_bus_by_route",
        },
        {
            "trigger": "advance",
            "source": "bus_by_route",
            "dest": "bus_by_route2",
            "conditions": "goint_bus_by_route2",
        },
        {
            "trigger": "advance",
            "source": ["bus_by_route2", "bus_by_stop2"],
            "dest": "bus_direction",
            "conditions": "going_bus_direction",
        },
        {
            "trigger": "advance",
            "source": "bus_direction",
            "dest": "bus_end",
            "conditions": "is_going_to_bus_end",
        },
        {
            "trigger": "advance",
            "source": "start",
            "dest": "train_start",
            "conditions": "is_going_to_train",
        },
        {
            "trigger": "advance",
            "source": "train_start",
            "dest": "train_start_station",
            "conditions": "going_train_start_station",
        },
        {
            "trigger": "advance",
            "source": "train_start_station",
            "dest": "train_end_station",
            "conditions": "going_train_end_station",
        },
        {
            "trigger": "advance",
            "source": "train_end_station",
            "dest": "train_time",
            "conditions": "going_train_time",
        },
        {
            "trigger": "advance",
            "source": "start",
            "dest": "hsr_start",
            "conditions": "is_going_to_hsr",
        },
        {
            "trigger": "advance",
            "source": "hsr_start",
            "dest": "hsr_start_station",
            "conditions": "going_hsr_start_station",
        },
        {
            "trigger": "advance",
            "source": "hsr_start_station",
            "dest": "hsr_end_station",
            "conditions": "going_hsr_end_station",
        },
        {
            "trigger": "advance",
            "source": "hsr_end_station",
            "dest": "hsr_time",
            "conditions": "going_hsr_time",
        },
        {
            "trigger": "reset",
            "source": "*",
            "dest": "user",
        },
    ],
    initial="user",
    auto_transitions=False,
    show_conditions=True,
)

app = Flask(__name__, static_url_path="")

# get channel_secret and channel_access_token from your environment variable
channel_secret = os.getenv("LINE_CHANNEL_SECRET", None)
channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", None)
if channel_secret is None:
    print("Specify LINE_CHANNEL_SECRET as environment variable.")
    sys.exit(1)
if channel_access_token is None:
    print("Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.")
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
parser = WebhookParser(channel_secret)


@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # parse webhook body
    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        abort(400)

    # if event is MessageEvent and message is TextMessage, then echo text
    for event in events:
        if not isinstance(event, MessageEvent):
            continue
        if not isinstance(event.message, TextMessage):
            continue

        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=event.message.text)
        )

    return "OK"


@app.route("/webhook", methods=["POST"])
def webhook_handler():
    signature = request.headers["X-Line-Signature"]
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info(f"Request body: {body}")

    # parse webhook body
    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        abort(400)

    # if event is MessageEvent and message is TextMessage, then echo text
    for event in events:
        print(f"\nFSM STATE: {machine.state}")
        print(f"REQUEST BODY: \n{body}")
        if event.type == 'message' and event.message.type == 'text' and event.message.text == 'reset':
            machine.reset()
        else:
            machine.advance(event)

    return "OK"


@app.route("/show-fsm", methods=["GET"])
def show_fsm():
    machine.get_graph().draw("fsm.png", prog="dot", format="png")
    return send_file("fsm.png", mimetype="image/png")


if __name__ == "__main__":
    port = os.environ.get("PORT", 8000)
    app.run(host="0.0.0.0", port=port, debug=True)
