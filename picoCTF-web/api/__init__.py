"""Configures the Flask app."""

import inspect
import logging
import traceback
from datetime import datetime

from bson import json_util
from flask import Flask, session
from flask_mail import Mail
from werkzeug.contrib.fixers import ProxyFix

import api.auth
import api.config
import api.logger
import api.routes.achievements
import api.routes.admin
import api.routes.group
import api.routes.problem
import api.routes.stats
import api.routes.team
import api.routes.user
from api.common import (InternalException, SevereInternalException, WebError,
                        WebException, WebResponse, WebSuccess)

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


def create_app(test_config=None):
    """Configure and create the Flask app via factory function."""
    app = Flask(__name__, static_url_path="/")
    app.wsgi_app = ProxyFix(app.wsgi_app)

    # Load default Flask settings
    app.config.from_pyfile('default_settings.py')
    # Override defaults with settings file passed in environment variable
    app.config.from_envvar('APP_SETTINGS_FILE', silent=True)

    # Configure Mail object based on runtime settings
    update_mail_config(app)

    # Register routes
    app.register_blueprint(api.routes.user.blueprint, url_prefix="/api/user")
    app.register_blueprint(api.routes.team.blueprint, url_prefix="/api/team")
    app.register_blueprint(api.routes.stats.blueprint, url_prefix="/api/stats")
    app.register_blueprint(api.routes.admin.blueprint, url_prefix="/api/admin")
    app.register_blueprint(api.routes.group.blueprint, url_prefix="/api/group")
    app.register_blueprint(
        api.routes.problem.blueprint, url_prefix="/api/problems")
    app.register_blueprint(
        api.routes.achievements.blueprint, url_prefix="/api/achievements")

    # Register error handlers
    @app.errorhandler(WebException)
    def handle_web_exception(e):
        return WebError(e.args[0], e.data).as_json()

    @app.errorhandler(InternalException)
    def handle_internal_exception(e):
        get_origin_logger(e).error(traceback.format_exc())
        return WebError(e.args[0]).as_json()

    @app.errorhandler(SevereInternalException)
    def handle_severe_internal_exception(e):
        get_origin_logger(e).critical(traceback.format_exc())
        return WebError(
                "There was a critical internal error. " +
                "Contact an administrator."
            ).as_json()

    @app.errorhandler(Exception)
    def handle_generic_exception(e):
        get_origin_logger(e).error(traceback.format_exc())
        return WebError("An error occurred. Please contact an administrator.").as_json()

    # Configure logging
    with app.app_context():
        api.logger.setup_logs({"verbose": 2})

    # Register a post-request function
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Methods', 'GET, POST')
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, *')
        response.headers.add('Cache-Control', 'no-cache')
        response.headers.add('Cache-Control', 'no-store')
        if api.auth.is_logged_in():
            # Flask 1.0+ bug loads config SESSION_COOKIE_DOMAIN
            # correctly as None but later converts it to bool false.
            domain = app.config['SESSION_COOKIE_DOMAIN']
            if not domain:
                domain = None

            if 'token' not in session:
                csrf_token = api.common.token()
                session['token'] = csrf_token
            response.set_cookie('token', session['token'], domain=domain)

        response.mimetype = 'application/json'
        return response

    # Add a route for getting the time
    @app.route('/api/time', methods=['GET'])
    def get_time() -> WebResponse:
        return WebSuccess(data=int(datetime.utcnow().timestamp())).as_json()

    return app
