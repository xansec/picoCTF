"""Problem feedback related endpoints."""
from flask import jsonify
from flask_restplus import Namespace, Resource

import api
from api import PicoException, require_login

from .schemas import feedback_list_req, feedback_submission_req

ns = Namespace('feedback', description='List and submit problem feedback')


@ns.route('/')
class FeedbackList(Resource):
    """Get the list of problem feedback, or submit new feedback."""

    # @TODO only show the current user's feedback, unless an admin, then allow
    #       uid/pid/tid filtering
    # @block_before_competition
    @require_login
    @ns.response(200, 'Success')
    @ns.response(400, 'Error parsing request')
    @ns.response(401, 'Not logged in')
    @ns.expect(feedback_list_req)
    def get(self):
        """Get the list of problem feedback, with optional filtering."""
        if not api.config.get_settings()['enable_feedback']:
            raise PicoException('Problem feedback is not currently being ' +
                                'accepted.', 500)

        req = feedback_list_req.parse_args(strict=True)

        # Handle args if they are present but unset
        for arg in ['pid', 'uid', 'tid']:
            if req[arg] == '':
                req[arg] = None

        return jsonify(api.problem_feedback.get_problem_feedback(
            pid=req['pid'], tid=req['tid'], uid=req['uid']
        ))

    # @block_before_competition
    # @check_csrf
    @require_login
    @ns.response(201, 'Feedback accepted')
    @ns.response(400, 'Error parsing request')
    @ns.response(404, 'Problem not found')
    @ns.response(500, 'Feedback submissions disabled')
    @ns.expect(feedback_submission_req)
    def post(self):
        """
        Submit problem feedback.

        Will update existing feedback if the current user and provided
        problem ID match a previous submission.
        """
        if not api.config.get_settings()['enable_feedback']:
            raise PicoException(
                'Problem feedback is not currently being accepted.',
                response_code=500
            )
        req = feedback_submission_req.parse_args(strict=True)
        api.problem_feedback.upsert_feedback(
            req['pid'], req['feedback']
        )
        res = jsonify({
            "success": True
        })
        res.status_code = 201
        return res
