"""Setup the website database"""
from sqlalchemy import Integer, String, MetaData
from migrate.versioning.schema import Table, Column
# Custom libraries
from model.connection import db, persist
from model.schema import Group, Item, WebsiteControl, CustomItemPair, ItemGroup
from configuration.website import Settings as WebSiteSettings
import os

class Setup:
    def __init__(self, app) -> None:
        self.app = app

    def exec(self):
        """Init the website database

        Args:
            app (Flask): Flask application.
        """
        with self.app.app_context():
            db.drop_all()
            db.create_all()
            
            # Remove previous exported database content
            export_location = WebSiteSettings.get_export_location(self.app)
            if os.path.exists(export_location):
                os.remove(export_location)

            # The session needs be commited after creationg the groups.
            self.__setup_group(db)
            self.__setup_website_control_history(db)
            db.session.commit()
            
            # The setup of the user configuration doesn't use SQLAlquemy ORM. The transaction
            # needs to be committed before inserting the user fields values. The user
            # columns values are dynamically defined so a different process needs to be followed.
            self.__setup_user(db)

    def __setup_group(self, db):
        """Save the group configuration in the database.

        Args:
            db (SQLAlquemy): Database connection
        """
        for g in WebSiteSettings.get_comparison_conf(WebSiteSettings.GROUPS, self.app):
            group = Group(
                name=g[WebSiteSettings.GROUP_NAME],
                display_name=g[WebSiteSettings.GROUP_DISPLAY_NAME]
            )
            group = persist(db, group)
            # Setup the items and their weights
            items = self.__setup_item(db, group, g)
            self.__setup_custom_item_pair(db, items, group, g)


    def __setup_custom_item_pair(self, db, items, group, g):
        """Save the custom item's weight configuration went defined manually using
        the Website configuration file. If the web configuration type was "equal",
        this section will be ignored. 

        Args:
            db (SQLAlquemy): Database connection
            items (array(Item)): Group items store in the database.
            group (Group): Group store in the database.
            g (json): Group configuration being saved.
        """
        weight_configuration = WebSiteSettings.get_comparison_conf(WebSiteSettings.GROUP_WEIGHT_CONFIGURATION, self.app)

        # Ignore this section when defining equally weighted items
        if weight_configuration == WebsiteControl.EQUAL_WEIGHT:
            return
        
        # Save the custom weights configuration
        if weight_configuration == WebsiteControl.CUSTOM_WEIGHT:
            weights = g[WebSiteSettings.GROUP_ITEMS_WEIGHT]
        
            items_dict = {}
            for i in items:
                items_dict[i.name] = int(i.item_id)

            for w in weights:
                c = CustomItemPair()
                c.item_1_id = items_dict[w["item_1"]]
                c.item_2_id = items_dict[w["item_2"]]
                c.group_id = group.group_id
                c.weight = w["weight"]
                db.session.add(c)

        return

    def __setup_item(self, db, group, g):
        """Save the item configuration in the database.

        Args:
            db (SQLAlquemy): Database connection
            group (SQLAlquemy): Inserted group object.
            g (Json): Group configuration object on the global website configuration.
        """
        # Insert each of the items related to the groups
        items = []
        for i in g[WebSiteSettings.GROUP_ITEMS]:
            # Verify if the item already exists in the database
            item = db.session.query(Item).\
                where(
                    Item.name == i[WebSiteSettings.ITEM_NAME],
                    Item.display_name == i[WebSiteSettings.ITEM_DISPLAY_NAME],
                    Item.image_path == i[WebSiteSettings.ITEM_IMAGE_NAME]
                ).first()
            # Insert the item in the database if it doesn't exists
            if item == None:
                item = Item(
                    name = i[WebSiteSettings.ITEM_NAME],
                    display_name = i[WebSiteSettings.ITEM_DISPLAY_NAME],
                    image_path = i[WebSiteSettings.ITEM_IMAGE_NAME]
                )
                persist(db, item)
            else:
                self.app.logger.info("Duplicated item {}. Using existing item information.".format(item.name))
            self.__setup_item_group(db, item, group)
                
            items.append(item)
            

        return items
    
    def __setup_item_group(self, db, item, group):
        """Relate the item to the correspondant group in the database

        Args:
            db (SQLAlquemy): Database connection
            item (SQLAlquemy): Inserted item object.
            group (SQLAlquemy): Inserted group object.
        """
        item_id = item.item_id
        group_id = group.group_id
        
        # Verify if the item was already related to the group
        item_group = db.session.query(ItemGroup).\
            where(
                ItemGroup.item_id == item_id,
                ItemGroup.group_id == group_id
            ).first()
        
        # Relate the item to the group if the relationship hasn't been created yet.
        if item_group == None:
            item_group = ItemGroup(
                item_id = item_id,
                group_id = group_id
            )
            persist(db, item_group)
        else:
            self.app.logger.info("Item {} is already related to group {}. Using existing information".\
                format(
                    item.name,
                    group.name
                ))     

    def __setup_user(self, db):
        """Save the user configuration in the database. User fields are dynamically configured
        using the website configuration file.

        Args:
            db (SQLAlquemy): Database connection
        """
        user_conf = WebSiteSettings.get_user_conf(self.app)
        
        # Gets a connection to the database
        db_engine = db.get_engine()
        db_meta = MetaData(bind=db_engine)
        table = Table('user' , db_meta)

        # Create each of the new user columns
        for f in user_conf:
            name = f[WebSiteSettings.USER_FIELD_NAME]
            required = bool(f[WebSiteSettings.USER_FIELD_REQUIRED])
            type = f[WebSiteSettings.USER_FIELD_TYPE]
            max_size = None
            col = None
            if type == WebSiteSettings.USER_FIELD_TYPE_TEXT or type == WebSiteSettings.USER_FIELD_TYPE_EMAIL:
                max_size = f[WebSiteSettings.USER_FIELD_MAX_LIMIT]
                col = Column(name, String(max_size), nullable=required)
            if type == WebSiteSettings.USER_FIELD_TYPE_DROPDOWN or type == WebSiteSettings.USER_FIELD_TYPE_RADIO:
                max_size = max([len(x) for x in f[WebSiteSettings.USER_FIELD_SELECT_OPTION]])
                col = Column(name, String(max_size), nullable=required)
            if type == WebSiteSettings.USER_FIELD_TYPE_INT:
                col = Column(name, Integer, nullable=required)
            
            # Insert the new column
            col.create(table)
        
        # Add a field to specify if the user accepted the ethics aggrement 
        # if this section was configured to be render
        render_ethics = WebSiteSettings.shoud_render(WebSiteSettings.BEHAVIOUR_RENDER_ETHICS_AGREEMENT_PAGE, self.app)
        if render_ethics:
            col = Column('accepted_ethics_agreement', Integer, nullable=required)      
            col.create(table)
            
    def __setup_website_control_history(self, db):
        """The control history helps to keep control of changes on the Website configuration.
        After the project has been set up, it's not allowed changing the website configuration file.
        Changes on this file will block the website execution.
        A new setup will be neccesary and the database information will be reset.

        Args:
            db (SQLAlquemy): Database connection,
        """
        hist = WebsiteControl()
        hist.weight_configuration = WebSiteSettings.get_comparison_conf(WebSiteSettings.GROUP_WEIGHT_CONFIGURATION, self.app)
        hist.configuration_file = self.app.config[WebSiteSettings.CONFIGURATION_LOCATION]
        db.session.add(hist)