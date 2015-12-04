#! env/bin/python

import re
import yaml

outputs = []
config = yaml.load(file('conf/rtmbot.conf', 'r'))
# this is what the bot responds to PING with.
OUTPUT_MESSAGE = "PONG"


def process_directmessage(data):
    """
    Outputs PONG if the bot is alive
    :param data:
    :return:
    """
    match = re.match(r"ping", data['text'], flags=re.IGNORECASE)
    if match:
        outputs.append([data['channel'], "{}".format(OUTPUT_MESSAGE)])
    return

def process_message(data):
    """
    Outputs PONG if the bot is alive
    :param data:
    :return:
    """
    match = re.match(r"{} ping".format(config['BOTNAME']), data['text'], flags=re.IGNORECASE)

    if match:
        outputs.append([data['channel'], "{}".format(OUTPUT_MESSAGE)])
    return
