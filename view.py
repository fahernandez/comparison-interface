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
from configuration.website import Settings as WebSiteSettings

blueprint = Blueprint('views', __name__)

@blueprint.route('/introduction', methods=['GET'])
def introduction():
    """Render the introduction page. This page contains an inframe
    with a link to a google doc with the webpage usage introductions.

    Raises:
        RuntimeError: When the page request methods hasn't been implemented yet.

    Returns:
        Response: Renders the introduction page.
    """
    app = current_app
    if request.method == 'GET':
        # Render the introduction page
        return render_template('page/introduction.html', **{**{
            'user_instruction_link': WebSiteSettings.get_behavior_conf(WebSiteSettings.BEHAVIOUR_USER_INSTRUCTION_LINK, app),
            'introduction_continue_button': WebSiteSettings.get_text(WebSiteSettings.LABEL_INTRODUCTION_CONTINUE_BUTTON_LABEL, app)
        },**WebSiteSettings.get_layout_text(app)})
        
    raise RuntimeError("Method not implemented")

@blueprint.route('/ethics-agreement', methods=['GET'])
def ethics_agreement():
    """Render the ethics agreement page. This page containcts an inframe
    with a link to a google doc with the ethics agreement.

    Raises:
        RuntimeError: When the page request methods hasn't been implemented yet.

    Returns:
        Response: Renders the ethics agreement page.
    """
    app = current_app
    if request.method == 'GET':
        # Render the introduction page
        return render_template('page/ethics.html', **{**{
            'ethics_agreement_link': WebSiteSettings.get_behavior_conf(WebSiteSettings.BEHAVIOUR_ETHICS_AGREEMENT_LINK, app),
            'ethics_agreement_back_button': WebSiteSettings.get_text(WebSiteSettings.LABEL_ETHICS_AGREEMENT_BACK_BUTTON_LABEL, app)
        },**WebSiteSettings.get_layout_text(app)})

    raise RuntimeError("Method not implemented")

