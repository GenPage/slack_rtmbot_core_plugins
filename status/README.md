  * [status plugin](#statusplugin)
      * [Version](#version)
      * [Requirements](#requirements)
    * [Exposed Chat Commands](#exposed-chat-commands)
    * [Exposed Functions for other plugins:](#exposed-functions-for-other-plugins)


# status plugin

status is a plugin for ig_skynet that provides commands to check the status of the bot and manage it

## ping.py

ping.py is a status check for the bot. It will respond to a "PING" request with "PONG" to make sure the bot is running

## controls.py

controls.py allows the bot to be stopped or restarted from a chat command by an admin user

### Version
1.0

### Requirements

####Auth.py
status.py relies on auth.py for some commands. The stop and restart commands require a user to be an admin

## Exposed Chat Commands
All commands only work in DM

- `botname ping` - Will return "PONG" if the bot is running
- `botname restart` - If requesting user is an admin, this will restart the bot process
- `botname stop` - If requesting user is an admin, this will stop the bot process

