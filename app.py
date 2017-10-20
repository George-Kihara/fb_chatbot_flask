import os
import sys
import json
from datetime import datetime

import requests
from flask import Flask, request

app = Flask(__name__)

@app.route('/', methods=['GET'])
def verify():
    #when the endpoint is registered as a webhook, it must echo back
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == os.environ["VERIFY_TOKEN"]:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200

    return "Welcome to fb chatbot", 200

@app.route('/', methods=['POST'])
def webhook():
    #endpoint for processing incoming messaging events

    data = request.get_json()
    log(data) #for optional logging message

    if data["object"] == "page":
        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:
                if messaging_event.get("message"): #someone sent a message
                    sender_id = messaging_event["sender"]["id"] #the facebook id of the person sending the message
                    recipient_id = messaging_event["recipient"]["id"] #my page's facebook id
                    message_text = messaging_event["message"]["text"]

                    send_message(sender_id, "your text has been received")
                if messaging_event.get("delivery"): #delivery confirmation
                    pass
                if messaging_event.get("optin"): #optin confirmation
                    pass
                if messaging_event.get("postback"): #user clicked a postback button in the earlier messages
                    pass

    return "ok", 200

def send_message(recipient_id, message_text):
    log("sending message to {recipient}: {text}".format(recipient_id, text=message_text))

    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content_Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": message_text
        }
    })
    r = request.post("https://graph.facebook.com/v2.6/me/messages",params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)

def log(msg, *args, **kwargs):  #simple wrapper for logging to stdout on heroku
    try:
        if type(msg) is dict:
            msg = json.dumps(msg)
        else:
            msg = unicode(msg).format(*args, **kwargs)
        print u"{}: {}".format(datetime.now(), msg)
    except UnicodeEncodeError:
        pass # squashing logging errors in case of non-ascii text
    sys.stdout.flush()

if __name__=='__main__':
    app.run(debug=True)