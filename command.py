import click
from flask import Blueprint
from flask.cli import with_appcontext
from flask import current_app
from sqlalchemy.exc import OperationalError
# Custom libraries
from model.setup import Setup as DBSetup
from model.export import Export
from configuration.website import Settings as WS
from configuration.validation import Validation as ConfigValidation
from model.schema import WebsiteControl

blueprint = Blueprint('commands', __name__, cli_group=None)


@blueprint.cli.command('setup')
@click.argument("conf")
@with_appcontext
def setup(conf):
    """Call the methods to make the application set-up. This operation will
    be ignored if the application was already set-up. Run flask reset for a full application
    clean.

    Args:
        conf (string): Website configuration location
    """
    # 1. Validate the website configuration
    app = current_app
    app.logger.info("Setting website configuration")
    WS.set_configuration_location(app, conf)
    ConfigValidation(app).validate()

    # 2. Configure database
    with app.app_context():
        try:
            # 2.1 Ignore, if the application was already set-up
            w = WebsiteControl()
            conf = w.get_conf()
            app.logger.info('Application setup already executed.')
        except OperationalError:
            # 2.2 If not, configure the website database.
            app.logger.info("Configuring website database")
            s = DBSetup(app)
            s.exec()
        except Exception as e:
            # 2.3 Report the error in any other case.
            app.logger.critical(e)
            exit()


@blueprint.cli.command('reset')
@click.argument("conf")
@with_appcontext
def reset(conf):
    """WARNING: Reset the application to an initial empty state. It will delete
    database content as well other exported information.

    Args:
        conf (string): Website configuration location
    """
    app = current_app
    # 1. Validate the website configuration
    app.logger.info("Setting website configuration")
    WS.set_configuration_location(app, conf)
    ConfigValidation(app).validate()

    # 2. Configure database
    app.logger.info("Reseating website database")
    s = DBSetup(app)
    s.exec()


@blueprint.cli.command('export')
@with_appcontext
def export():
    """Export the database into an excel file. Each tab of the file will contain a
    database table. The file will be saved into the location specified by the flask
    env variable EXPORT_PATH_LOCATION.
    """
    app = current_app
    location = None
    with app.app_context():
        try:
            # Get the website control variables
            w = WebsiteControl()
            conf = w.get_conf()
            # Set the application configuration
            app.logger.info("Setting website configuration")
            WS.set_configuration_location(app, conf.configuration_file)
            ConfigValidation(app).validate()
            location = WS.get_export_location(app)
        except OperationalError:
            app.logger.critical('Application not initialized yet.')
            exit()
        except Exception as e:
            # Report any other error
            app.logger.critical(e)
            exit()

    app.logger.info("Exporting database tables into {}".format(location))
    Export(app).save(location)
