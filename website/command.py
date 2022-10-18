import click
from flask import Blueprint
from flask.cli import with_appcontext
from flask import current_app
# Custom libraries
from model.setup import Setup as DBSetup
from model.export import Export
from configuration.website import Setup as WebSiteSetup

blueprint = Blueprint('commands', __name__, cli_group=None)

@blueprint.cli.command('setup')
@with_appcontext
def setup():
    """Call the methods in charge to make the application setup
    """
    app = current_app
    app.logger.info("Getting website configuration")
    s = WebSiteSetup(app)
    conf = s.load()
    
    app.logger.info("Configuring website database")
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
    location = app.config['EXPORT_PATH_LOCATION']
    app.logger.info("Exporting database tables into {}".format(location))
    Export(app).save(location)
