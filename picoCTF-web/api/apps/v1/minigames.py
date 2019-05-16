"""Minigame submission endpoint."""
import hashlib

from flask import jsonify
from flask_restplus import Namespace, Resource

import api
from api import PicoException, require_login, block_before_competition

from .schemas import minigame_submission_req

ns = Namespace('minigames', description='Minigame submission endpoint')


@ns.route('/submit')
class MinigameSubmissionResponse(Resource):
    """Submit a verification key for a minigame."""

    # @check_csrf
    @block_before_competition
    @require_login
    @ns.response(200, 'Success')
    @ns.response(400, 'Error parsing request')
    @ns.response(401, 'Not logged in')
    @ns.response(404, 'Minigame not found')
    @ns.response(422, 'Invalid verification key or competition ' +
                      'has not started')
    @ns.expect(minigame_submission_req)
    def post(self):
        """Submit a verification key for a minigame."""
        req = minigame_submission_req.parse_args(strict=True)
        curr_user = api.user.get_user()

        settings = api.config.get_settings()
        minigame_config = settings.get("minigame", {}).get("token_values", 0)

        if req['minigame_id'] not in minigame_config:
            raise PicoException('Minigame not found', 404)

        hashstring = req['minigame_id'] + curr_user['username'] + \
            minigame_config.get('secret')

        if hashlib.md5(hashstring.encode('utf-8')).hexdigest() != \
                req['verification_key']:
            raise PicoException('Invalid verification key', 422)

        previously_solved = True
        tokens_earned = 0
        if req['minigame_id'] not in curr_user['completed_minigames']:
            previously_solved = False
            tokens_earned = minigame_config[req['minigame_id']]
            db = api.db.get_conn()
            db.users.update_one({
                'uid': curr_user["uid"],
                'completed_minigames': {
                    '$ne': req['minigame_id']
                }
            }, {
                '$push': {
                    'completed_minigames': req['minigame_id']
                },
                '$inc': {
                    'tokens': tokens_earned
                }
            })

        return jsonify({
            'success': True,
            'previously_solved': previously_solved,
            'tokens_earned': tokens_earned,
            'new_token_count': api.user.get_user()['tokens']
        })