@blueprint.route('/', methods=['GET', 'POST'])
@blueprint.route('/register', methods=['GET', 'POST'])
def user_registration():
    """Register the user doing the comparative judgment.

    Raises:
        RuntimeError: When the page request methods hasn't been implemented yet.
        RuntimeError: When there were an error registring the user

    Returns:
        Response: Redirects to the item selection.
    """
    if __valid_session(session):
        return redirect(url_for('.item_selection'))
    
    app = current_app
    if request.method == 'GET':
        # Load user fields
        user_fields = WebSiteSettings.get_user_conf(app)
        user_components = []
        
        # Add the custom user fields
        for field in user_fields:
            component = 'component/{}.html'.format(field[WebSiteSettings.USER_FIELD_TYPE])
            user_components.append(render_template(component, **field))
        
        # Allow multiple item selection only if the item's weight distribution is "equal"
        multiple_selection = False
        if WebsiteControl().get_conf().weight_configuration == WebsiteControl.EQUAL_WEIGHT:
            multiple_selection = True

        # Add the group component
        groups = Group.query.all()
        user_components.append(render_template('component/group.html', **{
            'groups':groups,
            'label': WebSiteSettings.get_text(WebSiteSettings.USER_REGISTRATION_GROUP_QUESTION_LABEL, app),
            'multiple_selection': multiple_selection,
            'group_selection_error': WebSiteSettings.get_text(WebSiteSettings.USER_REGISTRATION_GROUP_SELECTION_ERROR, app)
        }))
        
        # Add the ethics component
        render_ethics = WebSiteSettings.shoud_render(WebSiteSettings.BEHAVIOUR_RENDER_ETHICS_AGREEMENT_PAGE, app)
        if render_ethics:
            user_components.append(render_template('component/ethics.html', **{
                'ethics_agreement_label': WebSiteSettings.get_text(WebSiteSettings.USER_REGISTRATION_ETHICS_AGREEMENT_LABEL, app)
            }))

        # Render the whole template
        return render_template('page/register.html', **{**{
            'title': WebSiteSettings.get_text(WebSiteSettings.USER_REGISTRATION_FORM_TITLE_LABEL, app),
            'button': WebSiteSettings.get_text(WebSiteSettings.USER_REGISTRATION_SUMMIT_BUTTON_LABEL, app),
            'components':user_components
        },**WebSiteSettings.get_layout_text(app)})

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
            user = db.session.query(User).filter(User.user_id == id).first()
            
            # Save the user's group preferences
            for id in group_ids:
                ug = UserGroup()
                ug.group_id = id
                ug.user_id = user.user_id
                
                db.session.add(ug)
                db.session.commit()

            # Save reference to the inserted values in the session
            session['user_id'] = user.user_id
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

    Raises:
        RuntimeError: When the page request methods hasn't been implemented yet.

    Returns:
        Response: Redirects to the item selection till al items were
        proccesed. After all items were specify, the method redirects
        to the comparison itself.
    """
    app = current_app
    if not __valid_session(session):
        return redirect(url_for('.user_registration'))
    
    # The item selection won't be allow if:
    # 1. Manual weights were defined.
    # 2. The user explicitly configured the website to not render this section.
    render_item_preference = WebSiteSettings.shoud_render(WebSiteSettings.BEHAVIOUR_RENDER_USER_ITEM_PREFERENCE_PAGE, app)

    if not session['weight_conf'] == WebsiteControl.EQUAL_WEIGHT or \
        not render_item_preference:
        return redirect(url_for('.rank'))
    
    if request.method == 'GET':
        # Get all items preferences not specified for the user yet.
        result = db.session.query(User, UserGroup, ItemGroup, Item, UserItem).\
            join(UserGroup, UserGroup.user_id == User.user_id, isouter = True).\
            join(ItemGroup, ItemGroup.group_id == UserGroup.group_id, isouter = True).\
            join(Item, ItemGroup.item_id == Item.item_id, isouter = True).\
            join(
                UserItem,
                (UserItem.user_id == User.user_id) & (UserItem.item_id == Item.item_id), 
                isouter = True
            ).\
            where(
                User.user_id == session['user_id'], 
                UserGroup.group_id.in_(session['group_ids']),
                ItemGroup.group_id.in_(session['group_ids']),
                UserItem.user_item_id == None
            ).order_by(func.random()).\
            first()
    
        # After the user had stated all items preferences
        # moves to the comparison itself.
        if not result:
            return redirect(url_for('.rank'))

        _, _ , _, item, _ = result
        return render_template('page/item_preference.html', **{**{
            'item':item,
            'item_selection_question': WebSiteSettings.get_text(WebSiteSettings.ITEM_SELECTION_QUESTION_LABEL, app),
            'item_selection_answer_no': WebSiteSettings.get_text(WebSiteSettings.ITEM_SELECTION_NO_BUTTON_LABEL, app),
            'item_selection_answer_yes': WebSiteSettings.get_text(WebSiteSettings.ITEM_SELECTION_YES_BUTTON_LABEL, app),
        },**WebSiteSettings.get_layout_text(app)})
    
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
    """Page to rank each of the items being compared.

    Raises:
        RuntimeError: When the page request methods hasn't been implemented yet.
        RuntimeError: When there were an error saving the comparison
        RuntimeError: When the provided comparison id is invalid
        RuntimeError: When there were an error updating a comparison.

    Returns:
        Html Content: Render the comparison page.
    """
    # Available rank actions
    REJUDGE = 'rejudged'
    CONFIRMED = 'confirmed'
    SKIPPED = 'skipped'

    app = current_app
    if not __valid_session(session):
        return redirect(url_for('.user_registration'))

    # Get the items used to make the comparative judgement
    if request.method == 'GET':
        comparison_id = None
        args = request.args.to_dict(flat=True)
        if 'comparison_id' in args:
            comparison_id = args['comparison_id']

        item_1, item_2 = __get_items_to_compare(app, comparison_id)
        # Show a "no content error" in case of not enought selected known items.
        if item_1 == None or item_2 == None:
            return render_template(
                '204.html', **WebSiteSettings.get_layout_text(app)
            )
        
        # The user can rejudge comparisons made if:
        # 1. Some comparison has been made.
        # 2. There is previous comparison to be made.
        can_redjudge = len(session['comparison_ids']) > 0 \
            and session['previous_comparison_id'] != None
            
        compared, skipped = __get_comparison_stats(session)

        # Load form labels
        return render_template(
            'page/rank.html', **{**{
            'item_1':item_1, 
            'item_2':item_2,
            'selected_item_label': WebSiteSettings.get_text(WebSiteSettings.RANK_ITEM_SELECTED_INDICATOR_LABEL, app),
            'tied_selection_label': WebSiteSettings.get_text(WebSiteSettings.RANK_ITEM_TIED_SELECTION_INDICATOR_LABEL, app),
            'rejudge_label': WebSiteSettings.get_text(WebSiteSettings.RANK_ITEM_REJUDGE_BUTTON_LABEL, app),
            'confirmed_label': WebSiteSettings.get_text(WebSiteSettings.RANK_ITEM_CONFIRMED_BUTTON_LABEL, app),
            'skipped_label': WebSiteSettings.get_text(WebSiteSettings.RANK_ITEM_SKIPPED_BUTTON_LABEL, app),
            'comparison_intruction_label': WebSiteSettings.get_text(WebSiteSettings.RANK_ITEM_INSTRUCTION_LABEL, app),
            'comparison_number_label': WebSiteSettings.get_text(WebSiteSettings.RANK_ITEM_COMPARISON_EXECUTED_LABEL, app),
            'comparison_number': compared,
            'skipped_number_label': WebSiteSettings.get_text(WebSiteSettings.RANK_ITEM_SKIPPED_COMPARISON_EXECUTED_LABEL, app),
            'skipped_number': skipped,
            'rejudge_value': REJUDGE,
            'confirmed_value': CONFIRMED,
            'skipped_value': SKIPPED,
            'can_redjudge': can_redjudge,
            'comparison_id': comparison_id
            
        },**WebSiteSettings.get_layout_text(app)})
    
    if request.method == 'POST':
        response = request.form.to_dict(flat=True)
        action = response['state']
        if action != REJUDGE:
            # Set the comparison state based on the user's action
            state = None
            selected_item_id = None
            if action == CONFIRMED and (not 'selected_item_id' in response or response['selected_item_id'] == ""):
                state = Comparison.TIED
                
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
                    session['previous_comparison_id'] = c.comparison_id
                    session['comparison_ids'] = session['comparison_ids'] + [c.comparison_id]
                except SQLAlchemyError as e:
                    raise RuntimeError(str(e))
            else:
                # Rejudge an existance comparison.
                comparison = db.session.query(Comparison).\
                    where(
                        Comparison.comparison_id == comparison_id,
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
    """Logout the user from the platform. Clears the session
    and redirects the user to the user registration page.

    Returns:
        _type_: _description_
    """
    session.clear()
    return redirect(url_for('.user_registration'))

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
        query(Comparison.state, func.count(Comparison.comparison_id)).\
        where(Comparison.user_id == session['user_id']).\
        group_by(Comparison.state).all()
    
    if len(res) == 0:
        return compared, skipped
    
    for states in res:
        stateName, number = states
        if stateName == Comparison.SELECTED or stateName == Comparison.TIED:
            compared = compared + number
        if stateName == Comparison.SKIPPED:
            skipped = number

    return compared, skipped


def __get_items_to_compare(app, comparison_id=None):
    """Get the items to compare.

    Args:
        comparison_id (int, optional): Gets the items related
        to a particular comparison. This parameter allows
        the rejudging functionality. Defaults to None.

    Returns:
        Item: Model Item | none
        Item: Model Item | none
    """
    render_item_preference = WebSiteSettings.shoud_render(WebSiteSettings.BEHAVIOUR_RENDER_USER_ITEM_PREFERENCE_PAGE, app)

    # Case 1: Returns the items related to a particular comparison.
    if comparison_id != None:
        # 1. Get the items related to the comparison.
        comparison = db.session.query(Comparison).\
            where(
                Comparison.comparison_id == comparison_id,
                Comparison.user_id == session['user_id']
            ).\
            first()
            
        if comparison == None:
            raise RuntimeError("Invalid comparison id provided")
         
        # 2. Get the items information
        items = db.session.query(Item).\
            where(
                Item.item_id.in_([comparison.item_1_id, comparison.item_2_id])
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
            pairs[p.custom_item_pair_id] = p
            pair_ids.append(p.custom_item_pair_id)
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
                Item.item_id.in_([item_1_id, item_2_id])
            ).all()
            
        return items[0], items[1]
    
    # Case 3: Get a random item pair when equal weights and item preference was defined
    if session['weight_conf'] == WebsiteControl.EQUAL_WEIGHT and render_item_preference:
        # 1. Get the know user items preferences 
        result = db.session.query(UserItem, Item).\
            join(Item, Item.item_id == UserItem.item_id, isouter = True).\
            where(
                UserItem.user_id == session['user_id'],
                UserItem.known == 1
            ).all()
        
        items_id = []
        items = {}
        for _, i in result:
            # Insert only unique values to guarantee an equal item distribution.
            if not i.item_id in items_id:
                items_id.append(i.item_id)
                items[i.item_id] = i

        if len(items_id) < 2:
            return None, None
        
        # 2. Select randomly two items from the user's item preferences
        selected_items_id = choice(items_id, 2, replace=False)
        
        return items[selected_items_id[0]], items[selected_items_id[1]] 
            
    # Case 4: Get a random item pair when equal weights and no item preference was defined
    if session['weight_conf'] == WebsiteControl.EQUAL_WEIGHT and not render_item_preference:
        # 1. Get the items related to the user's group preferences
        result = db.session.query(UserGroup, ItemGroup, Item).\
            join(ItemGroup, ItemGroup.group_id == UserGroup.group_id, isouter = True).\
            join(Item, ItemGroup.item_id == Item.item_id, isouter = True).\
            where(
                UserGroup.user_id == session['user_id'],
                UserGroup.group_id.in_(session['group_ids']),
                ItemGroup.group_id.in_(session['group_ids'])
            ).all()
        
        items_id = []
        items = {}
        for _, _, i in result:
            # Insert only unique values to guarantee an equal item distribution.
            if not i.item_id in items_id:
                items_id.append(i.item_id)
                items[i.item_id] = i
                
        if len(items_id) < 2:
            return None, None
        
        # 2. Select randomly two items using the user's group preferences
        selected_items_id = choice(items_id, 2, replace=False)
        
        return items[selected_items_id[0]], items[selected_items_id[1]]
    
    # All no implemented cases
    return None, None
   


def __valid_session(session):
    """Verify if the user session is valid.

    Returns: True when the user session is valid. False in other case.
    """

    if not "user_id" in session or not "group_ids" in session:
        return False
    return True