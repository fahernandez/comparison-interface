from flask import Blueprint
from flask.cli import with_appcontext
from flask import current_app
# Custom libraries
from model.setup import Setup as DBSetup
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


@blueprint.cli.command('reset')
@with_appcontext
def reset():
    """Reset the application to an initial state
    """
    app = current_app
    app.logger.info("Getting website configuration")
    s = WebSiteSetup(app)
    conf = s.load()
    
    app.logger.info("Resetting website database")
    s = DBSetup(app)
    s.exec(conf)