"""Endpoints related to the current user's team."""
from flask import jsonify
from flask_restplus import Namespace, Resource

import api.team
import api.user

from .schemas import update_team_password_req, score_progression_req

ns = Namespace('team', description="Information about the current user's team")


@ns.route('/')
class Team(Resource):
    """Get the current user's team."""

    # @require_login
    def get(self):
        """Get information about the current user's team."""
        current_tid = api.user.get_user()['tid']
        return jsonify(api.team.get_team_information(current_tid))


# @TODO doesn't make sense to return score in both /team an /team/score
@ns.route('/score')
class Score(Resource):
    """Get the current user's team's score."""

    # @require_login
    def get(self):
        """Get your team's score."""
        current_tid = api.user.get_user()['tid']
        return jsonify({
            'score': api.stats.get_score(current_tid)
        })


@ns.route('/update_password')
class UpdatePasswordResponse(Resource):
    """Update your team's password."""

    # @require_login
    # @check_csrf
    @ns.response(200, 'Success')
    @ns.response(400, 'Error parsing request')
    @ns.response(401, 'Not logged in')
    @ns.response(422, 'Provided password does not match')
    @ns.expect(update_team_password_req)
    def post(self):
        """Update your team password."""
        req = update_team_password_req.parse_args(strict=True)
        # @TODO refactor update_password_request()
        api.team.update_password_request(
            {
                'new-password': req['new_password'],
                'new-password-confirmation':
                    req['new_password_confirmation']
            })
        return jsonify({
            'success': True
        })


@ns.route('/score_progression')
class ScoreProgression(Resource):
    """Get your team's score progression."""

    # @require_login
    # @block_before_competition
    @ns.response(200, 'Success')
    @ns.response(400, 'Error parsing request')
    @ns.response(401, 'Not signed in')
    @ns.expect(score_progression_req)
    def get(self):
        """Get your team's score progression."""
        req = score_progression_req.parse_args(strict=True)
        # Handle the 'category' arg if present but unset
        if req['category'] == '':
            req['category'] = None
        current_tid = api.user.get_user()['tid']
        return jsonify(
            api.stats.get_score_progression(
                tid=current_tid, category=req['category'])
        )
