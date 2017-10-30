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

    data = request.get_json()
    log(data)  # you may not want to log every incoming message in production, but it's good for testing

    if data["object"] == "page":   # make sure this is a page subscription

        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:

                if messaging_event.get("message"):     # someone sent us a message
                    received_message(messaging_event)

                elif messaging_event.get("delivery"):  # delivery confirmation
                    pass
                    # received_delivery_confirmation(messaging_event)

                elif messaging_event.get("optin"):     # optin confirmation
                    pass
                    # received_authentication(messaging_event)

                elif messaging_event.get("postback"):  # user clicked/tapped "postback" button in earlier message
                    received_postback(messaging_event)

                else:    # uknown messaging_event
                    log("Webhook received unknown messaging_event: " + messaging_event)

    return "ok", 200

def received_message(event):
    
    sender_id = event["sender"]["id"]        # the facebook ID of the person sending you the message
    recipient_id = event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID
    
    # could receive text or attachment but not both
    if "text" in event["message"]:
        message_text = event["message"]["text"]

        # parse message_text and give appropriate response   
        if message_text == 'image':
            send_image_message(sender_id)

        elif message_text == 'file':
            send_file_message(sender_id)

        elif message_text == 'audio':
            send_audio_message(sender_id)

        elif message_text == 'video':
            send_video_message(sender_id)

        elif message_text == 'button':
            send_button_message(sender_id)

        elif message_text == 'generic':
            send_generic_message(sender_id)

        elif message_text == 'share':
            send_share_message(sender_id)

        else: # default case
            send_message(sender_id, "Echo: " + message_text)

    elif "attachments" in event["message"]:
        message_attachments = event["message"]["attachments"]   
        send_message(sender_id, "Message with attachment received")


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
                        "payload":"Find a bot"
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

def send_button_category(recipient_id):
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "attachment": {
                "type":"template",
                "payload":{
                    "template_type":"button",
                    "text":"What category of bot?",
                    "buttons":[
                    {
                        "type":"postback",
                        "title":"Games",
                        "payload":"Games"
                    },
                    {
                        "type":"postback",
                        "title":"Health",
                        "payload":"Health"
                    },
                    {
                        "type":"postback",
                        "title":"Community",
                        "payload":"Community"
                    }
                    ]
                }
            }
        }
    })

    log("sending category button to {recipient}: ".format(recipient=recipient_id))

    call_send_api(data)

def send_button_community(recipient_id):
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "attachment": {
                "type":"template",
                "payload":{
                    "template_type":"button",
                    "text":"Here is the list of community bots",
                    "buttons":[
                    {
                        "type":"web_url",
                        "url":"https://m.me/Comrades_nature",
                        "title":"Comrades_nature"
                    },
                    {
                        "type":"web_url",
                        "url":"https://m.me/Botstore",
                        "title":"Botstore"
                    },
                    {
                        "type":"web_url",
                        "title":"Ggflaskbot",
                        "url":"https://m.me/Ggflaskbot"
                    }
                    ]
                }
            }
        }
    })

    log("sending community button to {recipient}: ".format(recipient=recipient_id))

    call_send_api(data)

def send_generic_message(recipient_id):
    
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "generic",
                    "elements": [{
                        "title": "Comrades_nature",
                        "subtitle": "A bot to help comrades solve their nature problems",
                        "item_url": "https://m.me/Comrades_nature",               
                        "image_url": "",
                        "buttons": [{
                            "type": "web_url",
                            "url": "https://m.me/Comrades_nature",
                            "title": "Visit the bot"
                        }],
                    }, {
                        "title": "Botstore",
                        "subtitle": "Find all bots on facebook",
                        "item_url": "https://m.me/Botstore",               
                        "image_url": "",
                        "buttons": [{
                            "type": "web_url",
                            "url": "https://m.me/Botstore",
                            "title": "Visit the bot"
                        }]
                    }]
                }
            }
        }
    })

    log("sending template with choices to {recipient}: ".format(recipient=recipient_id))

    call_send_api(data)

def send_generic_category(recipient_id):
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "generic",
                    "elements": [{
                        "title": "Bots category",
                        "subtitle": "Please select one of the categories",
                        "buttons": [{
                            "type": "postback",
                            "title":"Community",
                            "payload":"Community"
                        },{
                            "type": "postback",
                            "title": "Games",
                            "payload": "Games"
                        },{
                            "type": "postback",
                            "title": "Health",
                            "payload": "Health"
                        }
                        ]
                    }]
                }
            }
        }
    })

    log("sending template with choices to {recipient}: ".format(recipient=recipient_id))

    call_send_api(data)

def received_postback(event):

    sender_id = event["sender"]["id"]        # the facebook ID of the person sending you the message
    recipient_id = event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID

    # The payload param is a developer-defined field which is set in a postback
    # button for Structured Messages
    payload = event["postback"]["payload"]
    user_details_url = "https://graph.facebook.com/v2.6/%s"%sender_id
    user_details_params = {'fields':'first_name,last_name,profile_pic', 'access_token':os.environ["PAGE_ACCESS_TOKEN"]}
    user_details = requests.get(user_details_url, user_details_params).json()

    if payload == 'Get Started':
        # Get Started button was pressed
        send_message(sender_id, "Welcome {} {} to bot store. You will find all facebook bots here.".format(user_details['first_name'], user_details['last_name']))
        send_generic_category(sender_id)
    elif payload == 'Find a bot':
        send_button_category(sender_id)
    elif payload == 'Community':
        send_generic_message(sender_id)
    elif payload == 'Games':
        send_button_category(sender_id)
    else:
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
    

def log(message):  # simple wrapper for logging to stdout on heroku
    print (str(message))
    sys.stdout.flush()


if __name__ == '__main__':
    app.run(debug=True)