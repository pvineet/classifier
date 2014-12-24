#!/usr/bin/python

import httplib2
import base64
import email

from classify import *
from utils import *
from xml.sax.saxutils import unescape
from apiclient import errors
from apiclient.discovery import build
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import run

#emails from these sources to be ignored
IGNORE_EMAILS = []

# Path to the client_secret.json file downloaded from the Developer Console
CLIENT_SECRET_FILE = 'client_secret.json'

# Check https://developers.google.com/gmail/api/auth/scopes for all available scopes
OAUTH_SCOPE = 'https://www.googleapis.com/auth/gmail.modify'

# Location of the credentials storage file
STORAGE = Storage('gmail.storage')

# Start the OAuth flow to retrieve credentials
flow = flow_from_clientsecrets(CLIENT_SECRET_FILE, scope=OAUTH_SCOPE)
http = httplib2.Http()

# Try to retrieve credentials from storage or run the flow to generate them
credentials = STORAGE.get()
if credentials is None or credentials.invalid:
  credentials = run(flow, STORAGE, http=http)

# Authorize the httplib2.Http object with our credentials
http = credentials.authorize(http)

# Build the Gmail service from discovery
gmail_service = build('gmail', 'v1', http=http)

messages = []
query = 'in:inbox after:2014/12/01  -from:*@wwstay.com'
user_id = 'me'
new_req_label = {'addLabelIds': ['INBOX','Label_5',]}

def read_mails():
    # Retrieve a page of threads
    response = gmail_service.users().messages().list(userId=user_id, q=query).execute()
    
    if 'messages' in response:
        messages.extend(response['messages'])
    
    while 'nextPageToken' in response:
        page_token = response['nextPageToken']
        response = gmail_service.users().messages().list(userId=user_id, q=query, pageToken=page_token).execute()
        messages.extend(response['messages'])
    print len(messages)
    return messages

def clean_mail(content):
    clean_mail = []
    for line in content.lower().splitlines():
        if not (line.rstrip() == '' or line.rstrip() == '=20'or line.rstrip() == None):
            if not line.strip()[0] == '>':
                if line.split(':')[0].lower() == 'from': 
                    found_from = True
                elif  line.split(':')[0].lower() == 'sent':
                    found_from = False
                    break
                else:
                    clean_mail.append(line.rstrip())
            else:   
                break
        else:
            continue
    return clean_mail

def split_mail(clean_mail):
    text = ''
    for l in clean_mail:
        text = text+' ' +l
    text = text.lower().split('thank')[0]
    text = text.lower().split('regard')[0]
    return text

def label_mail(text,msg_id):
    """Classification code"""       
    if classify(text) == 'new':
        #check if the mail is from WWStay
        try:
            label_response = gmail_service.users().messages().modify(userId=user_id, id=msg_id, body=new_req_label).execute()
            return 'new'
        except errors.HttpError, error:
            return 'An error occurred: %s' % error
    else:
        return 'others'


def parse_mails(message_list):
    for msg in message_list:
        msg_id = msg['id']
        response = gmail_service.users().messages().get(userId='me', id=msg_id, format='raw').execute()
        msg_str = base64.urlsafe_b64decode(response['raw'].encode('utf-8'))
        mime_msg = email.message_from_string(msg_str)
        if mime_msg.is_multipart():
            for m in mime_msg.walk():
                if m.get_content_type() == "text/plain":
                    if m['Content-Transfer-Encoding'] == "base64":
                        content = base64.urlsafe_b64decode(m.get_payload())
                    else:
                        content = m.get_payload()
                    text = split_mail(clean_mail(content))
                    
                    if label_mail(text,msg_id) == 'new': 
                        thread_id = msg['threadId']
                        #get the thread
                        thread_response = gmail_service.users().threads().get(userId=user_id, id=thread_id).execute()
                        thread_messages = thread_response['messages']
                        if thread_messages.pop()['id'] == msg['id']:
                            print "Need follow up %s" % (msg['id'])
        else:
            print mime_msg.get_content_type()
            content = mime_msg.get_payload()
            text = split_mail(clean_mail(content))

def main():
    parse_mails(read_mails())

if __name__=='__main__':
    main()
