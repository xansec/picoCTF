"""
Legacy API shim to support 2019 game.

Provides legacy behavior for:

/api/user/login
/api/problems
/api/problems/submit
/api/user/extdata
/api/team/score
/api/user/status
/api/user/minigame
/api/problems/unlock_walkthrough
/api/problems/walkthrough?pid=<pid>
"""

from flask import Blueprint


blueprint = Blueprint('v0_api', __name__)


@blueprint.route('/test')
def v0_test():
    return 'v0 api test'
