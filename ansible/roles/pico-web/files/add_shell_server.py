#!/usr/bin/env python3

# Simple script to programmatically add a shell server to a running picoCTF web
# instance.  If using a custom APP_SETTINGS_FILE, ensure the appropriate
# environment variable is set prior to running this script. This script is best
# run from the pico-web role (ansible/roles/pico-web/tasks/main.yml)
#
# Script outputs the `sid` of the shell server to use in a call to load_problems.py

import sys

# The picoCTF API
import api


def main(name, host, user, password, port, proto):
    # If a server by this name exists short circuit no action necessary
    servers = api.shell_servers.get_all_servers()
    for s in servers:
        if s["name"] == name:
            print(s["sid"], end="")
            return
    # server does not exist try to add
    try:
        sid = api.shell_servers.add_server(
            name=name,
            host=host,
            port=port,
            username=user,
            password=password,
            protocol=proto,
            server_number=1,
        )
        print(sid, end="")
    except Exception as e:
        print(e)
        sys.exit("Failed to connect to shell server.")


if __name__ == "__main__":
    if len(sys.argv) != 7:
        print("Incorrect arguments passed, need")
        print("name, host, user, password, port, proto")
        print(sys.argv)
        sys.exit("Bad args")
    else:
        _, name, host, user, password, port, proto = sys.argv
        with api.create_app().app_context():
            main(name, host, user, password, port, proto)
