import json
import os

class Setup:
    # Group related configuration keys
    COMPARISON_CONFIGURATION = 'comparisonConfiguration'
    GROUPS = 'groups'
    GROUP_NAME = 'name'
    GROUP_DISPLAY_NAME = 'displayName'
    GROUP_ITEMS = 'items'
    GROUP_ITEMS_WEIGHT = 'weight'
    # Items related configuration keys
    ITEM_NAME = 'name'
    ITEM_GROUP_ID = 'group_id'
    ITEM_DISPLAY_NAME = 'displayName'
    ITEM_IMAGE_NAME = 'imageName'
    # Website configuration
    WEBSITE_CONFIGURATION = 'websiteConfiguration'
    WEBSITE_WEIGHT_CONFIGURATION = 'weightConfiguration'
    WEBSITE_LABEL = 'label'
    WEBSITE_USER_FIELDS = 'userFields'
    # User fields
    USER_FIELD_NAME = "name"
    USER_FIELD_DISPLAY_NAME = "displayName"
    USER_FIELD_TYPE = "type"
    USER_FIELD_MAX_LIMIT = "maxLimit"
    USER_FIELD_MIN_LIMIT = "minLimit"
    USER_FIELD_REQUIRED = "required"
    USER_FIELD_SELECT_OPTION = "option"
    # User fields configuration options
    USER_FIELD_TYPE_TEXT = 'text'
    USER_FIELD_TYPE_INT = 'int'
    USER_FIELD_TYPE_DROPDOWN = 'dropdown'
    USER_FIELD_TYPE_RADIO = 'radio'
    USER_FIELD_TYPE_EMAIL = 'email'
    # Website labels
    LABEL_WEBSITE_LOGOUT = "websiteLogout"
    LABEL_GROUP_QUESTION = "groupQuestion"
    LABEL_SITE_HOME_LABEL = "websitehome"
    LABEL_USER_REGISTER_FORM_TITLE = "userRegisterFormTitle"
    LABEL_USER_REGISTER_BUTTON = "userRegisterButton"
    LABEL_ITEM_SELECTION_QUESTION = "itemSelectionQuestion"
    LABEL_ITEM_SELECTION_YES_BUTTON = "itemSelectionYesButton"
    LABEL_ITEM_SELECTION_NO_BUTTON = "itemSelectionNoButton"
    LABEL_ITEM_SELECTED_LABEL = "itemSelectedIndicatorLabel"
    LABEL_ITEM_INSTRUCTION  = "itemInstruction"
    LABEL_COMPARISON_NUMBER  = "comparisonNumberLabel"
    LABEL_SKIPPED_NUMBER  = "skippedNumberLabel"
    LABEL_ITEM_REJUDGE_BUTTON = "itemRejudgeButton"
    LABEL_ITEM_CONFIRMED_BUTTON = "itemConfirmedButton"
    LABEL_ITEM_SKIPPED_BUTTON = "itemSkippedButton"
    LABEL_TIGHT_SELECTION_LABEL = "tightSelectionIndicatorLabel"

    def __init__(self, app) -> None:
        self.app = app

    def load(self, validate=True):
        """Load and validate the website configuration

        Args:
            app (Flask): Flask application
            validate (Boolean): Flag to validate the configuration. The validation
            will be validated during setup only. Later on the program execution, it
            will be unmarshall and returned only.
        Returns:
            json: Website configuration file.
        """
        config_data = self.unmarshall()
        if validate:
            try:
                self.validate(config_data)
            except Exception as e:
                self.app.logger.critical(e)
                exit()

        return config_data
        

    def unmarshall(self):
        """Load the configuration file and load it into a Json object.

        Args:
            app (Flask): Flask application

        Returns:
            json: Website configuration file.
        """
        location = os.path.join(os.path.dirname(__file__), self.app.config['WEBSITE_SETUP_LOCATION'])
        config_data = None
        try:
            with open(location, 'r') as config_file:
                config_data = json.load(config_file)
        except IOError as e:
            self.app.logger.critical("Website configuration file %s not found" % (location))
            exit()
        except ValueError:
            self.app.logger.critical("Website configuration file %s invalid json format" %  (location))
            exit()
        except Exception as e:
            self.app.logger.critical(e)
            exit()
        return config_data

    def validate(self, config_data):
        """Validate the structure of the configuration file.
        This function will raise a set of exeptions in case of configuration problems.

        Args:
            config_data (json): Website configuration file

        Returns:
            _type_: _description_
        """
        # TODO: pending implementation
        # Group
        # Validate at least one group.
        # Validate existance
        # Validate Groups keys existance
        # Validate Groups unique names
        # Weight configuration types
        # Text limit.
        # Items
        # No empty/array
        # Name limit
        # Display name limit
        # Image name limit/existance
        # Weight Number
        # Weight sum close to 1
        # On Weight manual all items must have weight
        # User
        # Name unique/text/lenght/required/lowercase/no_space
        # Display name /text/lenght/required
        # required boolean/required
        # display order int/required
        # type text/{expected only}/required
        
        
        
        return None