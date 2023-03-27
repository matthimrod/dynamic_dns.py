#!/usr/bin/python3

import logging
import re
import requests
import smtplib
import socket
import ssl
import yaml

CONFIG_FILENAME = "dynamic_dns.yml"

config = []
with open(CONFIG_FILENAME, 'r') as file:
    try:
        config = yaml.safe_load(file)
    except yaml.YAMLError as exc:
        print(exc)

logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter(
        '%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)


def email(message):
    email_text = f"From: {config['config']['email_from']}\n" + \
                 f"To: {config['config']['email_to']}\n" + \
                 "Subject: Dynamic DNS error.\n\n" + \
                 message + "\n"

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL('smtp.gmail.com', 
                              465, 
                              context=context) as smtp_server:
            smtp_server.login(config['config']['username'], 
                              config['config']['password'])
            smtp_server.sendmail(config['config']['email_from'], 
                                 config['config']['email_to'], 
                                 email_text)
            smtp_server.close()
        logger.warn('Email sent to %s.', config['config']['email_to'])
        
    except:
        logger.error('Something went wrong while sending the failure email.')

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

def get_public_ip(api_url):
    result = requests.get(api_url)
    if result.status_code != requests.codes.ok:
        message = f'IP API call failed. {result.text}'
        logging.error(message)
        email(message)
        IP = '127.0.0.1'
    else:
        IP = result.text
    return IP


for site in config['sites']:
    if not (('last_result' in config['sites'][site]) and \
            (config['sites'][site]['last_result'] != 'error')):
        payload = {}
        payload['hostname'] = site
        if 'use_local_ip' in config['sites'][site]:
            payload['myip'] = get_ip()
        if 'ip_api_url' in config['sites'][site]:
            payload['myip'] = get_public_ip(config['sites'][site]['ip_api_url'])

        result = requests.get(config['config']['api_url'], 
                              auth=(config['sites'][site]['username'], 
                                    config['sites'][site]['password']), 
                              params=payload)
        logger.info('%s: %s', site, result.text)

        if (result.status_code != requests.codes.ok) or \
            not (re.match('(good|nochg)', result.text)):
            logger.error(f'DNS API call failed for {site}. {result.text}')
            email(f'DNS API call failed for {site}. {result.text}')
            config['sites'][site]['last_result'] = 'error'

with open(CONFIG_FILENAME, 'w') as file:
    yaml.dump(config, file, default_flow_style=False)
