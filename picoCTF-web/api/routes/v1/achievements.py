"""Achievement related endpoints."""
from flask import jsonify
from flask_restplus import Namespace, Resource, reqparse, inputs
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


@ns.route('/')
class AchievementList(Resource):
    """Get the full list of achievements, or add a new achievement."""

    def get(self):
        """Get the full list of achievements."""
        return api.achievement._get_all_achievements(), 200

    @ns.expect(achievement_req)
    @ns.response(201, 'Achievement added')
    @ns.response(400, 'Error parsing request')
    @ns.response(409, 'Achievement with same name already exists')
    @ns.response(500, 'Unexpected internal error')
    def post(self):
        """Insert a new achievement."""
        req = achievement_req.parse_args()
        api.achievement.insert_achievement(**req)
        res = jsonify({'success': True})
        res.status_code = 201
        return res
