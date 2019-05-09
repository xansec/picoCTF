"""Submission related endpoints."""
from flask import jsonify, request
from flask_restplus import Namespace, Resource

import api.problem
import api.stats
import api.user

from .schemas import submission_req

ns = Namespace('submissions', description='Submit flags and list ' +
               'submission attempts')


@ns.route('/')
class SubmissionList(Resource):
    """Submit new solution attempts, or clear all existing submissions."""

    # @require_login
    # @check_csrf
    # @block_before_competition
    # @block_after_competition
    @ns.response(200, 'Submission successful')
    @ns.response(400, 'Error parsing request')
    @ns.response(401, 'Not logged in')
    @ns.expect(submission_req)
    def post(self):
        """Submit a solution to a problem."""
        user_account = api.user.get_user()
        tid = user_account['tid']
        uid = user_account['uid']
        req = submission_req.parse_args(strict=True)
        pid = req['pid']
        key = req['key']
        method = req['method']
        ip = request.remote_addr

        (correct,
         previously_solved_by_user,
         previously_solved_by_team) = api.submissions.submit_key(
                tid, pid, key, method, uid, ip)

        if correct and not previously_solved_by_team:
            message = 'That is correct!'
        elif not correct and not previously_solved_by_team:
            message = 'That is incorrect!'
        elif correct and previously_solved_by_user:
            message = 'Flag correct: however, you have already solved ' + \
                      'this problem.'
        elif correct and previously_solved_by_team:
            message = 'Flag correct: however, your team has already ' + \
                      'received points for this flag.'
        elif not correct and previously_solved_by_user:
            message = 'Flag incorrect: please note that you have ' + \
                      'already solved this problem.'
        elif not correct and previously_solved_by_team:
            message = 'Flag incorrect: please note that someone on your ' + \
                      'team has already solved this problem.'

        return jsonify({
            'correct': correct,
            'message': message
        })

    # @require_admin
    @ns.response(200, 'Success')
    @ns.response(401, 'Not logged in')
    @ns.response(403, '')
    @ns.response(500, 'Debug mode not enabled')
    def delete(self):
        """Clear all submissions (debug mode only)."""
        api.submissions.clear_all_submissions()
        return jsonify({
            'success': True
        })


@ns.route('/statistics')
class SubmissionStatistics(Resource):
    """View submission statistics, broken down by problem."""

    # @require_admin
    def get(self):
        """Get submission statistics, broken down by problem name."""
        return jsonify({
            p['name']: api.stats.get_problem_submission_stats(p['pid'])
            for p in api.problem.get_all_problems(show_disabled=True)
        })
