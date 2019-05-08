"""Module for calculating gameplay statistics."""

import datetime
import math

import pymongo

import api.achievement
import api.annotations
import api.cache
import api.db
import api.group
import api.problem
import api.problem_feedback
import api.stats
import api.submissions
import api.team
from api.cache import memoize

scoreboard_page_len = 50


def _get_problem_names(problems):
    """Extract the names from a list of problems."""
    return [problem['name'] for problem in problems]


# @memoize
def get_score(tid=None, uid=None):
    """
    Get the score for a user or team.

    Args:
        tid: The team id
        uid: The user id
    Returns:
        The users's or team's score
    """
    score = sum([
        problem['score']
        for problem in api.problem.get_solved_problems(tid=tid, uid=uid)
    ])
    return score


def get_team_review_count(tid=None, uid=None):
    """
    Get the count of reviewed problems for a user or team.

    Args:
        tid: team to get count of
        uid: user to get count of (overrides tid)

    Returns: review count
    """
    if uid is not None:
        return len(api.problem_feedback.get_reviewed_pids(uid=uid))
    elif tid is not None:
        count = 0
        for member in api.team.get_team_members(tid=tid):
            count += len(
                api.problem_feedback.get_reviewed_pids(uid=member['uid']))
        return count


# Stored by the cache_stats daemon.
# @memoize
def get_group_scores(gid=None, name=None):
    """
    Get the group scores.

    Args:
        gid: The group id
        name: The group name
    Returns:
        A dictionary containing name, tid, and score
    """
    members = [
        api.team.get_team(tid=tid)
        for tid in api.group.get_group(gid=gid)['members']
    ]

    result = []
    for team in members:
        if team["size"] > 0:
            result.append({
                "name": team['team_name'],
                "tid": team['tid'],
                "affiliation": team["affiliation"],
                "score": get_score(tid=team['tid'])
            })

    return sorted(result, key=lambda entry: entry['score'], reverse=True)


def get_group_average_score(gid=None, name=None):
    """
    Get the average score of teams in a group.

    Args:
        gid: The group id
        name: The group name
    Returns:
        The total score of the group
    """
    group_scores = get_group_scores(gid=gid, name=name)
    total_score = sum([entry['score'] for entry in group_scores])
    return int(total_score / len(group_scores)) if len(group_scores) > 0 else 0


# Stored by the cache_stats daemon
# @memoize
def get_all_team_scores(country=None, include_ineligible=False):
    """
    Get the score for every team in the database.

    Args:
        country: optional restriction by country
        include_ineligible: include ineligible teams

    Returns:
        A list of dictionaries with name and score

    """
    teams = api.team.get_all_teams(include_ineligible=include_ineligible,
                                   country=country)
    db = api.db.get_conn()

    result = []
    all_groups = api.group.get_all_groups()
    for team in teams:
        # Get the full version of the group.
        groups = [
            group for group in all_groups if team["tid"] in group["members"] or
            team["tid"] in group["teachers"] or team["tid"] == group["owner"]
        ]

        # Determine if the user is exclusively a member of hidden groups.
        # If they are, they won't be processed.
        if (len(groups) == 0 or
                any([not (group["settings"]["hidden"]) for group in groups])):
            team_query = db.submissions.find({
                'tid': team['tid'],
                'correct': True
            })
            if team_query.count() > 0:
                lastsubmit = team_query.sort(
                    'timestamp', direction=pymongo.DESCENDING)[0]['timestamp']
            else:
                lastsubmit = datetime.datetime.now()
            score = get_score(tid=team['tid'])
            if score > 0:
                result.append({
                    "name": team['team_name'],
                    "tid": team['tid'],
                    "score": score,
                    "affiliation": team["affiliation"],
                    "lastsubmit": lastsubmit
                })
    time_ordered = sorted(result, key=lambda entry: entry['lastsubmit'])
    time_ordered_time_removed = [{
        'name': x['name'],
        'tid': x['tid'],
        'score': x['score'],
        'affiliation': x['affiliation']
    } for x in time_ordered]
    return sorted(
        time_ordered_time_removed,
        key=lambda entry: entry['score'],
        reverse=True)


def get_all_user_scores():
    """
    Get the score for every user in the database.

    Returns:
        A list of dictionaries with name and score

    """
    users = api.user.get_all_users()

    result = []
    for user in users:
        result.append({
            "name": user['username'],
            "score": get_score(uid=user['uid'])
        })

    return sorted(result, key=lambda entry: entry['score'], reverse=True)


@api.cache.memoize(timeout=120)
def get_problems_by_category():
    """
    Get the list of all problems divided into categories.

    Returns:
        A dictionary of category:[problem list]

    """
    result = {
        cat: _get_problem_names(api.problem.get_all_problems(category=cat))
        for cat in api.problem.get_all_categories()
    }

    return result


def get_team_member_stats(tid):
    """
    Get the solved problems for each member of a given team.

    Args:
        tid: the team id

    Returns:
        A dict of username:[problem list]

    """
    members = api.team.get_team_members(tid=tid)

    return {
        member['username']: _get_problem_names(
            api.problem.get_solved_problems(uid=member['uid']))
        for member in members
    }


