"""Team related endpoints."""
from flask import jsonify
from flask_restplus import Namespace, Resource

import api
from api import PicoException, require_login

from .schemas import team_req

ns = Namespace('teams', description='Team management')

# @TODO create listing / by tid GET endpoints like /problems
#       (did not exist in previous API)


@ns.route('')
class TeamList(Resource):
    """Add a new team."""

    @require_login
    @ns.response(201, 'Success')
    @ns.response(400, 'Error parsing request')
    @ns.response(401, 'Not logged in')
    @ns.response(403, 'Unauthorized to create team')
    @ns.response(409, 'User or team with this name already exists')
    @ns.response(422, 'User has already created a team')
    @ns.expect(team_req)
    def post(self):
        """Create and automatically join new team."""
        req = team_req.parse_args(strict=True)
        curr_user = api.user.get_user()
        if curr_user['teacher']:
            raise PicoException(
                'Teachers may not create teams', 403
            )
        new_tid = api.team.create_and_join_new_team(
            req['team_name'],
            req['team_password'],
            curr_user
        )
        res = jsonify({
            'success': True,
            'tid': new_tid
        })
        res.status_code = 201
        return res
