# Created 03/05/2020
# Author: Mike McGrail
# Usage: Send JSON payload to Splunk HEC
# Called from alert.py
# Update Log:
# 04/16/2020 Mike M. modified logging; updated try/except

import sys
import logging
import json
import requests
import pprint


def set_url():                                             #Set HEC destination URL
    return 'https://<endpoint as provided by Splunk Admins>:8088/services/collector'
    

def set_token():                                           #Set HEC auth token
    return '<set the token here as provided by Splunk Admins'


def send_event(dest_url, auth_token, payload):              #Function to send event to Splunk HTTP Event Collector (HEC)
    myheaders = {'Content-Type': 'application/json' , 'Authorization': auth_token }

    try:
        logging.info('operation=send_post url=%s, payload=%s', dest_url, payload)
        r = requests.post(url=dest_url, data=json.dumps(payload), headers=myheaders, verify=False)
        logging.info("Response: Status code: %d", r.status_code)
    except Exception as e:
        logging.warning('Unable to send to HEC: ' + str(e))


def main(payload):
    dest_url = set_url()
    auth_token = set_token()
    
    send_event(dest_url, auth_token, payload)


if __name__ == '__main__':
    main()