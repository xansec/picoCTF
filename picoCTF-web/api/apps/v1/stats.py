"""Endpoints for getting statistical reports."""
from flask import jsonify
from flask_restplus import Namespace, Resource

import api
from api import block_before_competition, PicoException, require_admin

from .schemas import scoreboard_page_req, top_teams_score_progression_req

ns = Namespace('stats', 'Statistical aggregations and reports')


@ns.route('/registration')
class RegistrationStatus(Resource):
    """Get information on user, team, and group registrations."""

    def get(self):
        """Get information on user, team, and group registrations."""
        return jsonify(api.stats.get_registration_count())


@ns.route('/scoreboard')
class Scoreboard(Resource):
    """Retrieve the inital scoreboard."""

    @block_before_competition
    @ns.response(200, 'Success')
    @ns.response(422, 'Competition has not started')
    def get(self):
        """Retrieve the initial scoreboard."""
        return jsonify(api.stats.get_initial_scoreboard())


@ns.route('/scoreboard/page')
class ScoreboardPage(Resource):
    """Retrieve a page of a specific scoreboard."""

    @block_before_competition
    @ns.response(200, 'Success')
    @ns.response(401, 'Must be logged in to retrieve groups board')
    @ns.response(422, 'Competition has not started')
    @ns.expect(scoreboard_page_req)
    def get(self):
        """Retrieve a page of a specific scoreboard."""
        req = scoreboard_page_req.parse_args(strict=True)
        if req['board'] == 'groups' and not api.user.is_logged_in():
            raise PicoException(
                'You must be logged in to retrieve pages from the ' +
                'groups scoreboard.', 401
            )
        return jsonify(api.stats.get_scoreboard_page(
            req['board'], req['page']
        ))


@ns.route('/top_teams/score_progression')
class TopTeamsScoreProgressions(Resource):
    """Get score progressions for the top n teams, optionally filtered."""

    @ns.response(200, 'Success')
    @ns.expect(top_teams_score_progression_req)
    def get(self):
        """Get score progressions for the top n teams, optionally filtered."""
        req = top_teams_score_progression_req.parse_args(strict=True)
        return jsonify(api.stats.get_top_teams_score_progressions(
            include_ineligible=req['include_ineligible'], gid=req['gid']
        ))


@ns.response(200, 'Success')
@ns.response(401, 'Not logged in')
@ns.response(403, 'Not authorized')
@ns.route('/submissions')
class SubmissionStatistics(Resource):
    """View submission statistics, broken down by problem."""

    @require_admin
    def get(self):
        """Get submission statistics, broken down by problem name."""
        return jsonify({
            p['name']: api.stats.get_problem_submission_stats(p['pid'])
            for p in api.problem.get_all_problems(show_disabled=True)
        })

@ns.route('/demographics')
class DemographicInformation(Resource):
    """Get demographic information used in analytics."""

    @require_admin
    def get(self):
        """Get demographic information used in analytics."""
        return jsonify(api.stats.get_demographic_data())
