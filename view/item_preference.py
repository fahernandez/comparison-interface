from view.request import Request
from sqlalchemy.sql.expression import func
from sqlalchemy.exc import SQLAlchemyError
# Custom libraries
from configuration.website import Settings as WS
from model.schema import WebsiteControl, User, UserGroup, ItemGroup, Item, UserItem
from model.connection import db


class ItemsPreference(Request):
    """This page allows specify which items are know and unknow
    for the registered user. Only know items will be shown while doing
    the comparative judgment comparison."""
    def get(self, _):
        """Request get handler"""
        if not self._valid_session():
            return self._redirect('.user_registration')

        # The item selection won't be allow if:
        # 1. Manual weights were defined.
        # 2. The user explicitly configured the website to not render this section.
        render_item_preference = WS.should_render(
            WS.BEHAVIOR_RENDER_USER_ITEM_PREFERENCE_PAGE, self._app)
        equal_weight_conf = self._session['weight_conf'] == WebsiteControl.EQUAL_WEIGHT
        if not equal_weight_conf or not render_item_preference:
            return self._redirect('.rank')

        # Get all items preferences not specified for the user yet.
        result = db.session.query(User, UserGroup, ItemGroup, Item, UserItem).\
            join(UserGroup, UserGroup.user_id == User.user_id, isouter=True).\
            join(ItemGroup, ItemGroup.group_id == UserGroup.group_id, isouter=True).\
            join(Item, ItemGroup.item_id == Item.item_id, isouter=True).\
            join(
                UserItem,
                (UserItem.user_id == User.user_id) & (UserItem.item_id == Item.item_id),
                isouter=True).\
            where(
                User.user_id == self._session['user_id'],
                UserGroup.group_id.in_(self._session['group_ids']),
                ItemGroup.group_id.in_(self._session['group_ids']),
                # WARNING: Don't change the None comparison by "is None". It won't work the same
                UserItem.user_item_id == None).order_by(func.random()).first() # noqa

        # After the user had stated all items preferences
        # moves to the comparison itself.
        if not result:
            return self._redirect('.rank')

        # Render the item preference template
        _, _, _, item, _ = result
        return self._render_template('page/item_preference.html', {
            'item': item,
            'item_selection_question': WS.get_text(WS.ITEM_SELECTION_QUESTION_LABEL, self._app),
            'item_selection_answer_no': WS.get_text(WS.ITEM_SELECTION_NO_BUTTON_LABEL, self._app),
            'item_selection_answer_yes': WS.get_text(WS.ITEM_SELECTION_YES_BUTTON_LABEL, self._app),
        })

    def post(self, request):
        """Request post handler"""
        response = request.form.to_dict(flat=True)

        known = False
        if response['action'] == 'agree':
            known = True

        # Save the user preference into the database
        ui = UserItem(
            user_id=self._session['user_id'],
            item_id=response['item_id'],
            known=known)

        try:
            db.session.add(ui)
            db.session.commit()
        except SQLAlchemyError as e:
            raise RuntimeError(str(e))

        return self._redirect('.item_selection')
