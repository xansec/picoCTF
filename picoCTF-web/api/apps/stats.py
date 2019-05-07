"""Routing functions for /api/stats/."""
import math

from bson import json_util
from flask import Blueprint, request

import api.auth
import api.stats
import api.team
import api.user
from api.annotations import block_before_competition, require_login
from api.common import WebError, WebSuccess

blueprint = Blueprint("stats_api", __name__)
scoreboard_page_len = 50

@blueprint.route(
    '/scoreboard', defaults={
        'board': None,
        'page': 1
    }, methods=['GET'])
@blueprint.route('/scoreboard/<board>/<int:page>', methods=['GET'])
@block_before_competition()
def get_scoreboard_hook(board, page):
    def get_user_pos(scoreboard, tid):
        for pos, team in enumerate(scoreboard):
            if team["tid"] == tid:
                return pos
        return 1

    user = None
    if api.auth.is_logged_in():
        user = api.user.get_user()

    # Old board, limit 1-50
    if board is None:
        result = {'tid': 0, 'groups': []}
        global_board = api.stats.get_all_team_scores(include_ineligible=True)
        result['global'] = {
            'name': 'global',
            'pages': math.ceil(len(global_board) / scoreboard_page_len),
            'start_page': 1
        }
        if user is None:
            result['global']['scoreboard'] = global_board[:scoreboard_page_len]
        else:
            result['tid'] = user['tid']
            global_pos = get_user_pos(global_board, user["tid"])
            start_slice = math.floor(global_pos / 50) * 50
            result['global']['scoreboard'] = global_board[start_slice:
                                                          start_slice + 50]
            result['global']['start_page'] = math.ceil((global_pos + 1) / 50)

            result['country'] = user["country"]
            student_board = api.stats.get_all_team_scores()
            student_pos = get_user_pos(student_board, user["tid"])
            start_slice = math.floor(student_pos / 50) * 50
            result['student'] = {
                'name': 'student',
                'pages': math.ceil(len(student_board) / scoreboard_page_len),
                'scoreboard': student_board[start_slice:start_slice + 50],
                'start_page': math.ceil((student_pos + 1) / 50),
            }

            for group in api.team.get_groups(uid=user["uid"]):
                # this is called on every scoreboard pageload and should be
                # cached to support large groups
                group_board = api.stats.get_group_scores(gid=group['gid'])
                group_pos = get_user_pos(group_board, user["tid"])
                start_slice = math.floor(group_pos / 50) * 50
                result['groups'].append({
                    'gid':
                    group['gid'],
                    'name':
                    group['name'],
                    'scoreboard':
                    group_board[start_slice:start_slice + 50],
                    'pages':
                    math.ceil(len(group_board) / scoreboard_page_len),
                    'start_page':
                    math.ceil((group_pos + 1) / 50),
                })

        return WebSuccess(data=result), 200
    else:
        if board in ["groups", "global", "student"]:
            # 1-index page
            start = scoreboard_page_len * (page - 1)
            end = start + scoreboard_page_len
            result = []
            if api.auth.is_logged_in():
                user = api.user.get_user()
            if board == "groups":
                for group in api.team.get_groups(uid=user.get("uid")):
                    group_board = api.stats.get_group_scores(gid=group['gid'])
                    result.append({
                        'gid': group['gid'],
                        'name': group['name'],
                        'scoreboard': group_board[start:end]
                    })
            elif board == "global":
                result = api.stats.get_all_team_scores(
                    include_ineligible=True)[start:end]
            elif board == "student":
                result = api.stats.get_all_team_scores()[start:end]
            else:
                result = []
            return WebSuccess(data=result), 200
        else:
            return WebError("A valid board must be specified"), 404


@blueprint.route('/top_teams/score_progression', methods=['GET'])
def get_top_teams_score_progressions_hook():
    include_ineligible = request.args.get("include_ineligible", "false")
    include_ineligible = json_util.loads(include_ineligible)

    return WebSuccess(
        data=api.stats.get_top_teams_score_progressions(
            include_ineligible=include_ineligible)), 200


@blueprint.route('/group/score_progression', methods=['GET'])
def get_group_top_teams_score_progressions_hook():
    gid = request.args.get("gid", None)
    return WebSuccess(
        data=api.stats.get_top_teams_score_progressions(
            gid=gid, include_ineligible=True)), 200
