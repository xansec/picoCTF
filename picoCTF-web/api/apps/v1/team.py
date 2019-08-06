"""Endpoints related to the current user's team."""
from flask import jsonify
from flask_restplus import Namespace, Resource

import api
from api import (PicoException, block_before_competition, check_csrf,
                 rate_limit, require_login)

from .schemas import (join_group_req, score_progression_req, team_change_req,
                      team_patch_req, update_team_password_req)

ns = Namespace('team', description="Information about the current user's team")

TEAMDATA_FILTER = ['achievements', 'affiliation', 'eligible', 'max_team_size',
                   'members', 'progression', 'score', 'size',
                   'solved_problems', 'team_name', 'tid']

TEAMMEMBER_FILTER = ['affiliation', 'country', 'username', 'usertype']


@ns.route('')
class Team(Resource):
    """The current user's team."""

    @require_login
    @ns.response(200, 'Success')
    @ns.response(401, 'Not logged in')
    def get(self):
        """Get information about the current user's team."""
        current_tid = api.user.get_user()['tid']
        teamdata = {k: v for k, v in
                    api.team.get_team_information(current_tid).items() if
                    k in TEAMDATA_FILTER}
        members = list(map(lambda member: {k: v for k, v in member.items() if
                           k in TEAMMEMBER_FILTER}, teamdata['members']))
        teamdata['members'] = members
        return jsonify(teamdata)

    @require_login
    @ns.response(200, 'Success')
    @ns.response(400, 'Error parsing request')
    @ns.response(401, 'Not logged in')
    @ns.expect(team_patch_req)
    def patch(self):
        """Update team settings."""
        req = team_patch_req.parse_args(strict=True)
        current_tid = api.user.get_user()['tid']
        api.team.update_team(current_tid, req)
        return jsonify({
            'success': True
        })


# @TODO doesn't make sense to return score in both /team and /team/score
@ns.route('/score')
class Score(Resource):
    """Get the current user's team's score."""

    @require_login
    @ns.response(200, 'Success')
    @ns.response(401, 'Not logged in')
    def get(self):
        """Get your team's score."""
        current_tid = api.user.get_user()['tid']
        return jsonify({
            'score': api.stats.get_score(tid=current_tid,
                                         time_weighted=False)
        })


@ns.route('/update_password')
class UpdatePasswordResponse(Resource):
    """Update your team's password."""

    @check_csrf
    @require_login
    @ns.response(200, 'Success')
    @ns.response(400, 'Error parsing request')
    @ns.response(401, 'Not logged in')
    @ns.response(403, 'CSRF token invalid')
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

    @block_before_competition
    @require_login
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


@ns.route('/join')
class TeamJoinResponse(Resource):
    """Join a team."""

    @require_login
    @rate_limit(limit=2, duration=15)
    @ns.response(200, 'Success')
    @ns.response(400, 'Error parsing request')
    @ns.response(401, 'Not logged in')
    @ns.response(403, 'Ineligible to join team')
    @ns.response(404, 'Team not found')
    @ns.response(429, 'Too many requests, slow down!')
    @ns.expect(team_change_req)
    def post(self):
        """Join a team by providing its name and password."""
        current_user = api.user.get_user()
        if current_user['teacher']:
            raise PicoException('Teachers may not join teams!', 403)
        req = team_change_req.parse_args(strict=True)

        # Ensure that the team exists
        team = api.team.get_team(name=req['team_name'])
        if team is None:
            raise PicoException('Team not found', 404)
        api.team.join_team(
            req['team_name'], req['team_password'], current_user)
        return jsonify({
            'success': True
        })


@check_csrf
@require_login
@ns.response(200, 'Success')
@ns.response(400, 'Error parsing request')
@ns.response(401, 'Not logged in')
@ns.response(403, 'Ineligible to join this group or CSRF token invalid')
@ns.response(404, 'Group or group owner not found')
@ns.response(409, 'Already a member of this group')
@ns.expect(join_group_req)
@ns.route('/join_group')
class GroupJoinResponse(Resource):
    """Add your current team to a group."""

    @ns.expect(join_group_req)
    def post(self):
        """Add your current team to a group."""
        req = join_group_req.parse_args(strict=True)
        curr_user = api.user.get_user()

        # Make sure the specified group and owner exist
        owner_team = api.team.get_team(name=req['group_owner'])
        if owner_team is None:
            raise PicoException('Group owner not found', 404)

        group = api.group.get_group(
            name=req['group_name'],
            owner_tid=owner_team['tid']
        )
        if group is None:
            raise PicoException('Group not found', 404)

        # Make sure the current user's team is not already in the group
        group_members = [group['owner']] + group['members'] + group['teachers']
        if curr_user['tid'] in group_members:
            raise PicoException(
                'Your team is already a member of this group.', 409
            )

        # Make sure each member of the current user's team passes the group's
        # email whitelist if present
        members = api.team.get_team_members(tid=curr_user['tid'])
        for member in members:
            if not api.user.verify_email_in_whitelist(
                    member["email"], group['settings']['email_filter']):
                raise PicoException(
                    "{}'s email does not belong to the whitelist " +
                    "for that classroom. Your team may not join this " +
                    "classroom at this time.".format(member["username"]), 403)

        # Join the group as a teacher if the current user's account has
        # teacher permissions
        api.group.join_group(group['gid'], curr_user['tid'],
                             teacher=(curr_user.get('teacher', False)))
        return jsonify({
            'success': True
        })
