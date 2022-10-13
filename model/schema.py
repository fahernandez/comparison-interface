from model.connection import db
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
    
    # Available weight configuration
    EQUAL = 'equal' # All items weights during the comparison are the same.
    MANUAL = 'manual'  # The weights of the items were manually assigned by the researcher.

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    weight_configuration = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    display_name = db.Column(db.String(255), nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class Item(db.Model, BaseModel):
    """
    The item model represent each of the object being compared

    Args:
        db (SQLAlchemy): SQLAlchemy connection object

    Returns: none
    """
    __tablename__ = 'item'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    weight = db.Column(db.Float, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    display_name = db.Column(db.String(255), nullable=False)
    image_path = db.Column(db.String(1000), nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class User(db.Model, BaseModel):
    """The User model represent the actual person making the comparisson

    Args:
        db (SQLAlchemy): SQLAlchemy connection object

    Returns: none
    """
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    # Other user files are added automatically by using the Website configuration file
    created_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class Comparison(db.Model, BaseModel):
    """The actual compararisson made between the items by the user.

    Args:
        db (SQLAlchemy): SQLAlchemy connection object

    Returns: none
    """
    __tablename__ = 'comparison'
    # Available comparison states
    COMPARED = 'compared'
    REJUDGE = 'rejudge'
    SKIPPED = 'skipped'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    item_1_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    item_2_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    selected_item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=True)
    # TODO define state as an enum
    state = db.Column(db.String(20), nullable=False)
    created = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class UserItem(db.Model, BaseModel):
    """Items that are recognizable by the user. The comparisson will be made using only this items.

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

class WebsiteControlHistory(db.Model, BaseModel):
    """Control table to know if the application is in a healthly state.

    Args:
        db (SQLAlchemy): SQLAlchemy connection object
    """
    __tablename__ = 'website_control_history'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    setup_exec_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
 