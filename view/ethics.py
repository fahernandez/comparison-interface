from view.request import Request
from configuration.website import Settings as WS


class Ethics(Request):
    """Render the ethics agreement page. This page containing an iframe
    with a link to a google doc with the ethics agreement."""

    def get(self, _):
        """Request get handler"""
        return self._render_template('page/ethics.html', {
            'ethics_agreement_link': WS.get_behavior_conf(
                WS.BEHAVIOR_ETHICS_AGREEMENT_LINK, self._app),
            'ethics_agreement_back_button': WS.get_text(
                WS.LABEL_ETHICS_AGREEMENT_BACK_BUTTON_LABEL, self._app)
        })
