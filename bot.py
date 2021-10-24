import random
import re
import os, sys, time
import requests
import base64
import json

from flask import Flask
from tinydb import TinyDB, Query

from dotenv import load_dotenv
load_dotenv()

import sendgrid
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition, ContentId

from matrix_bot_api.matrix_bot_api import MatrixBotAPI
from matrix_bot_api.mregex_handler import MRegexHandler
from matrix_bot_api.mcommand_handler import MCommandHandler
from matrix_bot_api.mhandler import MHandler

print(os.environ["DATABASE_PATH"], type(os.environ["DATABASE_PATH"]))

db = TinyDB(os.environ["DATABASE_PATH"])
recipients = db.table("recipients")

USERNAME = os.environ["ELEMENT_USERNAME"]
PASSWORD = os.environ["ELEMENT_PASSWORD"]
SERVER = os.environ["ELEMENT_SERVER"] # eg, "https://matrix.org"

sg = sendgrid.SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))

FROM_EMAIL = "your-email-account@domain.com"
TO_EMAILS = [r['email'] for r in recipients]

attachments = []
n_attachments = 0
subject  = ''
body = ''

class MFileHandler(MHandler):

    def __init__(self):
        MHandler.__init__(self, self.test_file, self.handle_file)

    def test_file(self, room, event):
        try:
            msgtype = event['content']['msgtype']
            return msgtype == 'm.image' or msgtype == 'm.file'
        except:
            return False

    def handle_file(self, room, event):
        file_type = event['content']['info']['mimetype']
        human_friendly = event['content']['body']
        mxc_url = event['content']['url']
        response = requests.get("https://matrix.org/_matrix/media/r0/download/" + mxc_url[6:])
        try:
            response.raise_for_status()
            binary = response.content
            attachments.append((human_friendly, mxc_url, file_type, binary))
            room.send_text(f"Received a file: {human_friendly} (MXC address: {mxc_url})")
        except:
            room.send_text(f"Error receiving file")
        return False

def hi_callback(room, event):
    print(event)
    args = event['content']['body'].split()
    room.send_text("Hi, " + event['sender'])

def set_n_attach_callback(room, event):
    args = event['content']['body'].split('!set_n_attach')[1]
    print(int(args))
    room.send_text(f"Set number of attachments to {args}.")
    global n_attachments 
    n_attachments = int(args)

def set_subject_callback(room, event):
    args = event['content']['body'].split('!set_subject')[1]
    room.send_text(f"Set subject line to {args}.")
    global subject 
    subject = args

def set_body_callback(room, event):
    args = event['content']['body'].split('!set_body')[1]
    room.send_text(f"Set body to {args}.")
    global body 
    body = args

def preview_callback(room, event):
    global subject
    global body
    global n_attachments
    global attachments
    room.send_text(f"Subject line: {subject}.")
    room.send_text(f"Body: {body}.")
    room.send_text(f"Number of attachments: {n_attachments}.")
    try:
        for fn in attachments[::-1][len(attachments)-n_attachments:]:
            room.send_text(f"Attachment: {fn[0]} (MXC address: {fn[1]})")
    except:
        room.send_text(f"Not enough attachments uploaded.")

def help_callback(room, event):
    room.send_text("The following commands are available: !set_n_attach, !set_body, !set_subject, !preview, !send. Uploading attachments will save them and only the last n attachments will be included with the email.")


def send_callback(room, event):
    room.send_text("Sending email...")
    try:
        global attachments
        global subject
        global body
        global n_attachments
        message = Mail(from_email=FROM_EMAIL, to_emails=TO_EMAILS,
                subject=subject, html_content=body)
        print("started message")
        for human_friendly, _, file_type, binary in attachments[::-1][len(attachments)-n_attachments:]:
            encoded_file = base64.b64encode(binary).decode()
            print("decoded!")
            attached_file = Attachment(
                    FileContent(encoded_file),
                    FileName(human_friendly),
                    FileType(file_type),
                    Disposition('attachment'))
            print("added attachment", human_friendly, file_type)
            message.attachment = attached_file
        #print(message.get())
        response = sg.send(message)
        room.send_text(f"Sent successfully with status {response.status_code}!")
    except:
        print(sys.exc_info())
        room.send_text("An error occurred.")
        
    n_attachments = 0
    attachments = []
    body = ''
    subject = ''

def main():
    bot = MatrixBotAPI(USERNAME, PASSWORD, SERVER)

    hi_handler = MRegexHandler("Hi", hi_callback)
    file_handler = MFileHandler()
    set_n_attachments_handler = MCommandHandler("set_n_attach", set_n_attach_callback)
    preview_handler = MCommandHandler("preview", preview_callback)
    send_handler = MCommandHandler("send", send_callback)
    set_body_handler = MCommandHandler("set_body", set_body_callback)
    set_subject_handler = MCommandHandler("set_subject", set_subject_callback)
    help_handler = MCommandHandler("help", help_callback)
    bot.add_handler(hi_handler)
    bot.add_handler(file_handler)
    bot.add_handler(preview_handler)
    bot.add_handler(send_handler)
    bot.add_handler(set_body_handler)
    bot.add_handler(set_subject_handler)
    bot.add_handler(help_handler)
    bot.add_handler(set_n_attachments_handler)
    bot.start_polling()

    while True:
        time.sleep(0.01) # input()

if __name__ == '__main__':
    main()

