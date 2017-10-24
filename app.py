import os
import sys
import json
from datetime import datetime

import requests
from flask import Flask, request, render_template

app = Flask(__name__)


@app.route('/', methods=['GET'])
def verify():
    # when the endpoint is registered as a webhook, it must echo back
    # the 'hub.challenge' value it receives in the query arguments
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == os.environ["VERIFY_TOKEN"]:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200

    return render_template("index.html")


@app.route('/', methods=['POST'])
def webhook():

    # endpoint for processing incoming messaging events
    set_greeting_text()
    data = request.get_json()
    log(data)  # you may not want to log every incoming message in production, but it's good for testing

    if data["object"] == "page":

        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:
                sender_id = messaging_event["sender"]["id"]        # the facebook ID of the person sending you the message
                recipient_id = messaging_event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID
                message_text = messaging_event["message"]["text"]  # the message's text

                if messaging_event.get("message"):  # someone sent us a message
                    if message_text == "hi":
                        send_message(sender_id, "hi too, welcome on board")
                    elif message_text == "button":
                        send_button_message(sender_id)
                    elif message_text == "bye":
                        send_message(sender_id, "Thanks for visiting my bot")
                    else:
                        send_message(sender_id, "your message has been received! Thanks")

                if messaging_event.get("delivery"):  # delivery confirmation
                    pass

                if messaging_event.get("optin"):  # optin confirmation
                    pass

                if messaging_event.get("postback"):  # user clicked/tapped "postback" button in earlier message
                    received_postback(event)
                        
                        

    return "ok", 200
def set_greeting_text():
    # Sets greeting text on welcome screen
    data = json.dumps({
       "setting_type":"greeting",
       "greeting":{
           "text":"Hi {{user_first_name}}, welcome to this bot."
      }
    call_send_api(data)

def send_message(recipient_id, message_text):

    log("sending message to {recipient}: {text}".format(recipient=recipient_id, text=message_text))

    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": message_text
        }
    })
    call_send_api(data)

def send_button_message(recipient_id):
    
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "attachment": {
                "type":"template",
                "payload":{
                    "template_type":"button",
                    "text":"What do you want to do next?",
                    "buttons":[
                    {
                        "type":"postback",
                        "title":"Find a bot",
                        "payload":"find()"
                    },
                    {
                        "type":"postback",
                        "title":"Do nothing",
                        "payload":"nothing()"
                    }
                    ]
                }
            }
        }
    })

    log("sending button to {recipient}: ".format(recipient=recipient_id))

    call_send_api(data)


def received_postback(event):

    sender_id = event["sender"]["id"]        # the facebook ID of the person sending you the message
    recipient_id = event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID

    # The payload param is a developer-defined field which is set in a postback
    # button for Structured Messages
    payload = event["postback"]["payload"]

    log("received postback from {recipient} with payload {payload}".format(recipient=recipient_id, payload=payload))

    if payload == 'Get Started':
        message_text = messaging_event["message"]["text"]  # the message's text
        # Get Started button was pressed
        send_message(sender_id, "Welcome to SoCal Echo Bot!")
    else:
        message_text = messaging_event["message"]["text"]  # the message's text
        # Notify sender that postback was successful
        send_message(sender_id, "Postback called")

def call_send_api(data):
    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)
    

def log(msg, *args, **kwargs):  # simple wrapper for logging to stdout on heroku
    try:
        if type(msg) is dict:
            msg = json.dumps(msg)
        else:
            msg = unicode(msg).format(*args, **kwargs)
        print u"{}: {}".format(datetime.now(), msg)
    except UnicodeEncodeError:
        pass  # squash logging errors in case of non-ascii text
    sys.stdout.flush()


if __name__ == '__main__':
    app.run(debug=True)