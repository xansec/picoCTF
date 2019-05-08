"""Group manangement."""
from flask import jsonify
from flask_restplus import Namespace, Resource

ns = Namespace('groups', description='Group management')

@ns.route('/')
class GroupList(Resource):
    """Get the list of groups, or add a new group."""

    def get(self):
        """Get the full list of groups."""
        return False