def get_problem_submission_stats(pid=None):
    """
    Retrieve the number of valid and invalid submissions for a given problem.

    Args:
        pid: the pid of the problem
        name: the name of the problem
    Returns:
        Dict of {valid: #, invalid: #}
    """

    return {
        "valid":
        len(api.submissions.get_submissions(pid, correctness=True)),
        "invalid":
        len(
            api.submissions.get_submissions(pid, correctness=False))
    }


# @memoize
def get_score_progression(tid=None, uid=None, category=None):
    """
    Find the score and time after each correct submission of a team or user.

    NOTE: this is slower than get_score.
          Do not use this for getting current score.

    Args:
        tid: the tid of the user
        uid: the uid of the user
        category: category filter
    Returns:
        A list of dictionaries containing score and time
    """
    solved = api.problem.get_solved_problems(
        tid=tid, uid=uid, category=category)

    result = []
    score = 0

    problems_counted = set()

    for problem in sorted(solved, key=lambda prob: prob["solve_time"]):
        if problem['pid'] not in problems_counted:
            score += problem["score"]
            problems_counted.add(problem['pid'])
        result.append({
            "score": score,
            "time": int(problem["solve_time"].timestamp())
        })

    return result


# Stored by the cache_stats daemon
# @memoize
def get_problem_solves(pid):
    """
    Return the number of solves for a particular problem.

    Args:
        pid: pid of the problem
    """
    db = api.db.get_conn()

    return db.submissions.find({
        'pid': pid,
        'correct': True
    }).count()


# Stored by the cache_stats daemon
# @memoize
def get_top_teams_score_progressions(
        limit, include_ineligible=False, gid=None):
    """
    Get the score progressions for the top teams.

    Args:
        limit: Number of teams to include
        gid: If specified, compute the progressions for the top teams
             from this group only. Overrides include_ineligible.
        include_ineligible: if specified, include ineligible teams in result

    Returns:
        The top teams and their score progressions.
        A dict of {name: name, score_progression: score_progression}

    """
    if gid is None:
        teams = api.stats.get_all_team_scores(
            include_ineligible=include_ineligible)
    else:
        teams = api.stats.get_group_scores(gid=gid)
    return teams[:limit]

    return [{
        "name": team["name"],
        "affiliation": team["affiliation"],
        "score_progression": get_score_progression(tid=team["tid"]),
    } for team in teams]


# @memoize(timeout=300)
def check_invalid_instance_submissions(gid=None):
    """Get submissions of keys for the wrong problem instance."""
    db = api.db.get_conn()
    shared_key_submissions = []

    group = None
    if gid is not None:
        group = api.group.get_group(gid=gid)

    for problem in api.problem.get_all_problems(show_disabled=True):
        valid_keys = [instance['flag'] for instance in problem['instances']]
        incorrect_submissions = db.submissions.find({
            'pid': problem['pid'],
            'correct': False
        }, {"_id": 0})
        for submission in incorrect_submissions:
            if submission['key'] in valid_keys:
                # make sure that the key is still invalid
                if not api.submissions.grade_problem(
                        submission['pid'], submission['key'],
                        tid=submission['tid']):
                    if group is None or submission['tid'] in group['members']:
                        submission['username'] = api.user.get_user(
                            uid=submission['uid'])['username']
                        submission["problem_name"] = problem["name"]
                        shared_key_submissions.append(submission)

    return shared_key_submissions


# Stored by the cache_stats daemon.
# @memoize
def get_registration_count():
    """Get the user, team, and group counts."""
    db = api.db.get_conn()
    users = db.users.count()
    stats = {
        "users": users,
        "teams": db.teams.count() - users,
        "groups": db.groups.count()
    }
    usernames = set(db.users.find({}).distinct("username"))
    team_names = set(db.teams.find({}).distinct("team_name"))

    real_team_names = team_names - usernames
    real_team_ids = list(
        db.teams.find({
            "team_name": {
                "$in": list(real_team_names)
            }
        }).distinct("tid"))

    teamed_users = db.users.count({"tid": {"$in": real_team_ids}})
    stats["teamed_users"] = teamed_users

    return stats


def get_initial_scoreboard():
    """
    Retrieve the initial scoreboard (first pages of global and student views).

    If a user is logged in, the initial pages will instead be those on which
    that user appears, and their group scoreboards will also be returned.

    Returns: dict of scoreboard information
    """
    def get_user_pos(scoreboard, tid):
        for pos, team in enumerate(scoreboard):
            if team["tid"] == tid:
                return pos
        return 1

        user = None
        if api.auth.is_logged_in():
            user = api.user.get_user()

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
        return result


def get_scorepage_page(board, page_number):
    """
    Retrieve a specific scoreboard page.

    Must be logged in to retrieve a page from the 'groups' board.

    Args:
        board: scoreboard to retrieve a page from (global, student, groups)
        page_number: page number to retrieve

    Raises:
        PicoException: if the 'groups' board is selected but no user is
                       logged in

    """
    start = scoreboard_page_len * (page_number - 1)
    end = start + scoreboard_page_len
    result = []
    if board == "groups":
        user = api.user.get_user()
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
    return result
