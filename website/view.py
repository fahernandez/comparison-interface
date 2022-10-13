from cProfile import label
from operator import and_
from flask import (Blueprint, redirect, render_template, request, session,
                   url_for, current_app)
from sqlalchemy import MetaData
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql.expression import func
import datetime
from numpy.random import choice

# Custom libraries
from model.connection import db
from model.schema import User, Group, UserItem, Item, Comparison
from configuration.website import Setup as WebSiteSetup

blueprint = Blueprint('views', __name__)

@blueprint.route('/', methods=['GET', 'POST'])
@blueprint.route('/register', methods=['GET', 'POST'])
def register_user():
    """Register the user doing the comparative judgment.

    Raises:
        RuntimeError: When the method was called without GET/POST
        RuntimeError: When there were an error registring the user

    Returns:
        Response: Redirects to the item selection.
    """
    session.clear()
    
    if request.method == 'GET':
        # Load the configuration
        s = WebSiteSetup(current_app)
        conf = s.load()
        
        # Load user fields
        user_fields = conf[WebSiteSetup.WEBSITE_CONFIGURATION][WebSiteSetup.WEBSITE_USER_FIELDS]
        user_components = []
        
        # Load form labels
        labels = conf[WebSiteSetup.WEBSITE_CONFIGURATION][WebSiteSetup.WEBSITE_LABEL]

        # Add the custom user fields
        for field in user_fields:
            component = 'component/{}.html'.format(field[WebSiteSetup.USER_FIELD_TYPE])
            user_components.append(render_template(component, **field))
        
        # Add the group component
        groups = Group.query.all()
        user_components.append(render_template('component/group.html', **{
            'groups':groups,
            'label': labels[WebSiteSetup.LABEL_GROUP_QUESTION]
        }))

        # Render the whole template
        return render_template('page/register.html', **{**{
            'title': labels[WebSiteSetup.LABEL_USER_REGISTER_FORM_TITLE],
            'buttom': labels[WebSiteSetup.LABEL_USER_REGISTER_BUTTOM],
            'components':user_components
        },**__get_layout_labels(labels)})

    if request.method == 'POST':
        # Register the user in the database.
        # Some of the user fields were dynamically added so we are using SQLAlquemy
        # reflection functionality to insert them.
        db_engine = db.get_engine()
        db_meta = MetaData()
        db_meta.reflect(bind=db_engine)
        table = db_meta.tables["user"]
        attr = request.form.to_dict(flat=True)
        attr['created_date'] = datetime.datetime.now(datetime.timezone.utc)
        new_user_sql = table.insert().values(**attr)
        
        try:
            # Insert the user into the database
            result = db.engine.execute(new_user_sql)
            # Get last inserted id
            id = result.lastrowid
            user = db.session.query(User).filter(User.id == id).first()
            # Save reference to the inserted values in the session
            session['user_id'] = user.id
            session['group_id'] = user.group_id
            
            return redirect(url_for('.item_selection'))

        except SQLAlchemyError as e:
            raise RuntimeError(str(e.__dict__['orig']))

    raise RuntimeError("Method not implemented")


