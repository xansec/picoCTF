"""Achievement related endpoints."""
from flask import jsonify
from flask_restplus import Namespace, Resource, reqparse, inputs
from api.common import PicoException
import api.achievement
ns = Namespace('achievements', description='Achievement related endpoints')

achievement_req = reqparse.RequestParser()
achievement_req.add_argument(
    'name', required=True, type=str,
    help='Name of the achievement.')
achievement_req.add_argument(
    'score', required=True, type=inputs.natural,
    help='Point value of the achievement (positive integer).')
achievement_req.add_argument(
    'description', required=True, type=str,
    help='Description of the achievement.')
achievement_req.add_argument(
    'processor', required=True, type=str,
    help='Path to the achievement processor.')
achievement_req.add_argument(
    'hidden', required=True, type=inputs.boolean,
    help='Hide this achievement?')
achievement_req.add_argument(
    'image', required=True, type=str,
    help='Path to achievement image.')
achievement_req.add_argument(
    'smallimage', required=True, type=str,
    help='Path to achievement thumbnail.')
achievement_req.add_argument(
    'disabled', required=True, type=inputs.boolean,
    help='Disable this achievement?')
achievement_req.add_argument(
    'multiple', required=True, type=inputs.boolean,
    help='Allow earning multiple instances of this achievement?')
achievement_patch_req = achievement_req.copy()
for arg in achievement_patch_req.args:
    arg.required = False


@ns.route('/')
class AchievementList(Resource):
    """Get the full list of achievements, or add a new achievement."""

    def get(self):
        """Get the full list of achievements."""
        return api.achievement.get_all_achievements(), 200

    @ns.expect(achievement_req)
    @ns.response(201, 'Achievement added')
    @ns.response(400, 'Error parsing request')
    def post(self):
        """Insert a new achievement."""
        req = achievement_req.parse_args(strict=True)
        aid = api.achievement.insert_achievement(**req)
        res = jsonify({
            'success': True,
            'aid': aid
            })
        res.response_code = 201
        return res


@ns.route('/<string:achievement_id>')
@ns.response(404, 'Achievement not found')
class Achievement(Resource):
    """Get or update a specific achievement."""

    @ns.response(200, 'Success')
    def get(self, achievement_id):
        """Retrieve a specific achievement."""
        res = api.achievement.get_achievement(achievement_id)
        if not res:
            raise PicoException('Achievement not found', status_code=404)
        else:
            return res, 200

    @ns.expect(achievement_req)
    @ns.response(200, 'Success')
    @ns.response(400, 'Error parsing request')
    @ns.response(404, 'Achievement not found')
    def put(self, achievement_id):
        """Replace an existing achievement."""
        req = achievement_req.parse_args(strict=True)
        aid = api.achievement.update_achievement(achievement_id, req)
        if aid is None:
            raise PicoException('Achievement not found', status_code=404)
        res = jsonify({
            'success': True,
            'aid': aid
            })
        res.response_code = 200
        return res

    @ns.expect(achievement_patch_req)
    @ns.response(200, 'Success')
    @ns.response(400, 'Error parsing request')
    @ns.response(404, 'Achievement not found')
    def patch(self, achievement_id):
        """Update an existing achievement."""
        req = {
            k: v for k, v in achievement_patch_req.parse_args().items() if
            v is not None
        }
        aid = api.achievement.update_achievement(achievement_id, req)
        if aid is None:
            raise PicoException('Achievement not found', status_code=404)
        res = jsonify({
            'success': True,
            'aid': aid
            })
        res.response_code = 200
        return res
