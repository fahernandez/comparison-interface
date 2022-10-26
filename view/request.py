# Custom imports
from configuration.website import Settings as WS
from flask import (render_template, redirect, url_for)


class Request():
    """View Base class"""
    def __init__(self, app, session) -> None:
        self._app = app
        self._session = session

    @staticmethod
    def process(handler, request):
        if request.method == 'GET':
            return handler.get(request)
        if request.method == 'POST':
            return handler.post(request)

        raise "Method not implemented."

    def get(self, request):
        raise "Method not implemented."

    def post(self, request):
        raise "Method not implemented."

    def get_layout_text(self):
        """Get the application layout configuration text

        Returns:
            dict: Layout configured text
        """
        render_instructions = WS.should_render(
            WS.BEHAVIOR_RENDER_USER_INSTRUCTION_PAGE, self._app)
        render_ethics_agreement = WS.should_render(
            WS.BEHAVIOR_RENDER_ETHICS_AGREEMENT_PAGE, self._app)
        return {
            'website_title': WS.get_text(WS.WEBSITE_TITLE, self._app),
            'introduction_page_title': WS.get_text(WS.PAGE_TITLE_INTRODUCTION, self._app),
            'ethics_agreement_page_title': WS.get_text(WS.PAGE_TITLE_ETHICS_AGREEMENT, self._app),
            'user_registration_page_title': WS.get_text(WS.PAGE_TITLE_USER_REGISTRATION, self._app),
            'logout_page_title': WS.get_text(WS.PAGE_TITLE_LOGOUT, self._app),
            'item_preference_page_title': WS.get_text(WS.PAGE_TITLE_ITEM_PREFERENCE, self._app),
            'rank_page_title': WS.get_text(WS.PAGE_TITLE_RANK, self._app),
            'render_user_instructions': render_instructions,
            'render_user_ethics_agreement': render_ethics_agreement
        }

    def _valid_session(self):
        """Verify if the user session is valid."""

        if "user_id" not in self._session or "group_ids" not in self._session:
            return False
        return True

    def _render_template(self, template: str, args: dict = None):
        """Render a HTML template using flask and Jinga2

        Args:
            template (str): iew html template location
            args (dict, optional): args used to render the template
        """
        if args is None or len(args) == 0:
            return render_template(template, **self.get_layout_text())
        return render_template(template, **{**args, **self.get_layout_text()})

    def _redirect(self, url: str, **values):
        """Redirect the web pase to a new location

        Args:
            url (str): Url where to redirect to

        Returns:
            Redirect the user to the provided URL
        """
        return redirect(url_for(url, **values))