@blueprint.route('/selection/items', methods=['GET', 'POST'])
def item_selection():
    """This page allows specify which items are know and unknow 
    for the registered user. Only know items will be shown while doing
    the comparative judgment comparison.

    Returns:
        Response: Redirects to the item selection till al items were
        proccesed. After all items were specify, the method redirects
        to the comparison itself.
    """
    response = __validate_session(session)
    if response:
        return response
    
    if request.method == 'GET':
        # Get all items preferences not specified for the user yet.
        result = db.session.query(User, Item, UserItem).\
            join(Item, User.group_id == Item.group_id, isouter = True).\
            join(
                UserItem,
                (UserItem.user_id == User.id) & (UserItem.item_id == Item.id), 
                isouter = True
            ).\
            where(
                User.id == session['user_id'], 
                User.group_id == session['group_id'],
                UserItem.id == None
            ).order_by(func.random()).\
            first()
    
        # After the user had stated all items preferences
        # moves to the comparison itself.
        if not result:
            return redirect(url_for('.rank'))

        _, item, _ = result
        # Load the configuration
        s = WebSiteSetup(current_app)
        conf = s.load()
        
        # Load form labels
        labels = conf[WebSiteSetup.WEBSITE_CONFIGURATION][WebSiteSetup.WEBSITE_LABEL]
        return render_template('page/item_preference.html', **{**{
            'item':item,
            'item_selection_question': labels[WebSiteSetup.LABEL_ITEM_SELECTION_QUESTION],
            'item_selection_answer_no': labels[WebSiteSetup.LABEL_ITEM_SELECTION_NO],
            'item_selection_answer_yes': labels[WebSiteSetup.LABEL_ITEM_SELECTION_YES]
        },**__get_layout_labels(labels)})
    
    if request.method == 'POST':
        response = request.form.to_dict(flat=True)
        known = False
        if response['action'] == 'agree':
            known = True
        
        # Save the user preference into the database
        ui = UserItem(
            user_id = session['user_id'],
            item_id = response['item_id'],
            known = known
        )

        try:
            db.session.add(ui)
            db.session.commit()
        except SQLAlchemyError as e:
            raise RuntimeError(str(e.__dict__['orig']))


        return redirect(url_for('.item_selection'))
    
    raise RuntimeError("Method not implemented")


@blueprint.route('/rank', methods=['GET', 'POST'])
def rank(comparison_id=None):
    response = __validate_session(session)
    if response:
        return response
    
    # Load the configuration
    s = WebSiteSetup(current_app)
    conf = s.load()
    
    # Load form labels
    labels = conf[WebSiteSetup.WEBSITE_CONFIGURATION][WebSiteSetup.WEBSITE_LABEL]

    if request.method == 'GET' and not 'items' in session:
        # Get all know items for the user
        result = db.session.query(User, Item, UserItem, Group).\
            join(Item, User.group_id == Item.group_id, isouter = True).\
            join(Group, User.group_id == Group.id, isouter = True).\
            join(
                UserItem,
                (UserItem.user_id == User.id) & (UserItem.item_id == Item.id), 
                isouter = True
            ).\
            where(
                User.id == session['user_id'], 
                User.group_id == session['group_id'],
                UserItem.known == 1
            ).all()
        
        # Show a "no content error" in case of not enought selected known items.
        if not result or len(result) == 1:
            return render_template(
                '204.html', **__get_layout_labels(labels)
            )

        items = []
        group  = None
        for _, i, _, g in result:
            items.append(i)
            group = g

        # Calibrate the weights used while selecting the items
        items, ids, weights = __calibrate_weight(items, group)
        
        # Save the items used to make the comparative judgment
        session['items'] = items
        session['items_ids'] = ids
        session['items_weights'] = weights
        session['previous_comparison_id'] = None
        session['actual_comparison_id'] = None
        session['comparison_ids'] = []
    
    # Get the items used to make the comparative judgement
    if request.method == 'GET' and 'items' in session:
        res = choice(
            session['items_ids'],
            2,
            p=session['items_weights'],
            replace=False
        )

        # Load the configuration
        s = WebSiteSetup(current_app)
        conf = s.load()
        
        # The redjudge buttom will be shown if:
        # 1. Some comparison has been made.
        # 2. There is previous comparison to be made.
        render_redjudge_buttom = len(session['comparison_ids']) > 0 \
            and session['actual_comparison_id'] != None

        # Load form labels
        labels = conf[WebSiteSetup.WEBSITE_CONFIGURATION][WebSiteSetup.WEBSITE_LABEL]
        return render_template(
            'page/rank.html', **{**{
            'r1':session['items'][str(res[0])], 
            'r2':session['items'][str(res[1])],
            'selected_item_label': labels[WebSiteSetup.LABEL_ITEM_SELECTED],
            'instruction_label': labels[WebSiteSetup.LABEL_ITEM_INSTRUCTION],
            'rejudge_label': labels[WebSiteSetup.LABEL_ITEM_REJUDGE],
            'compared_label': labels[WebSiteSetup.LABEL_ITEM_COMPARED],
            'skipped_label': labels[WebSiteSetup.LABEL_ITEM_SKIPPED],
            'comparison_intruction_label': labels[WebSiteSetup.LABEL_ITEM_INSTRUCTION],
            'rejudge_value': Comparison.REJUDGE,
            'compared_value': Comparison.COMPARED,
            'skipped_value': Comparison.SKIPPED,
            'render_redjudge': render_redjudge_buttom
            
        },**__get_layout_labels(labels)})
    
    if request.method == 'POST':
        response = request.form.to_dict(flat=True)
        print(response)
        if response['state'] != Comparison.REJUDGE:
            selected_item_id = None
            if 'selected_item_id' in response and response['state'] == Comparison.COMPARED:
                selected_item_id = response['selected_item_id']

            # Save the user preference into the database
            c = Comparison(
                user_id = session['user_id'],
                item_1_id = response['item_1_id'],
                item_2_id = response['item_2_id'],
                state = response['state'],
                selected_item_id = selected_item_id
            )

            try:
                db.session.add(c)
                db.session.commit()
                # Save the comparison. This for future rejudging
                session['previous_comparison_id'] = session['actual_comparison_id']
                session['actual_comparison_id'] = c.id
                session['comparison_ids'] = session['comparison_ids'] + [c.id]
            except SQLAlchemyError as e:
                raise RuntimeError(str(e.__dict__['orig']))
            
            return redirect(url_for('.rank'))
    
        if response['state'] == Comparison.REJUDGE:
            return redirect(url_for('.rank', comparison_id=None))

    raise RuntimeError("Method not implemented")


