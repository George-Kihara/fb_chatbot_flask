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




def send_greeting():
    #set greeting message on welcome screen
    log("sending message to {recipient}: {text}".format(recipient=recipient_id))

    data = json.dumps({
        "setting_type":"greeting",
        "greeting":{
            "text":"Hi {{user_first_name}}, welcome to this bot."
        }
    })
    
    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    
    r = requests.post("https://graph.facebook.com/v2.6/me/thread_settings", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log("setting greeting text")
        log(r.status_code)
        log(r.text)

    return "ok", 200

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

def send_image_message(recipient_id):
    
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "attachment": {
                "type":"image",
                "payload":{
                    "subtitle":"Welcome home",
                    "url":"data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wCEAAkGBxITEhUREhIVFhUSFRcWFxcYFRUXFRYdFRcWFxYVFRgYISsgGh0lGxcVJzEhJSktLi4uFx81ODMtNygtLisBCgoKDg0OGhAQGi0lICUrLS4tLS0uLS0tLS0tLS03LS0tLi0tLSstLS0tLS8tLS0tLS0tLTUtLS0tLS0tLS0tLf/AABEIAKcBLgMBIgACEQEDEQH/xAAcAAEAAgMBAQEAAAAAAAAAAAAABAYDBQcBCAL/xABEEAACAQIDBAcEBggEBwEAAAABAgADEQQSIQUGMUETIlFhcYGRBzJSoRQVI0KxwTNicoKSstHwosLh8RYkNENEU3MI/8QAGgEBAAMBAQEAAAAAAAAAAAAAAAECAwQFBv/EAC0RAQACAgECBAMIAwAAAAAAAAABAgMRMQQhEhNBUWHB8BQiMnGhsdHhM0KR/9oADAMBAAIRAxEAPwDi0REsqREQEREBERAREQEREBEQTARPMw7Z7AREEwETcYHdfG1henhqhHawCA+Bci82h9m+1cnSDCFl192pSZtP1Q1z5QhU4mbGYSpSbJWpvTb4XRkb0YAyXhtg4uouanha7KRcEUnsR2qba+UJa6JJxmz61KwrUalO/DPTdL+GYC8jQEREBERAREQEREBERAREQEREBERAREQEREBERAREQEREBOwew/dlGD4yqobNdaYOoABsT5sD/B3zj87j7ONqYgYGkcPhazoiZXZehsSrMDkVnDNbXgL9l4jlE8OonDpbLkWx5ZRb0nIva57PsPToPj8KgpGmVNWmulNlYhc6LwUgkXA0Ivz4yn9pGEL1nxOLr5abBaVDDK6Z1CIxqPUFjmLlhlzgALqJUN/fafVx9NsNSp9Dh2IzXOapUykEBjwUXANhfhx5S0zGmdazEufztW5W72FpYejWSmGqVKaOajC7XZQTlv7o14D5zjFGmznKilj2KCx9BO4bi5/oNBaisrIpUhgQbKzBdD+raVabb6WbYZ+xXxb8TKzLLsE/ZD9oyacqX4ScdgqVZTTrU0qIfuuquvo0h1tiUiOpdLaC2q+hkHF7Wqh2AIUKSLWB4HneTdl7U6Q5HADciOBtx07ZbcSrq0RtU/aBsiv9X4imlI186rZUBYgh1OcLxuoBOk+emBBIIsQbEHQgjiCJ9iyu707k4LHgmvSAqW0rJZao7Ln7w7mBEia+yYv7vluJb9+PZ9idnHOftcOTYVlFrX4Cqv3D36g9t9JUJVpvZERCSIiAiIgIiICIiAiIgIiICIiAiIgIiICIiAiIgCZ9T7hbP+j7Pw1IixWmC37R1b5z5o3ewXTYqhRtcPVUEfqg3b/CDPrKmmVAvwrb0EtXlnkns+VNi7vYjFHMiWQkk1G0Xjrbmx8JeNlbiYanY1b1m7+qnko4+ZMtFNQAABYAWAGgHcJ+p2Uw1rz3eXl6u9+O0MeHw6UxlpoqAclAUegmywDaEdh/GQZKwDakdo/CM0bpKvS21ljadLHu+fsj+2fwErk2+w8cqAoxtc3BPDgAQezhOKvL17x2bLGbNp1Dc3Ddo5+PbPzgtlpTOa5J5XtpeTVYEXBBHaNRPZfUMtzww4qizDquUI5ixHmOcj0TiFNmCuO0HK3odJOiTo2qntUxq0tlYosL9IgpKO+owUHyuT+7PmSdt/8A0FjGFHDUADlao1RzrYFVyoCe/M/8M4lM7ctacF4n0L7JsPgKWAp1qAFSsyg4hlU1K6seKFVBcKvAADUa63vIntgweHxOA6emyF6NqisvNTbMCewj52jXZPi76cFiIkLEREBERAREQEREBERAREQEREBERAREQE9AvoNSdAOZ7hPJefZ5sDMfpdQaAkUgeZGhqeWoHfc8hLUrNp1DPLkjHXxSsvsx3QFKqlasL1jwHKkDxA/WIvc+Q537LXPVY/qn8JTt26iI+dzYC/K/Lu8TN++L+kHoqYOT/uvw0+Be8/IXmsxEW1Dmra00i0+qjCey5Vt2KB4F18GuPmJCrbpn7lUeDLb5g/lOmMtXBPTZI9FanqMQbjlNvW3bxA4BW8GH+a0g1tm1l96k4/dJHqNJbxVlSaXr31LJTxo5i34SSjA8DeaunRZjZVJPYASfQSZhtmV8wbonFiDcqRwPfML4Kek6deLq8nExtvaWya66qwU9gYg/LSPrOvTOV7EjkR+YlhvzlV3kr5a2oNioseXOYeCf9XbOSsfjbSjt1D7ykeGok6jjqbcHXzNj6GUhsaOQP4TDUxbHul648ksb9RhjiWbep0xFR1YB6dgljqCBx+ZOs4rvXu82EqXFzSc9Ruz9Ru/8R5zrkjbSwKV6bUqguri3eOxh3gze+KLV048XUzS+54nlxPD13psHpuyMODKxVh4Eazsm7Ow6eL2BVqPTV8QUr5arC9W9MtkGc9awta3DWci2ts58PVai/FDoeTA8GHcRPoH2NpfZFJfiauPWo4nFEd9S9a1u0TD5zBiS9r4Toa9Wja3R1HUeAYgfK0iSFyIiAiIgIiICIiAiIgIiICIiAiIgIiIE3Y2z2xFZKK/fOp+FRqzeQv52naMPRVFVEFlQBVHYALASkezHZ+lXEkcT0S+Vmc+uUeRl7nZgrqu/d5PW5PFfw+z9JUI4HjNjgtuVaYCrbKOVhaayJtNInlzVy3rxK04feoffTzH9JsqO3aDfeI8R/S8okTKcMekt69Xb1h0VMdSPCovmbfjMvTrxzL6ic5Ssw4E/34yWnSED3Rfu1mVsc15mHTjz1vxEtttjGBq90PuKBmHbckWlntca8xrKZhKPWVeOZhc9tyBLdVxIBygFm45V5eJOg8zM97lv4ZiIZVW2kVEDCzAEHkRcehmLpm/9beRT+sfSRzVx+6T/AC3ko01OP3ZpvrTOQ9nFfTiPL0lZx2zatI2ddPiGqnz/AKy+jFJ8QHjofQz9seBH9g/2PSaVyzDnv01bcdnPKWAqt7tJz+61vWTKW7+IP/bt4so/O8uOMxyU7Zydb20vwmsrbzURwDH0/K8t51p4hT7LSve0/JTN5fZe+MyMa1Ok6XGbKz3U65SNOB4a8zNvuan1WBszE1ARc1MNWyFFqhutUpEXNqivmNr6qQeRkzEb1OfcQDx1M4vvrvrtCtUq4avUUIjkZFpqAbG6Prcg2sQQQReZZImPvTDpwWpMeCs8MPtTwyptKsVN1qZag8xl/wAt/OVKZMRiHds9R2djxZmLMbcNTrMcxdZERAREQEREBERAREQEREBERAREQERGW+g4nT1gdi3SwvR4OivMoHPjU65/m+U288RMoCj7oA9NJ7PTiNRp89e3itMkRElUiIgeqLm3bNuBNbhFuw7tZspx9TPeIep0FfuzZK2Yt6qftX9Nfym/o5srlAuY1G969rA5eXcJpdhresvcCflb85usIjFFKtl6xY6A3BZjbXhx4zGrqvymT8hz8JH8P9Z+mmELbkB++f6S7NmvMOWwIGgLfiQD87zS7V3zwGHuHxClh9yneo1+w5dB5kSl7X9rN9MNh7W1DVT4/cQ/5paKzKs5KxzKz744gNURB9wEnxa2noB6yqYzadGl+kqKD2Xu38I1lH2lt/E12ZqlU9ckkL1V15WHEeM1s6a9o08+9fFabSuGL3vQaUqZbvY5R6C5PylA3lxLVaxqsFBcC+UWHV0591pPmu2wNFPeR6/7TPN3q36XVckaayIicb1CIiAiIgIiICIiAiIgIiICIiAiIgJmwf6RP20/mEwxmtqOI19NYQ70Z5PEe4DDmL+us9nqPnSIiAiJjr4hEF3ZVHaSB+MCfs9eJ8pNlUffHDUlsoao1zwFl82b8gZo8fvviH0phaQ7hmb1bT5TiyY7XvMvWw5aY8cRPLrGxKiozuxCqqG5JAA1HEma3Fb/AGCoLTArmoVTrU6SZ7kj4zZRY9hnGcXjKlU3qOzn9Yk28L8Jhl64dcqX6iZ4h0Ta/tXrvdaFCnTB5v8AaN420Ued5TNp7dxOI/TV3cfDfKn8C2X5TXRNYrEMJvaeZeT2IkqkREBIG1/dH7X5GT5rtsHRR3k+n+8pl/BLXB/khrIiJxPUIiICIiAiIgIiICIiAiIgIiICIiAiJkw9BnZUQZmY2UDiSeUIdf3UxfS4Sg99QgU+KdQ/yzbTm+zdqYrZ1ApUwzWdyVZj1VJAuunhfiOch4vfKvU4lgOxTlHy19TO2uWsRETy8m/S3taZrw6Xi8fSp/pKir3E6+QGs0uL3upjSmjOe09Vf6/KUvosR0X0j6M/R2zZ7jh8VuNu+1pA+tB8B9ZM5aor0tp+P/Fpxe8uIfgwQdiCx9TrNTUcsbsST2kkn1MYXB4qoi1KeGdlYXBDLY8uc19baBVmRqZDKSpFxoVNiPWJyV9V64LcRH7J0TXfWg+A+sfWg+A+sjzae632fJ7NjEw1TVWktdqDCm9sr3Fje9u/kZE+tB8B9Y8yqIwXniGxie4bC4mogq08M7IQSCCDexINhx4gzW/Wg+A+v+keZWCMN54+TYxMezxWr3NGgz5bA2K6X4cZhxmJek5p1KRVxa4JFxcXHDujzK8nk33r1/OEqJHwFSpWYrRos7AZiARoLgX18RPxUxLqi1TSYI5IVrixK6MO3SPMqeTfetfslzUbWe7gdg/H+xM31qPgPrMW0MBWUCtUpsqVbFGNrG4uP8Myy3ia6hvgxTW27IMRE53aREQEREBERAREQEREBERAREQEREBNpuv/ANZh/wD6rNXJuxcUtLEUqr3y03DG2psOwSa8wreN1n8ly3nUrhMUBV6bPi7mzXFAZgQhub8QBYds5+3Ay1bZ25hTRr08P0rNiqoquzhQq2YPZbd4/wBZVTwl8sxM9mXT1mK9/f8Ah09ajfTRTucn1dfLc5fete3DhOYLwEuy70YX/qbVPpAw3QZLDo+3Nm7L/LlKSsZJieFcFZje49vmtW6+Jf6Jjuu3UpJl6x6utT3ezylXZiSSSSSbknUkniSZt9jbTp0qGLpvfNXpqqWFxcZ73PLiJp7ytp7Q0pXVrT8flBPCZ7efujlzLm93MM1tdLi/yvKtXQdtp/yVXCjjhcPhX87kt8l+c53Ltid8qdR8RTdbUatJkpkJ9pcqAM+vDVvDSUi80yzEz2c/T1tWJi0fH9HSt28O7YfAMtQKENYsuYg1Bmbqqo978pz/AGnUzVqrWIzVahsRYi7k2I5ETfYLb9FEwKnNfDPUNTq8nJtl114zQ7Trq9arUX3alR2W+hszEi48DJvaJiNfXaEYaTF5mfrvKy7o082DxiiqKN2pfaMxULrzI4X4ecrO0FIqMDVFXKbdIGLBrcwTxE2+7+0cMlDEYfEGoBXKG6KCbIb89BraajaIoioRQZzT0salg/DW9tON5W0x4YXpExe316QsO4GJ6OpiKp4U8M7n91lP5SZv3hRSoUUHDp67Dwclx8mlf2DtBKIxAe/22HqUlsL9ZrWv2Dvkvb+3Ur4bDU+t0lEWe40PVCgg872lotHg19cs5pbzot6f00AQnqjidB4nQToO+dnw1ZB/4deiB4Gki/i7eko2zKyJWpO/upURmsLmysCbDyllxu9qVqeLpVVAWrfoSqWY2YlekN+Oia+MikxETErZa2m9ZiOP5hUYiJm6CIiAiIgIiICIiAiIgIiICIiAiIgJJ2biBTqpUa5Cm5tx4Eaajt7RI0QiY22FTGocQtbKSoamSCNTkVQxsSeYJ1J7zMOOxOZlZWYlVAzto7EEkObE6i4HEnqiRYjaNJmPxvSVukJYi62vYkBbXFjccb6cNZ7tbFiq4cZvdsbi2t2OgzMQLEcWPpYCFEbNQl7NxnRMzWJJRlGpGptYkgggacjeeYLE5WYlmUupAddXQllYsLkcQGF736xkWCY2nSdSxwWu9YLYE1iq8LdIrhfdItYsOB5aTBj6weq7qCA7FgDa4vrbSMLhHqBzTXN0SGo9iOqqkAtrxsWHDXWbP/hTGcehGlr/AGtHmQoHv8SxCgcSbjiCI2ahCwWLCU6qEsDUy2Iv90VAQbMvHMONxpwjAY0U1cEEki6EW6r5WS5vyyuT4qsnpuhjSARRFibA9NQy3DZbZs9ve077jtExHdrFZ0p9GuaozKo6WiblFzvwfSw4k6A6cdJO5RqJRcDi1SnVQlgamWxW/wB0VAQbMvxDjcaaiZNlbQWkrqyk9JYG3IBKqnS4B1ddDcaHukwbnY7T/lz1uH2lLXqlj97sHrYcSBMT7sYtVLtSCqucEtVoj9ECXsC9zYKeHZGyYiULZ2M6MPpcsvV0ByuPdfXgQC/rPNnYw0i9iwzU2Xqm2pFlJ15GRAw7Z7I2nSbs3GLTzZkzZslhrbquGJ0IPAT8rilz1msbVFqBeGmc3F/9JEiNo1DabL2ilNGR0LXZmBFuqTTKKRc9pNx2G/ECYtj41aV82bUobqASQubMhuRocynmOoLgyBEnZ4YeAT2IkLEREBERAREQEREBERAREQEREBERAREQEREBERATPhcZUp36OoyZrXysRe3C9vExECRhts1kNVg+Zq9JqLs4zMUYWIBPDlr3CbD/AIwxRBDGm2YMDmphtGBXLryAZwB2ORqLWRCH7r764x8t2TqkkdTtqLV1116yr8+ZJOCvvViW1uqm7NmVSGu9I0S2a9wchNrcNOSqAiBJp7840BRmT7P3b0x8GQX7dMv8C8rgxsZvTiai5H6Mjr6imoYdKmSrY8s18x/WseQARA19TaldlKNWqFSLFS7EEdlpEiISREQEREBERAREQEREBERAREQP/9k="
                }
            }
        }
    })

    log("sending image to {recipient}: ".format(recipient=recipient_id))

    call_send_api(data)

