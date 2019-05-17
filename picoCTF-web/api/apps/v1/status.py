"""Endpoint for platform status."""
from flask import jsonify
from flask_restplus import Namespace, Resource

import api

ns = Namespace('status', description='Information about the platform status')


@ns.route('')
class Status(Resource):
    """Get information about the platform status."""

    def get(self):
        """
        Get information about the platform status.

        The main purpose is to have an endpoint to check if the platform is up,
        but also reports some settings for convenience.

        Previous versions of this endpoint included user/team status if
        a user was logged in - that information should now be retreived
        from their respective endpoints.
        """
        settings = api.config.get_settings()
        return jsonify({
            "server_"
            "enable_feedback":
                settings["enable_feedback"],
            "enable_captcha":
                settings["captcha"]["enable_captcha"],
            "reCAPTCHA_public_key":
                settings["captcha"]["reCAPTCHA_public_key"],
            "competition_active":
                api.config.check_competition_active(),
            "email_verification":
                settings["email"]["email_verification"],
            "max_team_size":
                settings["max_team_size"],
            "email_filter":
                settings["email_filter"]
        })
