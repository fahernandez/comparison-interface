from flask import (Blueprint, request, session, current_app)
# Custom libraries
from view.introduction import Introduction
from view.ethics import Ethics
from view.register import Register
from view.item_preference import ItemsPreference
from view.rank import Rank
from view.logout import Logout
from view.request import Request


blueprint = Blueprint('views', __name__)


@blueprint.route('/introduction', methods=['GET'])
def introduction():
    return Request.process(Introduction(current_app, session), request)


@blueprint.route('/ethics-agreement', methods=['GET'])
def ethics_agreement():
    return Request.process(Ethics(current_app, session), request)


@blueprint.route('/', methods=['GET', 'POST'])
@blueprint.route('/register', methods=['GET', 'POST'])
def user_registration():
    return Request.process(Register(current_app, session), request)


@blueprint.route('/selection/items', methods=['GET', 'POST'])
def item_selection():
    return Request.process(ItemsPreference(current_app, session), request)


@blueprint.route('/rank', methods=['GET', 'POST'])
def rank():
    return Request.process(Rank(current_app, session), request)


@blueprint.route('/logout', methods=['GET'])
def logout():
    return Request.process(Logout(current_app, session), request)
