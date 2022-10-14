"""Initial website script. This function are called after command
export FLASK_APP=website
flask run
"""
import os
from flask import Flask, render_template
from flask import current_app
from datetime import datetime as dt
# Custom libraries
from configuration.flask import Settings
from configuration.website import Setup as WebSiteSetup
from model.connection import db
from model.schema import WebsiteControl
from website import command, view

def create_app(test_config=None):
    """Start Flask website application

    Args:
        config_filename (object, optional): Default configuration file. 
        Defaults to None.
    """
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    if test_config is None:
        app.config.from_object(Settings)
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
    app.before_request(validate_app_itegrity)
    
    # Register page errors
    app.register_error_handler(404, page_not_found)
    app.register_error_handler(500, page_unexpected_condition)

    return app

def validate_app_itegrity():
    """Stop the server execution if the configuration file was modified after the
    setup of the application was executed. The configuration file is used on the website
    execution during runtime. Modification on this files can cause unexpected results.
    """
    app = current_app
    with app.app_context():
        # Get the date when the setup was executed
        w = WebsiteControl()
        conf = w.get_conf()
        setup_exec_date = conf.setup_exec_date
        config_modification_date = None

        try:
            # Get the last modification date of the configuration file (UTC)
            config_modification_date = os.path.getmtime(Settings.WEBSITE_SETUP_LOCATION)
            config_modification_date = dt.utcfromtimestamp(config_modification_date)
        except Exception as e:
            app.logger.critical(e)
            exit()
        
        # Stop the server execution if the configuration file was modified after the
        # setup of the application was executed.
        if config_modification_date > setup_exec_date:
            app.logger.critical("Configuration file cannot be modified after the website "
                                "setup. Modified on: %s UTC. Setup executed on : %s UTC. "
                                "Please execute >Flask setup< again." 
                                % (config_modification_date.strftime("%m/%d/%Y, %H:%M:%S"), 
                                   setup_exec_date.strftime("%m/%d/%Y, %H:%M:%S"))
            )
            raise RuntimeError("Application unhealthly state. "
                               "Please contact the website administrator.")

def page_not_found(e):
    
    # Load the configuration
    s = WebSiteSetup(current_app)
    conf = s.load()
    
    # Load form labels
    labels = conf[WebSiteSetup.WEBSITE_CONFIGURATION][WebSiteSetup.WEBSITE_LABEL]

    # note that we set the 404 status explicitly
    return render_template('404.html', **{
        'logout':labels[WebSiteSetup.LABEL_WEBSITE_LOGOUT]
    }), 404
    
    
def page_unexpected_condition(e):
    # Load the configuration
    s = WebSiteSetup(current_app)
    conf = s.load()
    
    # Load form labels
    labels = conf[WebSiteSetup.WEBSITE_CONFIGURATION][WebSiteSetup.WEBSITE_LABEL]

    # note that we set the 404 status explicitly
    return render_template('500.html', **{
        'logout':labels[WebSiteSetup.LABEL_WEBSITE_LOGOUT]
    }), 500