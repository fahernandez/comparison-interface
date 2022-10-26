"""Initialize the website application"""
import os
from flask import Flask, render_template, current_app, session
from datetime import datetime as dt
from datetime import timedelta
from whitenoise import WhiteNoise
# Custom libraries
from configuration.flask import Settings as FlaskSettings
from configuration.website import Settings as WS
from model.connection import db
from model.schema import WebsiteControl
from view.request import Request
import command
import route


def create_app(test_config=None):
    """Start Flask website application

    Args:
        config_filename (object, optional): Default configuration file.
        Defaults to None. Used for testing.
    """
    # Create and configure the app
    app = Flask(
        __name__,
        instance_relative_config=True,
        static_folder="static"
    )
    app.config.from_object(FlaskSettings)
    if test_config is not None:
        app.config.from_mapping(test_config)

    # Create folder for storing temporal files (if it doesn't exists)
    tmp_location = os.path.abspath(os.path.dirname(__file__)) + '/' + \
        app.config['TEMPORAL_DATA_LOCATION']
    if not os.path.exists(tmp_location):
        os.makedirs(tmp_location)
        app.logger.info('Creating folder to store temporal files.')

    # Register the database
    db.init_app(app)

    # Register the custom Flask commands
    app.register_blueprint(command.blueprint)

    # Register the application views
    app.register_blueprint(route.blueprint)

    # Register function executed before any request.
    app.before_request(__before_request)

    # Register page errors
    app.register_error_handler(404, __page_not_found)
    app.register_error_handler(500, __page_unexpected_condition)

    # Add the management for static libraries
    WHITENOISE_MAX_AGE = 31536000 if not app.config["DEBUG"] else 0
    app.wsgi_app = WhiteNoise(
        app.wsgi_app,
        root=os.path.join(os.path.dirname(__file__), "static"),
        prefix="assets/",
        max_age=WHITENOISE_MAX_AGE,
    )

    return app


def __before_request():
    """Executes a series of procedures before every request."""
    __validate_app_integrity()
    __configure_user_session()


def __configure_user_session():
    """Configure the user's session behavior"""
    app = current_app
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=app.config['SESSION_MINUTES_VALIDITY'])
    session.modified = True


def __validate_app_integrity():
    """Stop the server execution if the configuration file was modified after the
    setup of the application was executed. The configuration file is used on the website
    execution during runtime. Modification on this files can cause unexpected results.
    """
    app = current_app
    modification_date = None
    with app.app_context():
        try:
            # Get the application control variables
            w = WebsiteControl()
            conf = w.get_conf()

            WS.set_configuration_location(app, conf.configuration_file)
            setup_exec_date = conf.setup_exec_date

            # Get the last modification date of the configuration file (UTC)
            modification_date = os.path.getmtime(WS.get_configuration_location(app))
            modification_date = dt.utcfromtimestamp(modification_date)
        except Exception as e:
            app.logger.critical(str(e))
            raise RuntimeError("Application not initialized yet. Please read the README.md file.")

        # Stop the server execution if the configuration file was modified after the
        # setup of the application was executed.
        if modification_date is None or modification_date > setup_exec_date:
            app.logger.critical("Configuration file cannot be modified after the website "
                                "setup. Modified on: %s UTC. Setup executed on : %s UTC. "
                                "Please execute >Flask setup< again."
                                % (modification_date.strftime("%m/%d/%Y, %H:%M:%S"),
                                   setup_exec_date.strftime("%m/%d/%Y, %H:%M:%S"))
                                )
            raise RuntimeError("Application unhealthy state. "
                               "Please contact the website administrator.")


def __page_not_found(e):
    """Return 404 page"""
    return render_template('404.html',
                           **Request(current_app, session).get_layout_text()), 404


def __page_unexpected_condition(e):
    """Return 500 page"""
    return render_template('500.html',
                           **Request(current_app, session).get_layout_text()), 500


# Make the application global available
app = create_app()
