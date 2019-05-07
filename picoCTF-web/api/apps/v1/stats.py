"""Endpoints for getting statistical reports."""
from flask import jsonify
from flask_restplus import Namespace, Resource

import api.stats

ns = Namespace('stats', 'Statistical aggregations and reports')


@ns.route('/registration')
class RegistrationStatus(Resource):
    """Get information on user, team, and group registrations."""

    def get(self):
        """Get information on user, team, and group registrations."""
        return jsonify(api.stats.get_registration_count())
