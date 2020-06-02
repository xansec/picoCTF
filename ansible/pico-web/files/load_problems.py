#!/usr/bin/env python3

# Simple script to programmatically load problems from a shell server
# If using a custom APP_SETTINGS_FILE, ensure the appropriate
# environment variable is set prior to running this script. This script is best
# run from the pico-web role (ansible/roles/pico-web/tasks/main.yml)

import sys

import api


def main(sid):
    with api.create_app().app_context():
        shell_server = api.shell_servers.get_server(sid)
        try:
            # Load problems and bundles from the shell server
            output = api.shell_servers.get_publish_output(shell_server["sid"])
            output["sid"] = shell_server["sid"]
            api.problem.load_published(output)

            # Set problems to disabled
            for p in api.problem.get_all_problems(show_disabled=True):
                api.problem.set_problem_availability(p["pid"], False)

            # Set bundles to enabled to set correct unlock behavior
            for b in api.bundles.get_all_bundles():
                api.bundles.set_bundle_dependencies_enabled(b["bid"], True)

        except Exception as e:
            print(e.message, e.args)
            sys.exit("Failed to load problems.")


if __name__ == "__main__":

    if len(sys.argv) != 2:
        print("Incorrect arguments passed, need")
        print("sid")
        print(sys.argv)
        sys.exit("Bad args")
    else:
        _, name = sys.argv
        main(name)
