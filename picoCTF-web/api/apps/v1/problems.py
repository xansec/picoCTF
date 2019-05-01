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
from api.common import PicoException

from .schemas import shell_server_out, problem_patch_req

ns = Namespace('problems', description='Problem management')


@ns.route('/')
class ProblemList(Resource):
    """Get the list of problems, or update the problem/bundle state."""

    # @require_admin
    def get(self):
        """
        Get the list of problems.

        As an admin, displays the full list of problems.
        As a user, displays a filtered list of unlocked problems.
        """
        return api.problem.get_all_problems(show_disabled=True), 200

    # @require_admin
    @ns.expect(shell_server_out)
    @ns.response(200, 'Problem list updated')
    @ns.response(400, 'Error parsing request')
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
