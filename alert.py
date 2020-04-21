# Created 03/05/2020
# Author: Mike McGrail
# Usage: Parse SolarWinds alert to Python dictionary to be used in JSON payload
# Called from alert.bat as a wrapper
# Update Log:
# 04/16/2020 Mike M. Set type=str.lower for status and -t arguments to fix case-sensitivity; modified logging; updated try/except

#Sample SolarWinds call:
#D:\solarwinds_to_splunk\alert.bat "Test Alert" "testserver1" "192.168.1.1" "This is a detailed alert with custom properties" "www.splunk.com" "Alert"
#D:\solarwinds_to_splunk\alert.bat "Test Alert" "testserver1" "192.168.1.1" "This is a detailed alert with custom properties" "www.splunk.com" "Reset"
#D:\solarwinds_to_splunk\alert.bat "${AlertName}" "${NodeName}" "${N=SwisEntity;M=Node.IP_Address}" "${N=Alerting;M=AlertMessage}" "${N=Alerting;M=AlertDetailsUrl}" "Alert" "-t" "No"

import argparse
import os
import sys
import logging
import traceback
import send_to_splunk                                      #Sends data to Splunk HEC


def set_logging():
    logfile = set_logfile()
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', filename=logfile, level=logging.ERROR) #Set DEBUG,INFO,WARNING,ERROR,CRITICAL as needed


def set_logfile():                                         #Function to setup logging
    if not os.path.exists('log'):
        os.makedirs('log')                                 #Create log subdirectory if it does not exist
    logfile=os.path.abspath(os.path.join(os.path.dirname( __file__ ), 'log', 'solarwinds_to_splunk.log'))
    
    if os.path.isfile(logfile):
        if os.path.getsize(logfile) > 10000 * 1024:        #Control log file growth; delete and recreate if too large
            os.remove(logfile)
    return logfile


def main():
    parser = argparse.ArgumentParser()
    #Required arguments
    parser.add_argument('alert', help="${AlertName}")
    parser.add_argument('node', help="${NodeName}")
    parser.add_argument('ip', help="${N=SwisEntity;M=Node.IP_Address}")
    parser.add_argument('msg', help="${N=Alerting;M=AlertMessage}")
    parser.add_argument('url', help="${N=Alerting;M=AlertDetailsUrl}")
    parser.add_argument('status', help="alert or reset", choices=['alert','reset'], type=str.lower)

    # Optional arguments
    parser.add_argument('-t', '--ticket', default='no', choices=['yes','no'], help="yes or no to create incident (default is no)", type=str.lower)
    parser.add_argument('-g', '--group', help="support group")
    parser.add_argument('-k', '--kba', help="KBA number")
    
    try:
        args = parser.parse_args()

    except SystemExit:
        logging.error(sys.argv[1:])
        logging.error('failed to parse arguments')
        sys.exit(0)

    logging.info('operation=initializing arguments=%s', str(args))

    if (args.alert.startswith('(P)1')):                  #Map SolarWinds alerts to ITSM severity levels. This is based on an existing naming standard such as (P)1 - Node Down
        severity = 'CRITICAL'
    elif (args.alert.startswith('(P)2')):
        severity = 'HIGH'
    elif (args.alert.startswith('(P)3')):
        severity = 'MEDIUM'
    elif (args.alert.startswith('(P)4')):
        severity = 'LOW'
    else:
        severity = 'LOW'

    payload = {
        'index': 'solarwinds',
        'sourcetype': 'solarwinds:hec:alert',
        'event': {
            'alert': args.alert,
            'node': args.node,
            'ip': args.ip,
            'msg': args.msg,
            'url': args.url,
            'ticket': 'no',                            #Default to ticket: no, optional parameter may modify this below
            'severity': severity,
            'status': args.status
        }
    }

    if args.ticket:                                    #If present, append optional arguments
        if args.ticket == 'yes':
            payload['event']['ticket'] = 'yes'
    if args.group:
        payload['event']['group'] = args.group
    if args.kba:
        payload['event']['kba'] = args.kba

    logging.info('operation="calling_send_to_splunk" payload=%s', payload)
    try:
        send_to_splunk.main(payload)                       #Pass payload to send_to_splunk 
    except:
        logging.error('failed to send to Splunk')


if __name__ == '__main__':
    set_logging()
    main()