  * [auth.py](#authpy)
      * [Version](#version)
      * [Requirements](#requirements)
        * [Sqlite](#sqlite)
    * [Exposed Chat Commands](#exposed-chat-commands)
    * [Exposed Functions for other plugins:](#exposed-functions-for-other-plugins)


# auth.py

auth.py is a plugin for ig_skynet that provides other plugins the ability to use permissions to prevent/allow users from accessing certain commands

### Version
1.0

### Requirements

####Sqlite
Auth.py uses a sqlite database to store its data. See [docs/sqllite.schema](sqllite.schema "Schema File") for the schema.

## Exposed Chat Commands
All commands only work in DM

- `roles list [username]` - lists the roles a user has
- `roles list-roles` - lists all the roles 
- `roles list-users` _ Lists all the users that the auth db knows about
- `roles new [role-name]` - adds a new role
- `roles add [role-name]` [username] -  add [username] to role
- `roles remove [role-name] [username]` -  removes [username] from role

##Exposed Functions for other plugins:

- `user_has_role(username,rolename)` - pass a username and role name to this function and it will return true if that user has the role. It will return false if the user does not have that role or if the user does not exist.
- `create_new_role(new_role_name)` - will create a new role with your passed role name, if that role_name is unique. Returns false if unable to create new role, true if role creates.
