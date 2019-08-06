"""Team related endpoints."""
import string

from flask import jsonify
from flask_restplus import Namespace, Resource

import api
from api import PicoException, require_admin, require_login

from .schemas import team_req, team_patch_req

ns = Namespace('teams', description='Team management')


@ns.route('')
class TeamList(Resource):
    """The set of all teams."""

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
        if not all([
                c in string.digits + string.ascii_lowercase + " ()+-,#'&!?"
                for c in req['team_name'].lower()]):
            raise PicoException(
                "Team names cannot contain special characters other than "+
                "()+-,#'&!?", status_code=400
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


@ns.route('/<string:team_id>')
class Team(Resource):
    """A specific team."""

    @require_admin
    @ns.response(200, 'Success')
    @ns.response(400, 'Error parsing request')
    @ns.response(401, 'Not logged in')
    @ns.response(403, 'Not authorized')
    @ns.response(404, 'Team not found')
    @ns.expect(team_patch_req)
    def patch(self, team_id):
        """Update team settings."""
        req = team_patch_req.parse_args(strict=True)
        res = api.team.get_team(tid=team_id)
        if not res:
            raise PicoException('Team not found', status_code=404)
        api.team.update_team(team_id, req)
        return jsonify({
            'success': True
        })


@ns.response(200, 'Success')
@ns.response(401, 'Not logged in')
@ns.response(403, 'Permission denied')
@ns.response(404, 'Team not found')
@ns.route('/<string:team_id>/recalculate_eligibilities')
class RecalculateEligibilitiesResponse(Resource):
    """Force recalculation of a team's eligibilities."""

    @require_admin
    def get(self, team_id):
        """
        Force recalculation of a team's eligibilities.

        Re-evaluate a team's eligibilities. May be useful if a former team
        member that caused a team to become ineligible for an event has
        deleted their account, or if a new event has been added since the
        team was formed.
        """
        team = api.team.get_team(team_id)
        if not team:
            raise PicoException('Team not found', 404)

        team_members = api.team.get_team_members(
            tid=team_id, show_disabled=False)
        all_events = api.events.get_all_events()
        member_eligibilities = dict()
        for member in team_members:
            member_eligibilities[member['uid']] = {
                event['eid'] for event in all_events
                if api.events.is_eligible(member, event)
            }

        team_eligibilities = list(
            set.intersection(*member_eligibilities.values()))
        db = api.db.get_conn()
        db.teams.find_one_and_update(
            {"tid": team_id},
            {"$set": {
                "eligibilities": team_eligibilities
            }}
        )

        return jsonify({
            'success': True,
            'eligibilities': team_eligibilities
        })
