#! env/bin/python

import logging
import sys

import os
import psutil
import re
import yaml

outputs = []

# load default configs
config = yaml.load(file('conf/rtmbot.conf', 'r'))

# load the check_admin_user function from the auth plugin
from auth import check_admin_user


def restart_program():
    """Restarts the current program, with file objects and descriptors
       cleanup
    """
    try:
        p = psutil.Process(os.getpid())
        for handler in p.get_open_files() + p.connections():
            os.close(handler.fd)
    except Exception, e:
        logging.error(e)

    python = sys.executable
    os.execl(python, python, *sys.argv)


def stop_program():
    """Stops the current program.
    """
    os._exit(0)


def restart_bot(user):
    """
    checks if a user is an admin then calls the restart_program method
    :param user: a user id
    :return: string message, only returns if the user is not an admin
    """
    if check_admin_user(user):
        logging.info("{} restarted bot".format(user))
        restart_program()
    else:
        logging.info("{} tried to restart the bot and is not an admin".format(user))
        message = "You are not an admin."

    return message


def stop_bot(user):
    """
    checks if a user is an admin then calls the stop_program method
    :param user: a user id
    :return: string message, only returns if the user is not an admin
    """
    if check_admin_user(user):
        logging.info("{} stopped bot".format(user))
        stop_program()
    else:
        logging.info('{} tried to stop the bot and is not an admin'.format(user))
        message = "You are not an admin."

    return message


def controls_main(data):
    """
    Processes the actual controls command and returns the message to output if any
    :param data:
    :return:
    """
    if re.findall(r"restart", data['text'], flags=re.IGNORECASE):
        message = restart_bot(data['user'])
    if re.findall(r"stop", data['text'], flags=re.IGNORECASE):
        message = stop_bot(data['user'])

    return message


def process_directmessage(data):
    match = re.match(r"(restart|stop)", data['text'], flags=re.IGNORECASE)

    if match:
        message = controls_main(data)
        outputs.append([data['channel'], "{}".format(message)])
    return


def process_message(data):
    match = re.match(r"{} (restart|stop)".format(config['USERNAME']), data['text'], flags=re.IGNORECASE)
    if match:
        message = controls_main(data)
        outputs.append([data['channel'], "{}".format(message)])
    return

def process_help():
    dm_help = []
    channel_help = []
    plugin_help = []

    # setup help
    dm_help.append("restart - Restarts the bot. Admin only command")
    dm_help.append("stop - Stops the bot. Admin only command")

    plugin_help.append(dm_help)
    plugin_help.append(channel_help)
    return plugin_help

