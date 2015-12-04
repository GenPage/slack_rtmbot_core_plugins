#! env/bin/python
from datetime import timedelta

import psutil
import re
import yaml

outputs = []

# load default configs
config = yaml.load(file('conf/rtmbot.conf', 'r'))


def status_main():
    """
    Does the work of checking the server's status
    Returns the message to output
    :return: message
    """

    message = "Unable to check server status"

    cpu_usage = psutil.cpu_percent()
    disk_io = psutil.disk_io_counters(perdisk=False)
    with open('/proc/uptime', 'r') as f:
        uptime_seconds = float(f.readline().split()[0])
        uptime_string = str(timedelta(seconds=uptime_seconds))

    if cpu_usage and disk_io and uptime_string:
        message = "Load: {}\nDisk IO: {}\nUptime: {}".format(cpu_usage, disk_io, uptime_string)

    return message


def process_directmessage(data):
    match = re.match(r"status", data['text'], flags=re.IGNORECASE)
    if match:
        message = status_main()
        outputs.append([data['channel'], "{}".format(message)])
    return


def process_message(data):
    match = re.match(r"{} status".format(config['USERNAME']), data['text'], flags=re.IGNORECASE)
    if match:
        message = status_main()
        outputs.append([data['channel'], "{}".format(message)])
    return
