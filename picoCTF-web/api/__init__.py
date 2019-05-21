"""Configures the Flask app."""

import inspect
import logging
import traceback

from flask import Flask, jsonify, session
from flask_mail import Mail
from werkzeug.contrib.fixers import ProxyFix

# these have to come first to avoid circular import issues
# from api.cache import memoize # noqa
from api.common import check, PicoException, validate # noqa
from api.logger import log_action # noqa
from api.user import require_login, require_teacher, require_admin, check_csrf # noqa
from api.config import block_before_competition, block_after_competition # noqa

import api.achievement
import api.bundles
import api.cache
import api.common
import api.config
import api.db
import api.email
import api.group
import api.logger
import api.problem
import api.problem_feedback
import api.shell_servers
import api.stats
import api.submissions
import api.team
import api.token
import api.user
from api.apps.v0 import blueprint as v0_blueprint
from api.apps.v1 import blueprint as v1_blueprint

log = logging.getLogger(__name__)


def get_origin_logger(exception):
    """Get the logger for the module where an exception was raised."""
    try:
        origin = inspect.getmodule(inspect.trace()[-1]).__name__
        origin_logger = logging.getLogger(origin)
        return origin_logger
    except Exception as e:
        log.error('Failed to get origin logger for exception: ' + str(e) +
                  ' - returning fallback logger')
        return logging.getLogger('origin_fallback')


def update_mail_config(app):
    """Update the Flask-Mail config based on the current settings."""
    with app.app_context():
        settings = api.config.get_settings()
        if settings["email"]["enable_email"]:
            app.config["MAIL_SERVER"] = settings["email"]["smtp_url"]
            app.config["MAIL_PORT"] = settings["email"]["smtp_port"]
            app.config["MAIL_USERNAME"] = settings["email"]["email_username"]
            app.config["MAIL_PASSWORD"] = settings["email"]["email_password"]
            app.config["MAIL_DEFAULT_SENDER"] = settings["email"]["from_addr"]
            if (settings["email"]["smtp_security"] == "TLS"):
                app.config["MAIL_USE_TLS"] = True
            elif (settings["email"]["smtp_security"] == "SSL"):
                app.config["MAIL_USE_SSL"] = True
            api.email.mail = Mail(app)
        else:
            # Use a testing configuration
            app.config['MAIL_SUPPRESS_SEND'] = True
            app.config['MAIL_DEFAULT_SENDER'] = 'testing@picoctf.com'
            api.email.mail = Mail(app)


def create_app(config={}):
    """
    Configure and create the Flask app via factory function.

    Args:
        config (optional): dict of app.config settings to override
    """
    app = Flask(__name__, static_url_path="/")
    app.wsgi_app = ProxyFix(app.wsgi_app)

    # Load default Flask settings
    app.config.from_pyfile('default_settings.py')
    # Override defaults with settings file passed in environment variable
    app.config.from_envvar('APP_SETTINGS_FILE', silent=True)
    # If any config settings specified, set them
    for k, v in config.items():
        app.config[k] = v

    # Configure Mail object based on runtime settings
    update_mail_config(app)

    # Register blueprints
    app.register_blueprint(
        v0_blueprint, url_prefix="/api/v0"
    )
    app.register_blueprint(
        v1_blueprint, url_prefix="/api/v1"
    )

    # Report all validation errors (RequestParser-specific setting)
    app.config['BUNDLE_ERRORS'] = True

    # Register error handlers
    @app.errorhandler(PicoException)
    def handle_pico_exception(e):
        """Handle exceptions."""
        response = jsonify(e.to_dict())
        response.status_code = e.status_code
        return response

    if not app.debug:
        @app.errorhandler(Exception)
        def handle_generic_exception(e):
            # @TODO log picoexceptions also?
            get_origin_logger(e).error(traceback.format_exc())
            response = jsonify({
                'message': "An internal error occurred. " +
                           "Please contact an administrator."})
            response.status_code = 500
            return response

    # Configure logging
    with app.app_context():
        api.logger.setup_logs({"verbose": 2})

    # Register a post-request function
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Methods',
                             'GET, POST, PUT, PATCH, DELETE, OPTIONS')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, *')
        response.headers.add('Cache-Control', 'no-cache')
        response.headers.add('Cache-Control', 'no-store')
        with app.app_context():
            if app.debug:
                response.headers.add('Access-Control-Allow-Origin', '*')
        if api.user.is_logged_in():
            # Flask 1.0+ bug loads config SESSION_COOKIE_DOMAIN
            # correctly as None but later converts it to bool false.
            domain = app.config['SESSION_COOKIE_DOMAIN']
            if not domain:
                domain = None

            # Set the CSRF token cookie
            if 'token' not in session:
                csrf_token = api.common.token()
                session['token'] = csrf_token
            response.set_cookie('token', session['token'], domain=domain)

        return response

    return app
