"""Event management."""

import api
from api import block_before_competition, PicoException, require_admin
from flask import jsonify
from flask_restplus import Namespace, Resource

from .schemas import event_req, scoreboard_page_req

ns = Namespace('events', description='Event management')


@ns.route('')
class EventList(Resource):
    """Get the list of all events, or add a new event."""

    @require_admin
    @ns.response(200, 'Success')
    @ns.response(401, 'Not logged in')
    @ns.response(403, 'Permission denied')
    def get(self):
        """Get the list of all events."""
        return jsonify(api.events.get_all_events())

    @require_admin
    @ns.response(201, 'Event added')
    @ns.response(400, 'Error parsing request')
    @ns.response(401, 'Not logged in')
    @ns.response(403, 'Permission denied')
    @ns.expect(event_req)
    def post(self):
        """Add a new event."""
        req = event_req.parse_args(strict=True)
        eid = api.events.add_event(
            req['name'],
            eligibility_conditions=req['eligibility_conditions'],
            sponsor=req['sponsor'],
            logo=req['logo']
        )
        res = jsonify({
            'success': True,
            'eid': eid
        })
        res.status_code = 201
        return res


@ns.route('/<string:event_id>')
class Event(Resource):
    """Get a specific event."""

    @require_admin
    @ns.response(200, 'Success')
    @ns.response(401, 'Not logged in')
    @ns.response(403, 'Permission denied')
    def get(self, event_id):
        """Get a specific event."""
        event = api.events.get_event(event_id)
        if not event:
            raise PicoException('Event not found', 404)
        return jsonify(event)


@ns.route('/<string:event_id>/scoreboard')
class ScoreboardPage(Resource):
    """
    Get a scoreboard page for an event.

    If a page is not specified, will attempt to return the page containing the
    current team, falling back to the first page if neccessary.
    """

    @block_before_competition
    @ns.response(200, 'Success')
    @ns.response(422, 'Competition has not started')
    @ns.expect(scoreboard_page_req)
    def get(self, event_id):
        """Retrieve a scoreboard page for an event."""
        req = scoreboard_page_req.parse_args(strict=True)
        return jsonify(
            api.stats.get_scoreboard_page(
                {'event_id': event_id}, req['page']))
