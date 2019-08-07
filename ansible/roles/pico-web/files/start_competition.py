#!/usr/bin/env python3

# Simple script to programmatically start a competition useful for development
# and testing purposes. Defaults to 1 year.

# If using a custom APP_SETTINGS_FILE, ensure the appropriate
# environment variable is set prior to running this script. This script is best
# run from the pico-web role (ansible/roles/pico-web/tasks/main.yml)

from datetime import datetime, timedelta

import api


def main():
    with api.create_app().app_context():
        api.events.add_event("Global", eligibility_conditions={})

        settings = api.config.get_settings()
        settings["start_time"] = datetime.now()
        settings["end_time"] = settings["start_time"] + timedelta(weeks=52)
        api.config.change_settings(settings)


if __name__ == "__main__":
    main()
