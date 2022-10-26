from sqlalchemy.sql.expression import func
from numpy.random import choice
from sqlalchemy.exc import SQLAlchemyError
import datetime
# Custom import
from view.request import Request
from configuration.website import Settings as WS
from model.connection import db
from model.schema import (Comparison, Item, WebsiteControl, UserGroup,
                          CustomItemPair, UserItem, ItemGroup)


class Rank(Request):
    """Page to rank each of the items being compared."""
    # Available rank actions
    REJUDGE = 'rejudged'
    CONFIRMED = 'confirmed'
    SKIPPED = 'skipped'

    def get(self, request):
        """Request get handler"""
        if not self._valid_session():
            return self._redirect('.user_registration')

        comparison_id = None
        args = request.args.to_dict(flat=True)
        if 'comparison_id' in args:
            comparison_id = args['comparison_id']

        item_1, item_2 = self.__get_items_to_compare(comparison_id)
        # Show a "no content error" in case of not enough selected known items.
        if item_1 is None or item_2 is None:
            return self._render_template('204.html')

        # The user can rejudge comparisons if:
        # 1. Some comparison has been made.
        # 2. There is previous comparison to be made.
        can_rejudge = len(self._session['comparison_ids']) > 0 \
            and self._session['previous_comparison_id'] is not None

        compared, skipped = self.__get_comparison_stats()

        return self._render_template('page/rank.html', {
            'item_1': item_1,
            'item_2': item_2,
            'selected_item_label': WS.get_text(
                WS.RANK_ITEM_SELECTED_INDICATOR_LABEL, self._app),
            'tied_selection_label': WS.get_text(
                WS.RANK_ITEM_TIED_SELECTION_INDICATOR_LABEL, self._app),
            'rejudge_label': WS.get_text(
                WS.RANK_ITEM_REJUDGE_BUTTON_LABEL, self._app),
            'confirmed_label': WS.get_text(
                WS.RANK_ITEM_CONFIRMED_BUTTON_LABEL, self._app),
            'skipped_label': WS.get_text(
                WS.RANK_ITEM_SKIPPED_BUTTON_LABEL, self._app),
            'comparison_instruction_label': WS.get_text(
                WS.RANK_ITEM_INSTRUCTION_LABEL, self._app),
            'comparison_number_label': WS.get_text(
                WS.RANK_ITEM_COMPARISON_EXECUTED_LABEL, self._app),
            'comparison_number': compared,
            'skipped_number_label': WS.get_text(
                WS.RANK_ITEM_SKIPPED_COMPARISON_EXECUTED_LABEL, self._app),
            'skipped_number': skipped,
            'rejudge_value': self.REJUDGE,
            'confirmed_value': self.CONFIRMED,
            'skipped_value': self.SKIPPED,
            'can_rejudge': can_rejudge,
            'comparison_id': comparison_id
        })

    def post(self, request):
        """Request post handler"""
        response = request.form.to_dict(flat=True)
        action = response['state']
        if action != self.REJUDGE:
            # Set the comparison state based on the user's action
            state, selected_item_id = self.__get_comparison_state(action, response)

            # Verify if the user want to rejudge an item
            comparison_id = None
            if 'comparison_id' in response and response['comparison_id'] != "":
                comparison_id = response['comparison_id']

            if comparison_id is None:
                # Save the new user comparison in the database.
                c = Comparison(
                    user_id=self._session['user_id'],
                    item_1_id=response['item_1_id'],
                    item_2_id=response['item_2_id'],
                    state=state,
                    selected_item_id=selected_item_id
                )
                try:
                    db.session.add(c)
                    db.session.commit()
                    # Save the comparison for future possible rejudging
                    self._session['previous_comparison_id'] = c.comparison_id
                    self._session['comparison_ids'] = \
                        self._session['comparison_ids'] + [c.comparison_id]
                except SQLAlchemyError as e:
                    raise RuntimeError(str(e))
            else:
                # Rejudge an existence comparison.
                comparison = db.session.query(Comparison).\
                    where(
                        Comparison.comparison_id == comparison_id,
                        Comparison.user_id == self._session['user_id']).first()

                if comparison is None:
                    raise RuntimeError("Invalid comparison id provided")
                try:
                    comparison.selected_item_id = selected_item_id
                    comparison.state = state
                    comparison.updated = datetime.datetime.now(datetime.timezone.utc)
                    db.session.commit()
                    # Return the pointer to the last comparison made
                    self._session['previous_comparison_id'] = \
                        self._session['comparison_ids'][len(self._session['comparison_ids']) - 1]
                except SQLAlchemyError as e:
                    raise RuntimeError(str(e))

            return self._redirect('.rank')
        else:
            return self._redirect('.rank', comparison_id=self._session['previous_comparison_id'])

    def __get_comparison_state(self, action: str, response: dict):
        """Get the right comparison parameters based on the user's action

        Args:
            action (str): Action triggered by the user
            response (dict): POST from response

        Returns:
            state: Comparison state | None
            selected_item_id: Selected item | None
        """
        state = None
        selected_item_id = None
        if action == self.CONFIRMED and \
           ('selected_item_id' not in response or response['selected_item_id'] == ""):
            state = Comparison.TIED

        if action == self.CONFIRMED and \
           'selected_item_id' in response and response['selected_item_id'] != "":
            state = Comparison.SELECTED
            selected_item_id = response['selected_item_id']

        if action == self.SKIPPED:
            state = Comparison.SKIPPED

        return state, selected_item_id

    def __get_comparison_stats(self):
        """Get summary statistics about the comparison made
        Returns
            compared: Number of comparisons made
            skipped: Number of comparisons skipped
        """
        compared = 0
        skipped = 0
        res = db.session.\
            query(Comparison.state, func.count(Comparison.comparison_id)).\
            where(Comparison.user_id == self._session['user_id']).\
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

    def __get_items_to_compare(self, comparison_id=None):
        """Get the items to compare.

        Args:
            comparison_id (int, optional): Gets the items related
            to a particular comparison. This parameter allows
            the rejudging functionality. Defaults to None.

        Returns:
            Item: Model Item | none
            Item: Model Item | none
        """
        render_item_prefer = WS.should_render(
            WS.BEHAVIOR_RENDER_USER_ITEM_PREFERENCE_PAGE, self._app)

        # Case 1: Returns the items related to a particular comparison.
        if comparison_id is not None:
            return self.__get_comparison_items(comparison_id)

        # Case 2: Get a random pair from list of custom defined weights
        if self._session['weight_conf'] == WebsiteControl.CUSTOM_WEIGHT:
            return self.__get_custom_items()

        # Case 3: Get a random item pair when equal weights and item preference was defined
        if self._session['weight_conf'] == WebsiteControl.EQUAL_WEIGHT and render_item_prefer:
            return self.__get_preferred_items()

        # Case 4: Get a random item pair when equal weights and no item preference was defined
        if self._session['weight_conf'] == WebsiteControl.EQUAL_WEIGHT and not render_item_prefer:
            return self.__get_random_items()

        # All no implemented cases
        return None, None

    def __get_comparison_items(self, comparison_id: int):
        """Get the items related to a particular comparison already made.

        Args:
            comparison_id (int): Comparison id to be rejudged

        Raises:
            RuntimeError: Invalid comparison id provided

        Returns:
            Item: Model Item | none
            Item: Model Item | none
        """
        # 1. Get the items related to the comparison.
        comparison = db.session.query(Comparison).\
            where(
                Comparison.comparison_id == comparison_id,
                Comparison.user_id == self._session['user_id']).first()

        if comparison is None:
            raise RuntimeError("Invalid comparison id provided")

        # 2. Get the items information
        items = db.session.query(Item).\
            where(
                Item.item_id.in_([comparison.item_1_id, comparison.item_2_id])).all()

        # 3. Update the session parameters
        comparison_id_index = self._session['comparison_ids'].index(int(comparison_id))
        if comparison_id_index == 0:
            self._session['previous_comparison_id'] = None
        else:
            self._session['previous_comparison_id'] = \
                self._session['comparison_ids'][comparison_id_index - 1]

        return items[0], items[1]

    def __get_custom_items(self):
        """Get a random pair of items from a predefined list. This
        list was defined by the user when setting up the site.

        Returns:
            Item: Model Item | none
            Item: Model Item | none
        """
        # 1. Get the the custom pairs. This query assumes that just one group
        # can be selected by the user when defining custom weights.
        result = db.session.query(UserGroup, CustomItemPair).\
            join(CustomItemPair, CustomItemPair.group_id == UserGroup.group_id, isouter=True).\
            where(
                UserGroup.user_id == self._session['user_id'],
                UserGroup.group_id.in_(self._session['group_ids'])).all()

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
                Item.item_id.in_([item_1_id, item_2_id])).all()

        return items[0], items[1]

    def __get_preferred_items(self):
        """Get a random pair of items from the preferred user's item selection

        Returns:
            Item: Model Item | none
            Item: Model Item | none
        """
        # 1. Get the know user items preferences
        result = db.session.query(UserItem, Item).\
            join(Item, Item.item_id == UserItem.item_id, isouter=True).\
            where(
                UserItem.user_id == self._session['user_id'],
                UserItem.known == 1).all()

        items_id = []
        items = {}
        for _, i in result:
            # Insert only unique values to guarantee an equal item distribution.
            if i.item_id not in items_id:
                items_id.append(i.item_id)
                items[i.item_id] = i

        if len(items_id) < 2:
            return None, None

        # 2. Select randomly two items from the user's item preferences
        selected_items_id = choice(items_id, 2, replace=False)

        return items[selected_items_id[0]], items[selected_items_id[1]]

    def __get_random_items(self):
        """Get a random pair of items from the website configuration list

        Returns:
            Item: Model Item | none
            Item: Model Item | none
        """
        # 1. Get the items related to the user's group preferences
        result = db.session.query(UserGroup, ItemGroup, Item).\
            join(ItemGroup, ItemGroup.group_id == UserGroup.group_id, isouter=True).\
            join(Item, ItemGroup.item_id == Item.item_id, isouter=True).\
            where(
                UserGroup.user_id == self._session['user_id'],
                UserGroup.group_id.in_(self._session['group_ids']),
                ItemGroup.group_id.in_(self._session['group_ids'])).all()

        items_id = []
        items = {}
        for _, _, i in result:
            # Insert only unique values to guarantee an equal item distribution.
            if i.item_id not in items_id:
                items_id.append(i.item_id)
                items[i.item_id] = i

        if len(items_id) < 2:
            return None, None

        # 2. Select randomly two items using the user's group preferences
        selected_items_id = choice(items_id, 2, replace=False)

        return items[selected_items_id[0]], items[selected_items_id[1]]
