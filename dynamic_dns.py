#!/usr/bin/python3

import logging
import os
import re
import requests
import smtplib
import socket
import ssl
import yaml

CONFIG_FILENAME = "dynamic_dns.yml"

config = []
with open(CONFIG_FILENAME, 'r') as stream:
    try:
        config = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(exc)

logging.basicConfig(filename=config['config']['log_filename'], encoding='utf-8', level=logging.INFO, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %H:%M:%S')

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def email(message):
    email_text = f"""\
From: {config['config']['email_from']}
To: {config['config']['email_to']}
Subject: Dynamic DNS error.

{message}
"""

    try:
        # Create a secure SSL context
        context = ssl.create_default_context()

        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as server:
            server.login(config['config']['username'], config['config']['password'])
            server.sendmail(config['config']['email_from'], config['config']['email_to'], email_text)
            server.close()

        logging.info('Email sent to %s.', config['config']['email_to'])
    except:
        logging.error('Something went wrong while sending the failure email.')


for site in config['sites']:
    if not (('last_result' in config['sites'][site]) and (config['sites'][site]['last_result'] != 'error')):
        payload = {}
        payload['hostname'] = site
        if 'use_local_ip' in config['sites'][site]:
            payload['myip'] = get_ip()

        result = requests.get(config['config']['api_url'], auth=(config['sites'][site]['username'], config['sites'][site]['password']), params=payload)

        if (result.status_code != requests.codes.ok) or not (re.match('(good|nochg)', result.text)):
            logging.error(f'DNS API call failed for {site}. {result.text}')
            email(f'DNS API call failed for {site}. {result.text}')
            config['sites'][site]['last_result'] = 'error'

with open(CONFIG_FILENAME, 'w') as stream:
    yaml.dump(config, stream, default_flow_style=False)
