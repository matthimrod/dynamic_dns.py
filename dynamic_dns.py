#!/usr/bin/python3

import logging
import os
import re
import requests
import smtplib
import socket
import ssl
import yaml

my_hostname = socket.gethostname()
CONFIG_FILENAME = os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])),
                               f"dynamic_dns.{my_hostname}.yml")

config = []
with open(CONFIG_FILENAME, 'r') as config_file:
    try:
        config = yaml.safe_load(config_file)
    except yaml.YAMLError as exc:
        print(exc)

logging.basicConfig(filename=config.get('config', {}).get('log_filename'),
                    encoding='utf-8',
                    level=logging.INFO,
                    format='%(asctime)s %(message)s')
logger = logging.getLogger()


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


def get_ip6():
    s = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
    try:
        s.connect(('2001:4860:4860::8888', 53))
        IP = s.getsockname()[0]
    except Exception:
        IP = '::1'
    finally:
        s.close()
    return IP


def get_public_ip(api_url):
    result = requests.get(api_url)
    if result.status_code != requests.codes.ok:
        message = f'IP API call failed. {result.text}'
        logging.error(message)
        email(message)
        return None
    else:
        return result.text


def email(message):
    email_text = f"""\
From: {config['config']['email_from']}
To: {config['config']['email_to']}
Subject: Dynamic DNS error: {my_hostname}

{message}
"""

    try:
        # Create a secure SSL context
        context = ssl.create_default_context()

        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as server:
            server.login(config['config']['username'],
                         config['config']['password'])
            server.sendmail(config['config']['email_from'],
                            config['config']['email_to'], email_text)
            server.close()

        logger.warning('Email sent to %s.', config['config']['email_to'])
    except:
        logger.error('Something went wrong while sending the failure email.')


for site in config['sites']:
    if not (('last_result' in config['sites'][site]) and (config['sites'][site]['last_result'] != 'error')):
        payload = {}
        payload['hostname'] = site
        if 'use_local_ip' in config['sites'][site]:
            payload['myip'] = get_ip()
        if 'use_local_ip6' in config['sites'][site]:
            payload['myip'] = get_ip6()
        if 'ip_api_url' in config['sites'][site]:
            payload['myip'] = get_public_ip(
                config['sites'][site]['ip_api_url'])

        result = requests.get(config['config']['api_url'], auth=(
            config['sites'][site]['username'], config['sites'][site]['password']), params=payload)
        logger.info('%s: %s', site, result.text)

        if (result.status_code != requests.codes.ok) or not (re.match('(good|nochg)', result.text)):
            logger.error(f'DNS API call failed for {site}. {result.text}')
            email(f'DNS API call failed for {site}. {result.text}')
            config['sites'][site]['last_result'] = 'error'

with open(CONFIG_FILENAME, 'w') as config_file:
    yaml.dump(config, config_file, default_flow_style=False)
