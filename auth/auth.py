#! env/bin/python

import json
import sqlite3 as lite

import re
import yaml
from slackclient import SlackClient

outputs = []

# load our config file
auth_config = yaml.load(file('conf/auth.conf', 'r'))
# load main config file
config = yaml.load(file('conf/rtmbot.conf', 'r'))



def update_user_list():
    """
    Grabs a user list from slack and updates the sqlite DB
    :return: boolean. True if users table matches slack as of now. False if we were not able to update
    """
    users_to_date = False

    # doing a direct connection to the slack API here to retrieve the users
    # list
    try:
        sc = SlackClient(auth_config["SLACK_TOKEN"])
        data = json.loads(sc.api_call("users.list"))
    # generic except, I do not know what exceptions the api could throw
    except:
        # make data an empty list
        data = []
    try:
        con = lite.connect(auth_config['AUTH_DB'])
        cur = con.cursor()

        # these queries do an "upsert" on the users table - either updating an existing record or inserting a new one
        update_query = "UPDATE or IGNORE users set username=? where id=?"
        insert_query = "INSERT OR IGNORE into users ('id','username','roles') values (?,?,'[]')"

        # updates the admin table usernames if there is a change
        admin_name_update = "UPDATE or IGNORE admins set username=? where id=?"

        # if we excepted above, no need to do anything here
        if len(data) > 0:
            # this block should loop through the users data from slack and perform an upsert
            # any new record is inserted, any old one is updated based on the user_id
            # the admin table's name column is also updated if there is a
            # change
            for user in data["members"]:
                cur.execute(update_query, (user['name'], user['id']))
                cur.execute(insert_query, (user['id'], user['name']))
                cur.execute(admin_name_update, (user['name'], user['id']))
            con.commit()
            users_to_date = True
    except lite.Error as e:
        print "Error %s:" % e.args[0]
        return
    finally:
        if con:
            con.close()

    # true if users table matches slack as of now, false if we failed to make
    # any updates
    return users_to_date

def check_admin_user(user_id):
    """
    This function checks if a given slack userid is listed in the admins table of auth.db
    :param user_id: a user id
    :return: boolean True if user is an admin, false if user is not an admin
    """
    is_admin = False
    query = "select * from admins where id=?"
    try:
        con = lite.connect(auth_config['AUTH_DB'])
        cur = con.cursor()
        cur.execute(query, (user_id,))
        if len(cur.fetchall()) > 0:
            is_admin = True
    except lite.Error as e:
        print "Error %s:" % e.args[0]
        return
    finally:
        if con:
            con.close()
    # true if the user_id is in the admins table, false if not
    return is_admin


def update_user_role(role, username, action):
    """
    Updates a user's role column. It can add or remove roles
    :param role: role id to add/remove from a user
    :param username: the username to act on
    :param action: String either add or remove
    :return: True if we were able to update, false if we failed
    """
    find_role_id = "select id from roles where name=?"
    get_user = "select * from users where username=?"
    user_role = None
    to_return = False
    try:
        con = lite.connect(auth_config['AUTH_DB'])
        cur = con.cursor()
        cur.execute(find_role_id, (role.lower(),))
        role = cur.fetchone()
        if role is not None:
            cur.execute(get_user, (username,))
            user = cur.fetchone()

    except lite.Error as e:
        print "Error %s:" % e.args[0]
        return
    finally:
        if con:
            con.close()

    # if we got a role and a user from the db, lets continue
    if role is not None and user is not None:
        if action == "add":
            to_return = add_user_role(user, role)
        if action == "remove":
            to_return = remove_user_role(user, role)

    # true if an update was performed, false if we failed
    return to_return

def add_user_role(user, role):
    """
    Adds a role to a user
    :param user:  user id
    :param role: The role to add to the user
    :return: true if added, false if not
    """
    to_return = False
    user_roles = json.loads(user[2])
    new_role = role[0]
    not_repeat_role = True
    for role in user_roles:
        if role == new_role:
            not_repeat_role = False
    if not_repeat_role:
        user_roles.append(new_role)
        roles_txt = json.dumps(user_roles)
        to_return = write_user_data([user[0], user[1], roles_txt])
    return to_return



