"""Setting related endpoints."""

from flask import jsonify
from flask_restplus import Namespace, Resource

import api

from .schemas import settings_patch_req

ns = Namespace('settings', description='View or modify runtime settings')


@ns.route('/')
class Settings(Resource):
    """Get or modify the current settings."""

    # @require_admin
    # @TODO anyone should be able to see max_team_size, email_filter
    #       to replace the dedicated /team/settings call
    @ns.response(200, 'Success')
    def get(self):
        """Get the current settings."""
        return jsonify(api.config.get_settings())

    @ns.response(200, 'Success')
    @ns.response(400, 'Error parsing request')
    @ns.expect(settings_patch_req)
    def patch(self):
        """Update settings."""
        req = {
            k: v for k, v in settings_patch_req.parse_args().items() if
            v is not None
        }
        api.config.change_settings(req)
        return jsonify({
            'success': True
        })
