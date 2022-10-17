from model.connection import db
from sqlalchemy.schema import UniqueConstraint
import datetime

class BaseModel():
    def as_dict(self):
       return {c.name: str(getattr(self, c.name)) for c in self.__table__.columns}

    def __repr__(self):
        return self.as_dict()
    
class Group(db.Model, BaseModel):
    """ Entity clustering the items being compared. Some items
    cluster naturally. This table allows specify this items clustering.

    Args:
        db (SQLAlchemy): SQLAlchemy connection object
    """
    __tablename__ = 'group'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    display_name = db.Column(db.String(255), nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    __table_args__ = (
        UniqueConstraint(
            'name',
            name='_group_name_uidx'
        ),
    )

class Item(db.Model, BaseModel):
    """
    The item model represent each of the object being compared

    Args:
        db (SQLAlchemy): SQLAlchemy connection object

    Returns: none
    """
    __tablename__ = 'item'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    display_name = db.Column(db.String(255), nullable=False)
    image_path = db.Column(db.String(1000), nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    __table_args__ = (UniqueConstraint(
        'name',
        'display_name',
        'image_path', 
        name='_item_name_display_name_image_path_uidx'),
    )
    
class ItemGroup(db.Model, BaseModel):
    """
    The item model represent each of the object being compared

    Args:
        db (SQLAlchemy): SQLAlchemy connection object

    Returns: none
    """
    __tablename__ = 'item_group'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    item_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint(
            'item_id',
            'group_id',
            name='_item_group_uidx'
        ),
    )

class User(db.Model, BaseModel):
    """Represents the actual person making the comparisson

    Args:
        db (SQLAlchemy): SQLAlchemy connection object

    Returns: none
    """
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # Other user files are added automatically by using the Website configuration file
    created_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
class UserGroup(db.Model, BaseModel):
    """Holds the group prefences of the user. 

    Args:
        db (SQLAlchemy): SQLAlchemy connection object

    Returns: none
    """
    __tablename__ = 'user_group'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint(
            'group_id',
            'user_id',
            name='_user_group_uidx'
        ),
    )

class Comparison(db.Model, BaseModel):
    """The actual compararisson made between the items by the user.

    Args:
        db (SQLAlchemy): SQLAlchemy connection object

    Returns: none
    """
    __tablename__ = 'comparison'
    # Available comparison states
    SELECTED = 'selected'
    SKIPPED = 'skipped'
    TIGHT = 'tight'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    item_1_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    item_2_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    selected_item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=True)
    # TODO define state as an enum
    state = db.Column(db.String(20), nullable=False)
    created = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class CustomItemPair(db.Model, BaseModel):
    """Holds pair of items with custom weight configuration. If this
    table is empty, a random item selection will be made using the user's group preferences.
    This table is populated just when the items group weight configuration is set on manual

    Args:
        db (SQLAlchemy): SQLAlchemy connection object

    Returns: none
    """
    __tablename__ = 'custom_item_pair'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    item_1_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    item_2_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    weight = db.Column(db.Float, nullable=False)
    created = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint(
            'group_id',
            'item_1_id',
            'item_2_id',
            name='_custom_item_pair_uidx'
        ),
    )


class UserItem(db.Model, BaseModel):
    """Items that are recognizable by the user. 
    The comparison will be made using only these items (if selected).

    Args:
        db (SQLAlchemy): SQLAlchemy connection object

    Returns: none
    """
    __tablename__ = 'user_item'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    known = db.Column(db.Boolean, nullable=False) # 0 for unknow. 1 for know.
    date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    __table_args__ = (
        UniqueConstraint(
            'user_id',
            'item_id',
            name='_user_item_uidx'
        ),
    )


class WebsiteControl(db.Model, BaseModel):
    """Control table to know if the application is in a healthly state.

    Args:
        db (SQLAlchemy): SQLAlchemy connection object
    """
    __tablename__ = 'website_control'
    
    # Available weight configuration
    EQUAL_WEIGHT = 'equal' # All items weights during the comparison are the same.
    CUSTOM_WEIGHT = 'manual'  # The weights of the items were manually assigned by the researcher.

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    weight_configuration = db.Column(db.String(20), nullable=False)
    setup_exec_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    def get_conf(self):
        """Get the website control configuration

        Returns:
            WebsiteControl: Website Control configuration model object
        """
        return self.query.order_by(WebsiteControl.id.desc()).first()
    
    def equal_weight_configuration(self):
        c = self.get_conf()
        return c.weight_configuration == self.EQUAL_WEIGHT

 