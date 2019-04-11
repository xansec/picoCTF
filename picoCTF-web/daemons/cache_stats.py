#!/usr/bin/env python3


import api
import api.group
import api.stats


def run():
    """Run the stat caching daemon."""
    with api.create_app().app_context():
        print("Caching registration stats.")
        api.stats.get_registration_count(recache=True)

        print("Caching the public scoreboard entries...")
        api.stats.get_all_team_scores(recache=True)
        api.stats.get_all_team_scores(include_ineligible=True, recache=True)

        print("Caching the public scoreboard graph...")
        api.stats.get_top_teams_score_progressions(recache=True)
        api.stats.get_top_teams_score_progressions(
            include_ineligible=True, recache=True)

        print("Caching the scoreboard graph for each group...")
        for group in api.group.get_all_groups():
            api.stats.get_top_teams_score_progressions(
                gid=group['gid'],
                recache=True)
            api.stats.get_top_teams_score_progressions(
                gid=group['gid'],
                include_ineligible=True,
                recache=True)
            api.stats.get_group_scores(gid=group['gid'], recache=True)

        print("Caching number of solves for each problem.")
        for problem in api.problem.get_all_problems():
            print(problem["name"], api.stats.get_problem_solves(
                  pid=problem["pid"], recache=True))