def send_file_message(recipient_id):
    
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "attachment": {
                "type":"file",
                "payload":{
                    "url":"http://ee.usc.edu/~redekopp/ee355/EE355_Syllabus.pdf"
                }
            }
        }
    })

    log("sending file to {recipient}: ".format(recipient=recipient_id))

    call_send_api(data)


def send_audio_message(recipient_id):

    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "attachment": {
                "type":"audio",
                "payload":{
                    "url":"http://www.stephaniequinn.com/Music/Allegro%20from%20Duet%20in%20C%20Major.mp3"
                }
            }
        }
    })

    log("sending audio to {recipient}: ".format(recipient=recipient_id))

    call_send_api(data)


def send_video_message(recipient_id):

    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "attachment": {
                "type":"video",
                "payload":{
                    "url":"http://techslides.com/demos/sample-videos/small.mp4"
                }
            }
        }
    })

    log("sending video to {recipient}: ".format(recipient=recipient_id))

    call_send_api(data)

def send_share_message(recipient_id):
    
    # Share button only works with Generic Template
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "attachment": {
                "type":"template",
                "payload":{
                    "template_type":"generic",
                    "elements":[
                    {
                        "title":"Reddit link",
                        "subtitle":"Something funny or interesting",
                        "image_url":"https://pbs.twimg.com/profile_images/667516091330002944/wOaS8FKS.png",
                        "buttons":[
                        {
                            "type":"element_share"
                        }
                        ]
                    }    
                    ]
                }
        
            }
        }
    })

    log("sending share button to {recipient}: ".format(recipient=recipient_id))

    call_send_api(data)


def received_postback(event):

    sender_id = event["sender"]["id"]        # the facebook ID of the person sending you the message
    recipient_id = event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID

    # The payload param is a developer-defined field which is set in a postback
    # button for Structured Messages
    payload = event["postback"]["payload"]

    if payload == 'Get Started':
        # Get Started button was pressed
        send_message(sender_id, "Hi {{user_first_name}}, welcome to bot store. You will find all facebook bots here.")
        send_image_message(sender_id)
    elif payload == 'Find a bot':
        send_message(sender_id, "What is the category of the bot?")
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