def user_has_role(user_id, role_name):
    """
    Designed to be called from other methods to check if a user_id has a specific role
    :param user_id: A user id
    :param role_name: the name of the role to check
    :return: True if the user has the role, false if not
    """
    user = get_user(user_id, None)
    role = get_role(None, role_name)

    user_roles = json.loads(user[2])
    has_role = False
    for role in user_roles:
        if role_name == role[2]:
            has_role = True
    return has_role

def remove_user_role(user, role):
    """
    Removes a role to a user
    :param user: user id
    :param role: role name
    :return: true if removed, false if failed
    """
    to_return = False
    user_roles = json.loads(user[2])
    remove_role = role[0]
    has_role = False
    for role in user_roles:
        if role == remove_role:
            has_role = True
    if has_role:
        user_roles.remove(remove_role)
        roles_txt = json.dumps(user_roles)
        to_return = write_user_data([user[0], user[1], roles_txt])
    return to_return

def write_user_data(user):
    """
    this function takes a user data object and writes it to the db user data object is like ['id','username',roles]
    roles is a json dumped object of a list of ids [1,2,3]

    :param user: user object as described
    :return: true if written, false if fails
    """
    write_user_query = "update users set username=?, roles=? where id=?"
    to_return = True
    try:
        con = lite.connect(auth_config['AUTH_DB'])
        cur = con.cursor()
        cur.execute(write_user_query, (user[1], user[2], user[0]))
    except lite.Error as e:
        print "Error %s:" % e.args[0]
        to_return = False
    finally:
        if con:
            con.commit()
            con.close()
    return to_return


def list_user_roles(username):
    """
    Gets a users roles
    :param username: username to check
    :return: A message object
    """
    try:
        user_roles = json.loads(get_user(None, username)[2])
    except TypeError:
        return "{} is not a valid user".format(username)
    role_names = []
    for role in user_roles:
        role_names.append(get_role(role, None)[1])

    if len(role_names) > 0:
        message = "{} has the below roles:\n{}".format(
            username, "\n".join(role_names))
    else:
        message = "{} has no roles".format(username)

    return message


def get_user(user_id, username):
    """
    Returns a user object for either a userid or username. Pass none for the one you are not querying
    :param user_id: User id or none
    :param username: username or none
    :return:
    """
    if user_id is not None:
        query = "select * from users where id=?"
    elif username is not None:
        query = "select * from users where username=?"
    else:
        query = "select * from users where 0=1"

    try:
        con = lite.connect(auth_config['AUTH_DB'])
        cur = con.cursor()
        cur.execute(query, (user_id or username,))
        user = cur.fetchone()
    except lite.Error as e:
        print "Error %s:" % e.args[0]
        user = [None, None, "[]"]
    finally:
        if con:
            con.close()
    return user



def get_role(role_id, role_name):
    """
    Returns a role object for either a role id or role name. Pass none for the one you are not querying
    :param role_id:
    :param role_name:
    :return:
    """
    if role_id is not None:
        query = "select * from roles where id=?"
    elif role_name is not None:
        query = "select * from roles where name=?"
    else:
        query = "select * from roles where 0=1"

    try:
        con = lite.connect(auth_config['AUTH_DB'])
        cur = con.cursor()
        cur.execute(query, (role_id or role_name,))
        user = cur.fetchone()
    except lite.Error as e:
        print "Error %s:" % e.args[0]
        user = [None, None, "[]"]
    finally:
        if con:
            con.close()
    return user


def get_all_users():
    """
    Returns a list of all users in the database
    :return:
    """
    query = "select * from users"
    try:
        con = lite.connect(auth_config['AUTH_DB'])
        cur = con.cursor()
        cur.execute(query)
        users = cur.fetchall()
    except lite.Error as e:
        print "Error %s:" % e.args[0]
        users = [None, None, None]
    finally:
        if con:
            con.close()
    return users


def get_all_roles():
    """
    Returns a list of all roles in the database
    :return:
    """
    query = "select * from roles"
    try:
        con = lite.connect(auth_config['AUTH_DB'])
        cur = con.cursor()
        cur.execute(query)
        roles = cur.fetchall()
    except lite.Error as e:
        print "Error %s:" % e.args[0]
        roles = [None, None]
    finally:
        if con:
            con.close()
    return roles


