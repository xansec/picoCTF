#!/usr/bin/env python3


import api
import api.group
import api.stats


def run():
    """Run the stat caching daemon."""
    with api.create_app().app_context():
        def cache(f, *args, **kwargs):
            result = f(reset_cache=True, *args, **kwargs)
            return result

        print("Caching registration stats.")
        cache(api.stats.get_registration_count)

        print("Caching the public scoreboard entries...")
        cache(api.stats.get_all_team_scores)
        cache(api.stats.get_all_team_scores, include_ineligible=True)

        print("Caching the public scoreboard graph...")
        cache(api.stats.get_top_teams_score_progressions)
        cache(api.stats.get_top_teams_score_progressions,
              include_ineligible=True)

        print("Caching the scoreboard graph for each group...")
        for group in api.group.get_all_groups():
            # cache(
            #      api.stats.get_top_teams_score_progressions,
            #      gid=group['gid'])
            cache(
                  api.stats.get_top_teams_score_progressions,
                  gid=group['gid'],
                  include_ineligible=True)
            cache(api.stats.get_group_scores, gid=group['gid'])

        print("Caching number of solves for each problem.")
        for problem in api.problem.get_all_problems():
            print(problem["name"],
                  cache(api.stats.get_problem_solves, problem["pid"]))


if __name__ == '__main__':
    run()
