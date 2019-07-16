"""
Utilities for dealing with configuration commands
"""

import json
import logging

from shell_manager.util import (FatalException, get_config,
                                place_default_config, write_configuration_file,
                                write_global_configuration,
                                get_hacksports_config)

logger = logging.getLogger(__name__)


def port_range_to_str(port_range):
    if port_range["start"] == port_range["end"]:
        return str(port_range["start"])
    return "%d-%d" % (port_range["start"], port_range["end"])


def banned_ports_to_str(banned_ports):
    return "[" + ", ".join(map(port_range_to_str, banned_ports)) + "]"


def print_configuration(args):
    """
    Entry point for config subcommand
    """

    config = get_hacksports_config()

    if args.json:
        print("Configuration options (in JSON):")
    else:
        print("Configuration options (pretty printed):")

    for option, value in config.items():
        if args.json:
            value_string = json.dumps(value)
        else:
            if option == "banned_ports":
                value_string = banned_ports_to_str(value)
            else:
                value_string = repr(value)

        print("  %s = %s" % (option.ljust(50), value_string))


def set_configuration_option(args):
    """
    Entry point for config set subcommand
    """

    config = get_hacksports_config()

    field = args.field
    value = args.value
    if args.json:
        try:
            value = json.loads(args.value)
        except Exception:
            logger.fatal("Couldn't parse value as JSON")
            raise FatalException

    if field in config and type(
            config[field]) != type(value) and not args.allow_type_change:
        logger.fatal("Tried to change type of '%s' from '%s' to '%s'", field,
                     type(config[field]), type(value))
        logger.fatal("Try adding --json and supplying the value as json.")
        logger.fatal(
            "If changing the type is desired, add the --allow-type-change option"
        )
        raise FatalException

    config[field] = value

    write_global_configuration(config)

    logger.info("Set %s = %s", field, value)

