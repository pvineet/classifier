#!/usr/bin/python

import httplib2
import base64
import email

from classify import *
from  utils import *
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
query = 'in:inbox after:2014/12/01 from:@wns.com -from:noreply@wwstay.com'
user_id = 'me'
new_req_label = {'addLabelIds': ['INBOX','Label_5',]}
# Retrieve a page of threads
response = gmail_service.users().messages().list(userId=user_id, q=query).execute()

if 'messages' in response:
    messages.extend(response['messages'])

while 'nextPageToken' in response:
    page_token = response['nextPageToken']
    response = gmail_service.users().messages().list(userId=user_id, q=query, pageToken=page_token).execute()
    messages.extend(response['messages'])

message_list = messages

print len(messages)

i=1
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
                print type(content)
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
                
                        text = ''
                        for l in clean_mail:
                            text = text+' ' +l
    
                        text = text.lower().split('thank')[0]
                        text = text.lower().split('regard')[0]
                    else:
                        continue
                if classify(text) == 'new':
                    print text
                    try:
                        label_response = gmail_service.users().messages().modify(userId='me', id=msg_id, body=new_req_label).execute()
                    except errors.HttpError, error:
                        print 'An error occurred: %s' % error
    else:
        pass
        #print i
        #print message['snippet']
        #print m.get_content_type()
    i=i+1         

