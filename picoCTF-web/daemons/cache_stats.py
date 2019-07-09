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
        get_all_team_scores(include_ineligible=True)

        print("Caching the public scoreboard graph...")
        cache(get_top_teams_score_progressions, include_ineligible=False,
              gid=None)
        cache(get_top_teams_score_progressions, include_ineligible=True,
              gid=None)

        print("Caching the scoreboard graph for each group...")
        for group in api.group.get_all_groups():
            get_group_scores(gid=group['gid'])
            cache(get_top_teams_score_progressions,
                  include_ineligible=True,
                  gid=group['gid'])

        print("Caching number of solves for each problem.")
        for problem in api.problem.get_all_problems():
            print(problem["name"],
                  cache(get_problem_solves, problem["pid"]))

        print("Caching Invalid Instance Submissions.")
        cache(check_invalid_instance_submissions)


if __name__ == '__main__':
    run()
