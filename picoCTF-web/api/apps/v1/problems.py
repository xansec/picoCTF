"""
Problem related endpoints.

Problems and bundles are not treated as usual CRUD resources because
the source of truth for problem and bundle state is the shell server(s).

So bundles and problems are essentially treated as read-only, with the
exception of the PATCH /problems endpoint, which takes a shell server's
output and updates the state of the problems and bundles accordingly.

There are two other exceptions to this:
- A problem's "disabled" property is a web API-only concept. The shell server
  will continue to serve the problem either way.
- A bundle's "dependencies_enabled" property works similarly.

These two properties are the ONLY fields modifiable via PATCH reqests on
problem or bundle resources, respectively.

Note that bundles, despite their name, are really just documents specifying
unlock requirements for existing problems.
"""
from flask import jsonify
from flask_restplus import Namespace, Resource

import api.problem
import api.user
import api.team
from api.common import PicoException

from .schemas import shell_server_out, problem_patch_req, problems_req

ns = Namespace('problems', description='Problem management')


@ns.response(400, 'Error parsing request')
@ns.response(401, 'Not logged in')
@ns.response(403, 'Not authorized')
@ns.route('/')
class ProblemList(Resource):
    """Get the list of problems, or update the problem/bundle state."""

    # @require_admin
    @ns.response(200, 'Success')
    @ns.expect(problems_req)
    def get(self):
        """
        Get the list of problems, with optional filtering.

        By default, only problems unlocked by your team will be displayed.
        Teachers or admins can override this by specifying
        '?unlocked_only=false'. However, teachers will only recieve problems'
        names, categories, and scores when doing this.
        """
        req = problems_req.parse_args(strict=True)

        # Handle the 'category' arg if present but unset
        if req['category'] == '':
            req['category'] = None

        # To begin, get all problems, filtered by category and include_disabled
        problems = api.problem.get_all_problems(
            category=req['category'],
            show_disabled=req['include_disabled'])

        # Handle the solved_only param
        if req['solved_only']:
            problems = [p for p in problems if p['pid'] in
                        api.problem.get_solved_pids(
                            api.user.get_team()
                        )]

        # Handle the unlocked_only param, which depends on user role
        is_teacher = api.user.is_teacher()
        is_admin = api.user.is_admin()
        if req['unlocked_only'] is True:
            if not is_teacher and not is_admin:
                raise PicoException(
                    'You must be a teacher or admin to use ' +
                    'unlocked_only=false.', status_code=403)
            if not is_admin:
                # Teachers recieve only a reduced subset of fields
                # when getting all problems.
                problems = [{
                    'name': p['name'],
                    'category': p['category'],
                    'score': p['score']
                    } for p in problems]
        else:
            # When unlocked_only is False (by default), strip out any problems
            # that have not been unlocked by the current user's team.
            problems = [p for p in problems if p['pid'] in
                        api.problem.get_unlocked_pids(
                            api.user.get_team()
                        )]
            # Additionally, show only fields from the assigned instance.
            problems = [api.problem.filter_problem_instances(p) for p in
                        problems]

        # Strip out any system properties for non-admin users
        if not is_admin:
            problems = api.problem.sanitize_problem_data(problems)

        # Handle the count_only param
        if req['count_only']:
            res = jsonify({
                'count': len(problems)
            })
            res.status_code = 200
            return res
        else:
            res = jsonify(problems)
            res.status_code = 200
            return res

    # @require_admin
    @ns.expect(shell_server_out)
    @ns.response(200, 'Problem list updated')
    @ns.response(404, 'Shell server not found')
    def patch(self):
        """
        Update the problem and bundle state via shell server output.

        If `shell_manager publish` output is not provided as a payload,
        will attempt to automatically request it from the provided
        shell server.

        Note that this will only add new / update existing problems – if a
        problem has been removed from the shell server, it should be
        disabled using the PATCH /<problem_id> endpoint or manually
        removed from the database.
        """
        req = {
            k: v for k, v in
            shell_server_out.parse_args(strict=True).items() if
            v is not None
        }
        # Check that the provided sid is valid
        found = api.shell_servers.get_server(req['sid'])
        if found is None:
            raise PicoException('Shell server not found', status_code=404)
        if 'problems' in req:
            api.problem.load_published({
                'problems': req['problems'],
                'bundles': req['bundles'],
                'sid': req['sid']
            })
        else:
            output = api.shell_servers.get_publish_output(req['sid'])
            api.problem.load_published({
                'problems': output['problems'],
                'bundles': output['bundles'],
                'sid': req['sid']
            })

        res = jsonify({
            'success': True,
            })
        res.response_code = 200
        return res


@ns.response(200, 'Success')
@ns.response(404, 'Problem not found')
@ns.route('/<string:problem_id>')
class Problem(Resource):
    """Get or update the availability of a specific problem."""

    # @TODO: -restrict availability to unlocked if not admin
    #        -strip out instance information if not admin
    def get(self, problem_id):
        """Retrieve a specific problem."""
        problem = api.problem.get_problem(problem_id)
        if not problem:
            raise PicoException('Problem not found', status_code=404)
        else:
            return problem, 200

    # @require_admin
    @ns.response(400, 'Error parsing request')
    @ns.expect(problem_patch_req)
    def patch(self, problem_id):
        """
        Update a specific problem.

        The only valid field for this method is "disabled".
        Other fields are pulled from the shell server, and
        can be updated via the PATCH /problems endpoint.
        """
        req = problem_patch_req.parse_args(strict=True)
        pid = api.problem.set_problem_availability(problem_id, req['disabled'])
        if not pid:
            raise PicoException('Problem not found', status_code=404)
        else:
            res = jsonify({
                "success": True
            })
            res.status_code = 200
            return res
