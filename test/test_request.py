import pytest
import shutil
from os.path import exists
from flask import session
# Custom libraries
from model.schema import WebsiteControl, User, Comparison
from model.connection import db
from configuration.website import Settings as WS
from configuration.flask import Settings
from website import create_app

# Configuration location
conf_equal_weight = "example/config-equal-item-weights.json"
conf_custom_weight = "example/config-custom-item-weights.json"
user_data = {
    'name': 'Dummy test',
    'gender': 'Prefer not to say',
    'allergies': 'Yes',
    'age': '30',
    'group_ids': '1',
    'email': 'dummy@test',
    'accepted_ethics_agreement': '1'
}


@pytest.fixture(scope='session')
def clear_files():
    yield None

    # Starting with a clean testing setup
    shutil.rmtree(Settings.TEMPORAL_DATA_LOCATION)


@pytest.fixture(scope='session')
def app():
    # Set-up the project for testing
    app = create_app()
    app.config.update({
        "TESTING": True,
    })

    yield app


@pytest.fixture(scope='session')
def client(app):
    return app.test_client()


@pytest.fixture(scope='session')
def runner(app):
    return app.test_cli_runner()


def test_setup_equal_weights(clear_files, runner, app):
    config_file = conf_equal_weight
    result = runner.invoke(args=["setup", config_file])
    assert "" in result.output

    # Get the application control variables (last step on the website setup project)
    with app.app_context():
        w = WebsiteControl()
        conf = w.get_conf()
        assert conf.configuration_file == config_file


def test_render_404(client):
    response = client.get("/not-exist")
    assert response.status_code == 404


def test_render_home(client):
    response = client.get("/")
    assert response.status_code == 200


def test_render_introduction(client):
    response = client.get("/introduction")
    assert response.status_code == 200


def test_render_ethics_agreement(client):
    response = client.get("/ethics-agreement")
    assert response.status_code == 200


def test_render_logout(client):
    response = client.get("/logout")
    # Logout should redirect to the register page
    assert response.status_code == 302


def test_render_user_register(client):
    response = client.get("/register")
    assert response.status_code == 200


def test_register_user(client, app):
    with client:
        response = client.post("/register", data=user_data)

        # Check that there was one redirect to the next page.
        assert response.status_code == 302

        # Verify the user was insert in the database
        with app.app_context():
            user = User.query.order_by(User.user_id.desc()).first()
            assert isinstance(user.user_id, int)
            assert user.user_id == session['user_id']


def test_render_prefer_item_selection(client):
    with client:
        client.post("/register", data=user_data)
        response = client.get("/selection/items", data=user_data)
        assert response.status_code == 200


def test_register_prefer_item_selection(client, app):
    with client:
        client.post("/register", data=user_data)
        response = client.post("/selection/items", data={
            'action': 'agree',
            'item_id': '1',
        })
        assert response.status_code == 302
        assert response.request.path == "/selection/items"


def test_reset_custom_weights(runner, app):
    config_file = conf_custom_weight
    result = runner.invoke(args=["reset", config_file])
    assert "" in result.output

    # Get the application control variables (last step on the website setup project)
    with app.app_context():
        w = WebsiteControl()
        conf = w.get_conf()
        assert conf.configuration_file == conf_custom_weight


def test_export_equal_weights(runner, app):
    result = runner.invoke(args=["export"])
    assert "" in result.output

    # Get the application control variables
    with app.app_context():
        assert exists(WS.get_export_location(app))


def test_render_rank_comparison(client):
    with client:
        client.post("/register", data=user_data)
        response = client.get("/rank")
        assert response.status_code == 200
        assert response.request.path == "/rank"


def test_register_selected_rank_comparison(client, app):
    with client:
        client.post("/register", data=user_data)
        response = client.post("/rank", data={
            'state': 'confirmed',
            'item_1_id': '1',
            'item_2_id': '2',
            'selected_item_id': '1',
        })
        assert response.status_code == 302
        assert response.request.path == "/rank"

        with app.app_context():
            comp = db.session.query(Comparison).\
                where(
                    Comparison.comparison_id == session['previous_comparison_id'],
                    Comparison.user_id == session['user_id']).first()
            assert comp.comparison_id == session['previous_comparison_id']
            assert comp.user_id == session['user_id']
            assert comp.selected_item_id == 1
            assert comp.state == 'selected'
            assert comp.item_1_id == 1
            assert comp.item_2_id == 2


def test_register_skipped_rank_comparison(client, app):
    with client:
        client.post("/register", data=user_data)
        response = client.post("/rank", data={
            'state': 'skipped',
            'item_1_id': '1',
            'item_2_id': '2'
        })
        assert response.status_code == 302
        assert response.request.path == "/rank"

        with app.app_context():
            comp = db.session.query(Comparison).\
                where(
                    Comparison.comparison_id == session['previous_comparison_id'],
                    Comparison.user_id == session['user_id']).first()
            assert comp.comparison_id == session['previous_comparison_id']
            assert comp.user_id == session['user_id']
            assert comp.selected_item_id == None  # noqa
            assert comp.state == 'skipped'
            assert comp.item_1_id == 1
            assert comp.item_2_id == 2
