import click
from flask import Blueprint
from flask.cli import with_appcontext
from flask import current_app
from sqlalchemy.exc import OperationalError
import os
# Custom libraries
from model.setup import Setup as DBSetup
from model.export import Export
from configuration.website import Setup as WebSiteSetup
from model.schema import WebsiteControl

blueprint = Blueprint('commands', __name__, cli_group=None)

@blueprint.cli.command('setup')
@with_appcontext
def setup():
    """Call the methods in charge to make the application setup. This operation will
    be ignored if the application was already set-up. Run flask reset for a full application
    clean.
    """

    # Get the date when the setup was executed
    app = current_app
    with app.app_context():
        try:
            # Ignore the operation if the set-up was already done
            w = WebsiteControl()
            conf = w.get_conf()
            app.logger.info('Application setup already executed.')
        except OperationalError as oe:
            # Make the application setup
            app = current_app
            app.logger.info("Getting website configuration")
            s = WebSiteSetup(app)
            conf = s.load()
            
            app.logger.info("Configuring website database")
            s = DBSetup(app)
            s.exec(conf)
        except Exception as e:
            # Report any other error
            app.logger.critical(e)
    
@blueprint.cli.command('reset')
@with_appcontext
def setup():
    """WARNING: Reset the application to an initial empty state. It will delete
    database content as well other exported information.
    """
    app = current_app
    app.logger.info("Getting website configuration")
    s = WebSiteSetup(app)
    conf = s.load()
    
    app.logger.info("Reseating website database")
    s = DBSetup(app)
    s.exec(conf)

    
@blueprint.cli.command('export')
@with_appcontext
def export():
    """Export the database into an excel file. Each tab of the file will contain a
    database table. The file will be saved into the location specified by the flask 
    env variable EXPORT_PATH_LOCATION.
    """
    app = current_app
    location = os.path.join(os.path.dirname(__file__), app.config['EXPORT_PATH_LOCATION'])
    app.logger.info("Exporting database tables into {}".format(location))
    Export(app).save(location)
