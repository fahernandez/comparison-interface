from view.request import Request
from configuration.website import Settings as WS


class Introduction(Request):
    """Render the introduction page. This page contains an iframe
    with a link to a google doc with the webpage usage introductions."""

    def get(self, _):
        """Request get handler"""
        return self._render_template('page/introduction.html', {
            'user_instruction_link': WS.get_behavior_conf(
                WS.BEHAVIOR_USER_INSTRUCTION_LINK, self._app),
            'introduction_continue_button': WS.get_text(
                WS.LABEL_INTRODUCTION_CONTINUE_BUTTON_LABEL, self._app)
        })
