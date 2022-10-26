from flask import render_template
from sqlalchemy import MetaData
import datetime
from sqlalchemy.exc import SQLAlchemyError

# Custom libraries
from view.request import Request
from configuration.website import Settings as WS
from model.schema import Group, WebsiteControl, User, UserGroup
from model.connection import db


class Register(Request):
    """Register the user doing the comparative judgment."""

    def get(self, _):
        """Request get handler"""
        if self._valid_session():
            return self._redirect('.item_selection')

        # Load components
        user_components = []
        self.__load_user_component(user_components)
        self.__load_group_component(user_components)
        self.__load_ethics_component(user_components)

        # Render components
        return self._render_template('page/register.html', {
            'title': WS.get_text(WS.USER_REGISTRATION_FORM_TITLE_LABEL, self._app),
            'button': WS.get_text(WS.USER_REGISTRATION_SUMMIT_BUTTON_LABEL, self._app),
            'components': user_components
        })

    def post(self, request):
        """Request post handler"""
        # Remove the group id from the request.
        # This field is not related to the user model
        dic_user_attr = request.form.to_dict(flat=True)
        dic_user_attr.pop('group_ids', None)

        # Get all groups id selected by the user
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
            self._session['user_id'] = user.user_id
            self._session['group_ids'] = group_ids
            self._session['weight_conf'] = WebsiteControl().get_conf().weight_configuration
            self._session['previous_comparison_id'] = None
            self._session['comparison_ids'] = []
        except SQLAlchemyError as e:
            raise RuntimeError(str(e))

        return self._redirect('.item_selection')

    def __load_user_component(self, user_components: list):
        """Load user custom fields.

        Args:
            user_components (list): Components render in the user registry view
        """
        user_fields = WS.get_user_conf(self._app)
        # Add the custom user fields
        for field in user_fields:
            component = 'component/{}.html'.format(field[WS.USER_FIELD_TYPE])
            user_components.append(render_template(component, **field))

    def __load_group_component(self, user_components: list):
        """Load the group selection component
        Args:
            user_components (list): Components render in the user registry view
        """
        # Allow multiple item selection only if the item's weight distribution is "equal"
        multiple_selection = False
        if WebsiteControl().get_conf().weight_configuration == WebsiteControl.EQUAL_WEIGHT:
            multiple_selection = True

        groups = Group.query.all()
        user_components.append(render_template('component/group.html', **{
            'groups': groups,
            'label': WS.get_text(WS.USER_REGISTRATION_GROUP_QUESTION_LABEL, self._app),
            'multiple_selection': multiple_selection,
            'group_selection_error': WS.get_text(
                WS.USER_REGISTRATION_GROUP_SELECTION_ERROR, self._app)
        }))

    def __load_ethics_component(self, user_components: list):
        """Load the ethics agreement component

        Args:
            user_components (list): Components render in the user registry view
        """
        render_ethics = WS.should_render(WS.BEHAVIOR_RENDER_ETHICS_AGREEMENT_PAGE, self._app)
        if render_ethics:
            user_components.append(render_template('component/ethics.html', **{
                'ethics_agreement_label': WS.get_text(
                    WS.USER_REGISTRATION_ETHICS_AGREEMENT_LABEL, self._app)
            }))
