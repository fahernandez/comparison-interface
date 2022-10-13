"""Initialize Flask website database"""
from sqlalchemy import Integer, String, MetaData
from migrate.versioning.schema import Table, Column
# Custom libraries
from model.connection import db, persist
from model.schema import Group, Item, WebsiteControlHistory, User
from configuration.website import Setup as WebSiteSetup

class Setup:
    def __init__(self, app) -> None:
        self.app = app

    def exec(self, config):
        """Init the website database

        Args:
            app (Flask): Flask application.
            config (Json): Website configuration object.
        """
        with self.app.app_context():
            db.drop_all()
            db.create_all()

            # The session needs be commited after creationg the groups.
            self.__setup_group(db, config)
            db.session.commit()
            
            # The setup of the user configuration doesn't use SQLAlquemy ORM
            self.__setup_user(db, config)

    def __setup_group(self, db, config):
        """Save the group configuration in the database.

        Args:
            db (SQLAlquemy): Database connection
            config (Json): Website configuration object.
        """
        for g in config[WebSiteSetup.COMPARISON_CONFIGURATION][WebSiteSetup.GROUPS]:
            group = Group(
                weight_configuration=g[WebSiteSetup.GROUP_WEIGHT_CONFIGURATION], 
                name=g[WebSiteSetup.GROUP_NAME],
                display_name=g[WebSiteSetup.GROUP_DISPLAY_NAME]
            )
            group = persist(db, group)
            self.__setup_item(db, group, g)

        self.__setup_website_control_history(db)

    def __setup_item(self, db, group, g):
        """Save the item configuration in the database.

        Args:
            db (SQLAlquemy): Database connection
            group (SQLAlquemy): Inserted group object.
            g (Json): Group configuration object on the global website configuration.
        """
        item_weight = None

        if g[WebSiteSetup.GROUP_WEIGHT_CONFIGURATION] == Group.EQUAL:
            item_weight = 1/len(g[WebSiteSetup.GROUP_ITEMS])

        # Insert each of the items related to the groups
        for i in g[WebSiteSetup.GROUP_ITEMS]: 
            if g[WebSiteSetup.GROUP_WEIGHT_CONFIGURATION] == Group.MANUAL:
                item_weight = i[WebSiteSetup.ITEM_WEIGHT]
                
            item = Item(
                group_id=group.id,
                weight=item_weight,
                name=i[WebSiteSetup.ITEM_NAME],
                display_name=i[WebSiteSetup.ITEM_DISPLAY_NAME],
                image_path=i[WebSiteSetup.ITEM_IMAGE_NAME]
            )
            
            item = persist(db, item)
            
    def __setup_user(self, db, config):
        """Save the user configuration in the database. User fields are dynamically configured
        using the website configuration file.

        Args:
            db (SQLAlquemy): Database connection
            config (Json): Website configuration object.
        """
        user_conf = config[WebSiteSetup.WEBSITE_CONFIGURATION][WebSiteSetup.WEBSITE_USER_FIELDS]
        
        # Gets a connection to the database
        db_engine = db.get_engine()
        db_meta = MetaData(bind=db_engine)
        table = Table('user' , db_meta)

        # Create each of the new user columns
        for f in user_conf:
            name = f[WebSiteSetup.USER_FIELD_NAME]
            required = bool(f[WebSiteSetup.USER_FIELD_REQUIRED])
            type = f[WebSiteSetup.USER_FIELD_TYPE]
            max_size = None
            col = None
            if type == WebSiteSetup.USER_FIELD_TYPE_TEXT or type == WebSiteSetup.USER_FIELD_TYPE_EMAIL:
                max_size = f[WebSiteSetup.USER_FIELD_MAX_LIMIT]
                col = Column(name, String(max_size), nullable=required)
            if type == WebSiteSetup.USER_FIELD_TYPE_DROPDOWN or type == WebSiteSetup.USER_FIELD_TYPE_RADIO:
                max_size = max([len(x) for x in f[WebSiteSetup.USER_FIELD_SELECT_OPTION]])
                col = Column(name, String(max_size), nullable=required)
            if type == WebSiteSetup.USER_FIELD_TYPE_INT:
                col = Column(name, Integer, nullable=required)
            
            # Insert the new column
            col.create(table)
            
    def __setup_website_control_history(self, db):
        """The control history helps to keep control of changes on the Website configuration.
        After the project has been set up, it's not allowed changing the website configuration file.
        Changes on this file will block the website execution.
        A new setup will be neccesary and the database information will be reset.

        Args:
            db (SQLAlquemy): Database connection
        """
        hist = WebsiteControlHistory()
        db.session.add(hist)