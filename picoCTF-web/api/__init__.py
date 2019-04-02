"""Configures the Flask app."""

from datetime import datetime

from flask import Flask, request, session
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
from api.annotations import api_wrapper
from api.common import WebSuccess


def create_app(test_config=None):
    """Configure and create the Flask app via factory function."""
    app = Flask(__name__, static_url_path="/")
    app.wsgi_app = ProxyFix(app.wsgi_app)

    # Load default settings
    app.config.from_pyfile('default_settings.py')
    # Override defaults with settings file passed in environment variable
    app.config.from_envvar('APP_SETTINGS_FILE', silent=True)

    # Configure email settings based on database values
    with app.app_context():
        db_settings = api.config.get_settings()
        if db_settings["email"]["enable_email"]:
            app.config["MAIL_SERVER"] = db_settings["email"]["smtp_url"]
            app.config["MAIL_PORT"] = db_settings["email"]["smtp_port"]
            app.config["MAIL_USERNAME"] = db_settings["email"]["email_username"]
            app.config["MAIL_PASSWORD"] = db_settings["email"]["email_password"]
            app.config["MAIL_DEFAULT_SENDER"] = db_settings["email"]["from_addr"]
            if (db_settings["email"]["smtp_security"] == "TLS"):
                app.config["MAIL_USE_TLS"] = True
            elif (db_settings["email"]["smtp_security"] == "SSL"):
                app.config["MAIL_USE_SSL"] = True
            api.email.mail = Mail(app)
        else:
            # Use a testing configuration
            app.config['MAIL_SUPPRESS_SEND'] = True
            app.config['MAIL_DEFAULT_SENDER'] = 'testing@picoctf.com'
            api.email.mail = Mail(app)

    # Register routes
    app.register_blueprint(api.routes.user.blueprint, url_prefix="/api/user")
    app.register_blueprint(api.routes.team.blueprint, url_prefix="/api/team")
    app.register_blueprint(api.routes.stats.blueprint, url_prefix="/api/stats")
    app.register_blueprint(api.routes.admin.blueprint, url_prefix="/api/admin")
    app.register_blueprint(api.routes.group.blueprint, url_prefix="/api/group")
    app.register_blueprint(api.routes.problem.blueprint,
                           url_prefix="/api/problems")
    app.register_blueprint(api.routes.achievements.blueprint,
                           url_prefix="/api/achievements")

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
            # correctly as None but later converts it to bool false. (@todo)
            domain = app.config['SESSION_COOKIE_DOMAIN']
            if not domain:
                domain = None

            if 'token' in session:
                response.set_cookie('token', session['token'], domain=domain)
            else:
                csrf_token = api.common.token()
                session['token'] = csrf_token
                response.set_cookie('token', csrf_token, domain=domain)

        # JB: This is a hack. We need a better solution (@todo)
        if request.path[0:19] != "/api/autogen/serve/":
            response.mimetype = 'application/json'
        return response

    # Add a route for getting the time
    @app.route('/api/time', methods=['GET'])
    @api_wrapper
    def get_time():
        return WebSuccess(data=int(datetime.utcnow().timestamp()))

    return app