def create_new_role(new_role_name):
    """
    Create a new role. Must be unique name
    :param new_role_name: String new role name
    :return: True if created role, false if not
    """
    to_return = True
    query = "insert into roles(id,name) values (NULL,?)"
    try:
        con = lite.connect(auth_config['AUTH_DB'])
        cur = con.cursor()
        cur.execute(query, (new_role_name.lower(),))
    except lite.Error as e:
        print "Create new role: Error %s:" % e.args[0]
        to_return = False
    finally:
        if con:
            con.commit()
            con.close()
    return to_return


def process_directmessage(data):

    match = re.findall(r"roles (.*)", data['text'])

    if not match:
        return

    # Update the user list from slack just to make sure we have the most accurate data
    update_user_list()

    user_id = data['user']

    if check_admin_user(user_id):
        # split the message data on every space
        data_split = match[0].split(" ")
        # action is the first part of the message
        action = data_split[0]

        # we're adding a new role
        if action == "add":
            role = data_split[1]
            username = data_split[2]
            result = update_user_role(role, username, "add")
            if result:
                message = "Added {} role to {}".format(role, username)
            else:
                message = ("Failed to add {} role to {}\n Maybe try listing that person's roles to make sure there"
                           + "isn't a duplicate? \n If you still have issues, contact {} for support.").format(
                    role, username, config['SUPPORT_CONTACT'])

                # we're removing a role
        elif action == "remove":
            role = data_split[1]
            username = data_split[2]
            if update_user_role(role, username, "remove"):
                message = "Removed {} fole from {}".format(role, username)
            else:
                message = ("Failed to remove {} role from {}.\nMaybe try listing that person's role to make sure "
                           + "there isn't a duplicate. If you still have issues contact {} for support.").format(
                    role, username, config['SUPPORT_CONTACT'])

                # we're listing a user's roles
        elif action == "list":
            try:
                username = data_split[1]
                message = list_user_roles(username)
            except IndexError:
                message = ("Please provide a username to get a list of their roles or use list-roles to get a list "
                           + "of all roles.")

                # we're listing all roles
        elif action == "list-roles":
            all_roles = get_all_roles()
            all_role_names = []
            for role in all_roles:
                all_role_names.append(role[1])
            message = "All roles:\n{}".format("\n".join(all_role_names))

        # we're listing all users
        elif action == "list-users":
            all_users = get_all_users()
            all_usernames = []
            for user in all_users:
                all_usernames.append(user[1])
            message = "All users:\n{}".format("\n".join(all_usernames))

        # we're creating a new role
        elif action == "new" or action == "create":
            new_role_name = data_split[1]
            if create_new_role(new_role_name):
                message = "Successfully created new role named {}".format(
                    new_role_name)
            else:
                message = ("Unable to add new role named {}\nMaybe try list-roles to see if it already exists. "
                           "\n If you still have issues contact {} for support.").format(
                    new_role_name, config['SUPPORT_CONTACT'])

        #should be no way to get here but just covering all of the bases
        else:
            message = "Invalid action chosen"

    # this user isnt an admin so tell them to go away with love
    else:
        message = "Only admins can play with roles. Contact an admin"

    # return the message to the bot main process to be returned
    outputs.append([data['channel'], "{}".format(message)])

    # update the user list from slack again
    update_user_list()
    return


def process_help():
    dm_help = []
    channel_help = []

    plugin_help = []
    # setup help
    dm_help.append("roles add [RoleName] [UserName] - Adds [RoleName] role to [UserName]")
    dm_help.append("roles remove [RoleName] [UserName] - Removes [RoleName] role from [UserName]")
    dm_help.append("roles list [Username]-Lists all the roles [Username] has")
    dm_help.append("roles list-roles-Lists all roles")
    dm_help.append("roles list-users-Lists all user names")
    dm_help.append("roles new [RoleName]-Creates a new role with [RoleName]")
    dm_help.append("roles create [RoleName]-Creates a new role with [RoleName]")

    plugin_help.append(dm_help)
    plugin_help.append(channel_help)
    return plugin_help
