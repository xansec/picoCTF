#!/usr/bin/env python3


import api
import api.group
from api.stats import (check_invalid_instance_submissions, get_all_team_scores,
                       get_group_scores, get_problem_solves,
                       get_registration_count,
                       get_top_teams_score_progressions)


def run():
    """Run the stat caching daemon."""
    with api.create_app().app_context():
        def cache(f, *args, **kwargs):
            result = f(reset_cache=True, *args, **kwargs)
            return result

        print("Caching registration stats.")
        cache(get_registration_count)

        print("Caching the public scoreboard entries...")
        get_all_team_scores()
        for scoreboard in api.scoreboards.get_all_scoreboards():
            get_all_team_scores(scoreboard_id=scoreboard['sid'])

        print("Caching the public scoreboard graph for each scoreboard...")
        for scoreboard in api.scoreboards.get_all_scoreboards():
            cache(get_top_teams_score_progressions,
                  scoreboard_id=scoreboard['sid'], gid=None)

        print("Caching the scoreboard graph for each group...")
        for group in api.group.get_all_groups():
            get_group_scores(gid=group['gid'])
            cache(get_top_teams_score_progressions,
                  gid=group['gid'])

        print("Caching number of solves for each problem.")
        for problem in api.problem.get_all_problems():
            print(problem["name"],
                  cache(get_problem_solves, problem["pid"]))

        print("Caching Invalid Instance Submissions.")
        cache(check_invalid_instance_submissions)


if __name__ == '__main__':
    run()
