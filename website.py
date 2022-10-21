"""Initialize the website application"""
import os
from flask import Flask, render_template, current_app, session
from datetime import datetime as dt
from datetime import timedelta
from whitenoise import WhiteNoise
import os
# Custom libraries
from configuration.flask import Settings as FlaskSettings
from configuration.website import Settings as WebSiteSettings
from model.connection import db
from model.schema import WebsiteControl
import command, view


def create_app(test_config=None):
    """Start Flask website application

    Args:
        config_filename (object, optional): Default configuration file. 
        Defaults to None.
    """
    # create and configure the app
    app = Flask(
        __name__,
        instance_relative_config=True,
        static_folder="static"
    )
    if test_config is None:
        app.config.from_object(FlaskSettings)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # Register database
    db.init_app(app)
    
    # Register custom Flask commands
    app.register_blueprint(command.blueprint)

    # Register Blueprints
    app.register_blueprint(view.blueprint)
    
    # Register function executed before any request to validate the app integrity.
    app.before_request(before_request)
    
    # Register page errors
    app.register_error_handler(404, page_not_found)
    app.register_error_handler(500, page_unexpected_condition)
    
    # Add the management for static libraries
    WHITENOISE_MAX_AGE = 31536000 if not app.config["DEBUG"] else 0
    # configure WhiteNoise
    app.wsgi_app = WhiteNoise(
        app.wsgi_app,
        root=os.path.join(os.path.dirname(__file__), "static"),
        prefix="assets/",
        max_age=WHITENOISE_MAX_AGE,
    )

    return app

def before_request():
    """Executes a series of procedures before every request."""
    validate_app_itegrity()
    configure_user_session()

def configure_user_session():
    """Configure the user's session behavior"""
    app = current_app
    session.permanent  = True
    app.permanent_session_lifetime = timedelta(minutes=app.config['SESSION_MINUTES_VALIDITY'])
    session.modified = True

def validate_app_itegrity():
    """Stop the server execution if the configuration file was modified after the
    setup of the application was executed. The configuration file is used on the website
    execution during runtime. Modification on this files can cause unexpected results.
    """
    app = current_app
    config_modification_date = None
    with app.app_context():
        try:
            # Get the application control variables
            w = WebsiteControl()
            conf = w.get_conf()

            WebSiteSettings.set_configuration_location(app, conf.configuration_file)
            setup_exec_date = conf.setup_exec_date

            # Get the last modification date of the configuration file (UTC)
            config_modification_date = os.path.getmtime(WebSiteSettings.get_configuration_location(app))
            config_modification_date = dt.utcfromtimestamp(config_modification_date)
        except Exception as e:
            raise RuntimeError("Application not initialized yet. Plase read the README.md file.")

        # Stop the server execution if the configuration file was modified after the
        # setup of the application was executed.
        if config_modification_date == None or config_modification_date > setup_exec_date:
            app.logger.critical("Configuration file cannot be modified after the website "
                                "setup. Modified on: %s UTC. Setup executed on : %s UTC. "
                                "Please execute >Flask setup< again." 
                                % (config_modification_date.strftime("%m/%d/%Y, %H:%M:%S"), 
                                   setup_exec_date.strftime("%m/%d/%Y, %H:%M:%S"))
            )
            raise RuntimeError("Application unhealthly state. "
                               "Please contact the website administrator.")

def page_not_found(e):
    """Return 404 page"""
    return render_template('404.html', **WebSiteSettings.get_layout_text(current_app)), 404
    
    
def page_unexpected_condition(e):
    """Return 500 page"""
    return render_template('500.html', **WebSiteSettings.get_layout_text(current_app)), 500

# Make the app global available
app = create_app()
    