@blueprint.route('/logout')
def logout():
    print(session.keys())
    session.clear()
    print(session.keys())
    return redirect(url_for('.register_user'))

def __calibrate_weight(items, group):
    """Calibrate items weight based on the user preferences. Weights are defined using
    the website configuration file, but because of the user preferences, this initial
    assigment could be needed to be changed. i.e the weigths assigment could be made taken 
    into consideration n items, but because the user didn't know some of the items, this
    number as reduced to n-m. This means that the initial weights needs to be adjusted to n-m.

    Args:
        items (array): items to be compared
        group (Group): items grouped be used
    """
    items_len = len(items)
    if group.weight_configuration == Group.EQUAL:
        for i in items:
           i.weight = 1/items_len
    
    if group.weight_configuration == Group.MANUAL:
        # Possible cases
        # 1. Just two items: equal weight
        # 2. All items with same weight: equal weight.
        # 3. Some items with biggest weight. recalibrate
        ## TODO-Case 3 not implemented yet. 
        for i in items:
            i.weight = 1/items_len

    # Returns the parameters needed to get the items following the weight assigment
    items.sort(key=lambda x: x.id, reverse=False)
    weights = [i.weight for i in items]
    id = [i.id for i in items]
    items = dict((str(x.id), x.as_dict()) for x in items)

    return items, id, weights

def __validate_session(session):
    """Validate the user session integrity

    Returns:
        Response object: Redirect the user to the user registration secton
    """

    if not "user_id" in session or not "group_id" in session:
        return redirect(url_for('.register_user'))
    return None

def __get_layout_labels(labels):
    """Get the labels used to render the application layout

    Args:
        labels (json):
        app (Flask):

    Returns:
        json: Application labels to be render
    """
    return {
        'logout':labels[WebSiteSetup.LABEL_WEBSITE_LOGOUT],
        'home_label':labels[WebSiteSetup.LABEL_SITE_HOME_LABEL]
    }