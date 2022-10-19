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
from model.schema import (User, Group, UserItem, Item, Comparison, WebsiteControl, 
    UserGroup, CustomItemPair, ItemGroup)
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
        
        # Allow multiple item selection only the weight distribution is "equal"
        multiple_selection = False
        if WebsiteControl().get_conf().weight_configuration == WebsiteControl.EQUAL_WEIGHT:
            multiple_selection = True

        # Add the group component
        groups = Group.query.all()
        user_components.append(render_template('component/group.html', **{
            'groups':groups,
            'label': labels[WebSiteSetup.LABEL_GROUP_QUESTION],
            'multiple_selection': multiple_selection
        }))

        # Render the whole template
        return render_template('page/register.html', **{**{
            'title': labels[WebSiteSetup.LABEL_USER_REGISTER_FORM_TITLE],
            'buttom': labels[WebSiteSetup.LABEL_USER_REGISTER_BUTTON],
            'components':user_components
        },**__get_layout_labels(labels)})

    if request.method == 'POST':
        # Remove the group id from the request.
        # This field is not related to the user model
        dic_user_attr = request.form.to_dict(flat=True)
        dic_user_attr.pop('group_ids', None)

        # Multiple group ids can be selected by the user
        group_ids = request.form.to_dict(flat=False)['group_ids']

        # Register the user in the database.
        # Some of the user fields were dynamically added so we are using SQLAlquemy
        # reflection functionality to insert them.
        db_engine = db.get_engine()
        db_meta = MetaData()
        db_meta.reflect(bind=db_engine)
        table = db_meta.tables["user"]
        dic_user_attr['created_date'] = datetime.datetime.now(datetime.timezone.utc)
        new_user_sql = table.insert().values(**dic_user_attr)
        try:
            # Insert the user into the database
            result = db.engine.execute(new_user_sql)
            # Get last inserted id
            id = result.lastrowid
            user = db.session.query(User).filter(User.id == id).first()
            
            # Save the user's group preferences
            for id in group_ids:
                ug = UserGroup()
                ug.group_id = id
                ug.user_id = user.id
                
                db.session.add(ug)
                db.session.commit()

            # Save reference to the inserted values in the session
            session['user_id'] = user.id
            session['group_ids'] = group_ids
            session['weight_conf'] = WebsiteControl().get_conf().weight_configuration
            session['previous_comparison_id'] = None
            session['comparison_ids'] = []
        
            return redirect(url_for('.item_selection'))

        except SQLAlchemyError as e:
            raise RuntimeError(str(e))

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
    
    # The item selection won't be allow if:
    # 1. Manual weights were defined.
    # 2. The user explicitly configured the website to not render this section.
    if not session['weight_conf'] == WebsiteControl.EQUAL_WEIGHT or \
        not current_app.config['RENDER_USER_ITEM_PREFERENCE']:
        return redirect(url_for('.rank'))
    
    if request.method == 'GET':
        # Get all items preferences not specified for the user yet.
        result = db.session.query(User, UserGroup, ItemGroup, Item, UserItem).\
            join(UserGroup, UserGroup.user_id == User.id, isouter = True).\
            join(ItemGroup, ItemGroup.group_id == UserGroup.group_id, isouter = True).\
            join(Item, ItemGroup.item_id == Item.id, isouter = True).\
            join(
                UserItem,
                (UserItem.user_id == User.id) & (UserItem.item_id == Item.id), 
                isouter = True
            ).\
            where(
                User.id == session['user_id'], 
                UserGroup.group_id.in_(session['group_ids']),
                ItemGroup.group_id.in_(session['group_ids']),
                UserItem.id == None
            ).order_by(func.random()).\
            first()
    
        # After the user had stated all items preferences
        # moves to the comparison itself.
        if not result:
            return redirect(url_for('.rank'))

        _, _ , _, item, _ = result
        # Load the configuration
        s = WebSiteSetup(current_app)
        conf = s.load()
        
        # Load form labels
        labels = conf[WebSiteSetup.WEBSITE_CONFIGURATION][WebSiteSetup.WEBSITE_LABEL]
        return render_template('page/item_preference.html', **{**{
            'item':item,
            'item_selection_question': labels[WebSiteSetup.LABEL_ITEM_SELECTION_QUESTION],
            'item_selection_answer_no': labels[WebSiteSetup.LABEL_ITEM_SELECTION_NO_BUTTON],
            'item_selection_answer_yes': labels[WebSiteSetup.LABEL_ITEM_SELECTION_YES_BUTTON]
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
            raise RuntimeError(str(e))


        return redirect(url_for('.item_selection'))
    
    raise RuntimeError("Method not implemented")


@blueprint.route('/rank', methods=['GET', 'POST'])
def rank():
    # Available rank actions
    REJUDGE = 'rejudged'
    CONFIRMED = 'confirmed'
    SKIPPED = 'skipped'

    response = __validate_session(session)
    if response:
        return response
    
    # Load the configuration
    s = WebSiteSetup(current_app)
    conf = s.load()
    
    # Load form labels
    labels = conf[WebSiteSetup.WEBSITE_CONFIGURATION][WebSiteSetup.WEBSITE_LABEL]

    # Get the items used to make the comparative judgement
    if request.method == 'GET':
        comparison_id = None
        args = request.args.to_dict(flat=True)
        if 'comparison_id' in args:
            comparison_id = args['comparison_id']

        item_1, item_2 = __get_items_to_compare(comparison_id)
        # Show a "no content error" in case of not enought selected known items.
        if item_1 == None or item_2 == None:
            return render_template(
                '204.html', **__get_layout_labels(labels)
            )

        # Load the configuration
        s = WebSiteSetup(current_app)
        conf = s.load()
        
        # The user can rejudge comparisons made if:
        # 1. Some comparison has been made.
        # 2. There is previous comparison to be made.
        can_redjudge = len(session['comparison_ids']) > 0 \
            and session['previous_comparison_id'] != None
            
        compared, skipped = __get_comparison_stats(session)

        # Load form labels
        labels = conf[WebSiteSetup.WEBSITE_CONFIGURATION][WebSiteSetup.WEBSITE_LABEL]
        return render_template(
            'page/rank.html', **{**{
            'item_1':item_1, 
            'item_2':item_2,
            'selected_item_label': labels[WebSiteSetup.LABEL_ITEM_SELECTED_LABEL],
            'tight_selection_label': labels[WebSiteSetup.LABEL_TIGHT_SELECTION_LABEL],
            'instruction_label': labels[WebSiteSetup.LABEL_ITEM_INSTRUCTION],
            'rejudge_label': labels[WebSiteSetup.LABEL_ITEM_REJUDGE_BUTTON],
            'confirmed_label': labels[WebSiteSetup.LABEL_ITEM_CONFIRMED_BUTTON],
            'skipped_label': labels[WebSiteSetup.LABEL_ITEM_SKIPPED_BUTTON],
            'comparison_intruction_label': labels[WebSiteSetup.LABEL_ITEM_INSTRUCTION],
            'comparison_number_label': labels[WebSiteSetup.LABEL_COMPARISON_NUMBER],
            'comparison_number': compared,
            'skipped_number_label': labels[WebSiteSetup.LABEL_SKIPPED_NUMBER],
            'skipped_number': skipped,
            'rejudge_value': REJUDGE,
            'confirmed_value': CONFIRMED,
            'skipped_value': SKIPPED,
            'can_redjudge': can_redjudge,
            'comparison_id': comparison_id
            
        },**__get_layout_labels(labels)})
    
    if request.method == 'POST':
        response = request.form.to_dict(flat=True)
        action = response['state']
        if action != REJUDGE:
            # Set the comparison state based on the user's action
            state = None
            selected_item_id = None
            if action == CONFIRMED and (not 'selected_item_id' in response or response['selected_item_id'] == ""):
                state = Comparison.TIGHT
                
            if action == CONFIRMED and 'selected_item_id' in response and response['selected_item_id'] != "":
                state = Comparison.SELECTED
                selected_item_id = response['selected_item_id']
    
            if action == SKIPPED:
                state = Comparison.SKIPPED
                
            # Verify if the user want to rejudge an item
            comparison_id = None
            if 'comparison_id' in response and response['comparison_id'] != "":
                comparison_id = response['comparison_id']
                
            if comparison_id == None:
                # Save the new user comparison in the database.
                c = Comparison(
                    user_id = session['user_id'],
                    item_1_id = response['item_1_id'],
                    item_2_id = response['item_2_id'],
                    state = state,
                    selected_item_id = selected_item_id
                )
                try:
                    db.session.add(c)
                    db.session.commit()
                    # Save the comparison for future possible rejudging
                    session['previous_comparison_id'] = c.id
                    session['comparison_ids'] = session['comparison_ids'] + [c.id]
                except SQLAlchemyError as e:
                    raise RuntimeError(str(e))
            else:
                # Rejudge an existance comparison.
                comparison = db.session.query(Comparison).\
                    where(
                        Comparison.id == comparison_id,
                        Comparison.user_id == session['user_id']
                    ).\
                    first()

                if comparison == None:
                    raise RuntimeError("Invalid comparison id provided")
                
                try:
                    comparison.selected_item_id = selected_item_id
                    comparison.state = state
                    comparison.updated = datetime.datetime.now(datetime.timezone.utc)
                    db.session.commit()
                    # Return the pointer to the last comparasion made
                    session['previous_comparison_id'] = session['comparison_ids'][len(session['comparison_ids'])-1]
                except SQLAlchemyError as e:
                    raise RuntimeError(str(e))
        
            return redirect(url_for('.rank'))
    
        if action == REJUDGE:
            return redirect(url_for('.rank', comparison_id=session['previous_comparison_id']))

    raise RuntimeError("Method not implemented")


@blueprint.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('.register_user'))

def __get_comparison_stats(session):
    """Get summary statistics about the comparison made
    Args:
        session (dict): User session.
    Returns
        compared: Number of comparisons made
        skipped: Number of comparisons skipped 
    """
    compared = 0
    skipped = 0
    res = db.session.\
        query(Comparison.state, func.count(Comparison.id)).\
        where(Comparison.user_id == session['user_id']).\
        group_by(Comparison.state).all()
    
    if len(res) == 0:
        return compared, skipped
    
    for states in res:
        stateName, number = states
        if stateName == Comparison.SELECTED or stateName == Comparison.TIGHT:
            compared = compared + number
        if stateName == Comparison.SKIPPED:
            skipped = number

    return compared, skipped


def __get_items_to_compare(comparison_id=None):
    """Get the items to compare.

    Args:
        comparison_id (int, optional): Gets the items related
        to a particular comparison. This parameter allows
        the rejudging functionality. Defaults to None.

    Returns:
        Item: Model Item | none
        Item: Model Item | none
    """
    # Case 1: Returns the items related to a particular comparison.
    if comparison_id != None:
        # 1. Get the items related to the comparison.
        comparison = db.session.query(Comparison).\
            where(
                Comparison.id == comparison_id,
                Comparison.user_id == session['user_id']
            ).\
            first()
            
        if comparison == None:
            raise RuntimeError("Invalid comparison id provided")
         
        # 2. Get the items information
        items = db.session.query(Item).\
            where(
                Item.id.in_([comparison.item_1_id, comparison.item_2_id])
            ).all()
        
        # 3. Update the session parameters
        comparison_id_index = session['comparison_ids'].index(int(comparison_id))
        if comparison_id_index == 0:
            session['previous_comparison_id'] = None
        else:
            session['previous_comparison_id'] = session['comparison_ids'][comparison_id_index - 1]
        
        return items[0], items[1]

    # Case 2: Get a random pair from list of custom defined weights
    if session['weight_conf'] == WebsiteControl.CUSTOM_WEIGHT:
        # 1. Get the the custom pairs. This query assumes that just one group
        # can be selected by the user when defining custom weights.
        result = db.session.query(UserGroup, CustomItemPair).\
            join(CustomItemPair, CustomItemPair.group_id == UserGroup.group_id, isouter = True).\
            where(
                UserGroup.user_id == session['user_id'], 
                UserGroup.group_id.in_(session['group_ids'])
            ).all()

        pair_ids = []
        pair_weights = []
        pairs = {}
        for _, p in result:
            pairs[p.id] = p
            pair_ids.append(p.id)
            pair_weights.append(p.weight)
        
        if len(pair_ids) == 0:
            return None, None
        
        # 2. Select the item pair to compare but respecting the custom weights
        pair_id = choice(pair_ids, 1, p=pair_weights, replace=False)
        item_1_id = pairs[pair_id[0]].item_1_id
        item_2_id = pairs[pair_id[0]].item_2_id

        # 3. Get the items information
        items = db.session.query(Item).\
            where(
                Item.id.in_([item_1_id, item_2_id])
            ).all()
            
        return items[0], items[1]
    
    # Case 3: Get a random item pair when equal weights and item preference was defined
    if session['weight_conf'] == WebsiteControl.EQUAL_WEIGHT and \
        current_app.config['RENDER_USER_ITEM_PREFERENCE']:
        # 1. Get the know user items preferences 
        result = db.session.query(UserItem, Item).\
            join(Item, Item.id == UserItem.item_id, isouter = True).\
            where(
                UserGroup.user_id == session['user_id'],
                UserItem.known == 1
            ).all()
        
        items_id = []
        items = {}
        for _, i in result:
            # Insert only unique values to guarantee an equal item distribution.
            if not i.id in items_id:
                items_id.append(i.id)
                items[i.id] = i

        if len(items_id) < 2:
            return None, None
        
        # 2. Select randomly two items from the user's item preferences
        selected_items_id = choice(items_id, 2, replace=False)
        
        return items[selected_items_id[0]], items[selected_items_id[1]] 
            
    # Case 4: Get a random item pair when equal weights and no item preference was defined
    if session['weight_conf'] == WebsiteControl.EQUAL_WEIGHT and \
        not current_app.config['RENDER_USER_ITEM_PREFERENCE']:
        # 1. Get the items related to the user's group preferences
        result = db.session.query(UserGroup, ItemGroup, Item).\
            join(ItemGroup, ItemGroup.group_id == UserGroup.group_id, isouter = True).\
            join(Item, ItemGroup.item_id == Item.id, isouter = True).\
            where(
                UserGroup.user_id == session['user_id'],
                UserGroup.group_id.in_(session['group_ids']),
                ItemGroup.group_id.in_(session['group_ids'])
            ).all()
        
        items_id = []
        items = {}
        for _, _, i in result:
            # Insert only unique values to guarantee an equal item distribution.
            if not i.id in items_id:
                items_id.append(i.id)
                items[i.id] = i
                
        if len(items_id) < 2:
            return None, None
        
        # 2. Select randomly two items using the user's group preferences
        selected_items_id = choice(items_id, 2, replace=False)
        
        return items[selected_items_id[0]], items[selected_items_id[1]]
    
    # All no implemented cases
    return None, None
   


def __validate_session(session):
    """Validate the user session integrity

    Returns:
        Response object: Redirect the user to the user registration secton
    """

    if not "user_id" in session or not "group_ids" in session:
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