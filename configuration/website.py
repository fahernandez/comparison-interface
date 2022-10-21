import json
import os

class Settings:
    # Json configuration object
    configuration = None
    
    ## #####################################
    # Configuration file key values
    ## #####################################
    CONFIGURATION_LOCATION = 'CONFIG_LOC'
    # Website configuration sections
    CONFIGURATION_BEHAVIOR = 'behaviorConfiguration'
    CONFIGURATION_COMPARISON = 'comparisonConfiguration'
    CONFIGURATION_USER_FIELDS = 'userFieldsConfiguration'
    CONFIGURATION_WEBSITE_TEXT = 'websiteTextConfiguration'
    # Website behavior configuration keys
    BEHAVIOUR_EXPORT_PATH_LOCATION = "exportPathLocation"
    BEHAVIOUR_RENDER_USER_ITEM_PREFERENCE_PAGE = "renderUserItemPreferencePage"
    BEHAVIOUR_RENDER_USER_INSTRUCTION_PAGE = "renderUserInstructionPage"
    BEHAVIOUR_RENDER_ETHICS_AGREEMENT_PAGE = "renderEthicsAgreementPage"
    BEHAVIOUR_USER_INSTRUCTION_LINK = "userInstructionLink"
    BEHAVIOUR_ETHICS_AGREEMENT_LINK = "userEthicsAgreementLink"
    # Group related configuration keys
    GROUPS = 'groups'
    GROUP_WEIGHT_CONFIGURATION = 'weightConfiguration'
    GROUP_NAME = 'name'
    GROUP_DISPLAY_NAME = 'displayName'
    GROUP_ITEMS = 'items'
    GROUP_ITEMS_WEIGHT = 'weight'
    # Items related configuration keys
    ITEM_NAME = 'name'
    ITEM_GROUP_ID = 'group_id'
    ITEM_DISPLAY_NAME = 'displayName'
    ITEM_IMAGE_NAME = 'imageName'
    # User fields configuration fileds
    USER_FIELD_NAME = "name"
    USER_FIELD_DISPLAY_NAME = "displayName"
    USER_FIELD_TYPE = "type"
    USER_FIELD_MAX_LIMIT = "maxLimit"
    USER_FIELD_MIN_LIMIT = "minLimit"
    USER_FIELD_REQUIRED = "required"
    USER_FIELD_SELECT_OPTION = "option"
    USER_FIELD_TYPE_TEXT = 'text'
    USER_FIELD_TYPE_INT = 'int'
    USER_FIELD_TYPE_DROPDOWN = 'dropdown'
    USER_FIELD_TYPE_RADIO = 'radio'
    USER_FIELD_TYPE_EMAIL = 'email'
    # Website labels
    WEBSITE_TITLE = "websiteTitle"
    PAGE_TITLE_LOGOUT = "pageTitleLogout"
    PAGE_TITLE_USER_REGISTRATION = "pageTitleUserRegistration"
    PAGE_TITLE_ETHICS_AGREEMENT = "pageTitleEthicsAgreement"
    PAGE_TITLE_INTRODUCTION= "pageTitleIntroduction"
    PAGE_TITLE_ITEM_PREFERENCE= "pageTitleItemPreference"
    PAGE_TITLE_RANK= "pageTitleRank"
    USER_REGISTRATION_GROUP_QUESTION_LABEL = "userRegistrationGroupQuestionLabel"
    USER_REGISTRATION_FORM_TITLE_LABEL = "userRegistrationFormTitleLabel"
    USER_REGISTRATION_SUMMIT_BUTTON_LABEL = "userRegistrationSummitButtonLabel"
    USER_REGISTRATION_GROUP_SELECTION_ERROR = "userRegistrationGroupSelectionErr"
    USER_REGISTRATION_ETHICS_AGREEMENT_LABEL = "userRegistrationEthicsAgreementLabel"
    ITEM_SELECTION_QUESTION_LABEL = "itemSelectionQuestionLabel"
    ITEM_SELECTION_YES_BUTTON_LABEL = "itemSelectionYesButtonLabel"
    ITEM_SELECTION_NO_BUTTON_LABEL = "itemSelectionNoButtonLabel"
    RANK_ITEM_SELECTED_INDICATOR_LABEL = "itemSelectedIndicatorLabel"
    RANK_ITEM_TIED_SELECTION_INDICATOR_LABEL = "rankItemTiedSelectionIndicatorLabel"
    RANK_ITEM_INSTRUCTION_LABEL  = "rankItemInstructionLabel"
    RANK_ITEM_COMPARISON_EXECUTED_LABEL  = "rankItemComparisonExecutedLabel"
    RANK_ITEM_SKIPPED_COMPARISON_EXECUTED_LABEL  = "rankItemSkippedComparisonExecutedLabel"
    RANK_ITEM_REJUDGE_BUTTON_LABEL = "rankItemItemRejudgeButtonLabel"
    RANK_ITEM_CONFIRMED_BUTTON_LABEL = "rankItemConfirmedButtonLabel"
    RANK_ITEM_SKIPPED_BUTTON_LABEL = "rankItemSkippedButtonLabel"
    LABEL_INTRODUCTION_CONTINUE_BUTTON_LABEL = "introductionContinueButtonLabel"
    LABEL_ETHICS_AGREEMENT_BACK_BUTTON_LABEL = "ethicsAgreementBackButtonLabel"

    @classmethod
    def set_configuration_location(cls, app, loc):
        """Set the website configuration file

        Args:
            app (Flask ap): Website main applicaiton
            loc (string): Path location of the configuration file
        """
        app.config[cls.CONFIGURATION_LOCATION] = loc
    
    @classmethod
    def get_configuration_location(cls, app):
        if not cls.CONFIGURATION_LOCATION in app.config:
            app.logger.critical("Configuration location not set in the application yet")
            exit()
        
        location = app.config[cls.CONFIGURATION_LOCATION]
        location = os.path.abspath(os.path.dirname(__file__)) + "/../" + location
        return location
    
    @classmethod
    def get_configuration(cls, app):
        """Get the website configuration.

        Args:
            app (Flask): Flask application

        Returns:
            json: website configuration object
        """
        if not cls.CONFIGURATION_LOCATION in app.config:
            app.logger.critical("Configuration location not set in the application yet")
            exit()
        
        if cls.configuration == None:
            app.logger.info("Loading website configuration")
            cls.configuration = cls.__load(app)

        return cls.configuration
        
    @classmethod
    def get_text(cls, label, app):
        """Get a particular text being render on the website. This text is configured by the user
        when the setup of the application is made.

        Args:
            label (string): Label text being required.
            app (Flask): Flask application
        
        Returns:
            string: Text configured by the user for the specific label
        """
        conf = cls.get_configuration(app)
        if not label in conf[cls.CONFIGURATION_WEBSITE_TEXT]:
            app.logger.critical(f"Label {label} wasn't found in the website text configuration.")
            exit()
        
        return conf[cls.CONFIGURATION_WEBSITE_TEXT][label]
    
    @classmethod
    def get_comparison_conf(cls, key, app):
        """Get the configuration values related to the comparison behavior of the website

        Args:
            key (string): configuration key required
            app (Flask App): Flask application

        Returns:
            string: Configuration value related to the key
        """
        conf = cls.get_configuration(app)
        if not key in conf[cls.CONFIGURATION_COMPARISON]:
            app.logger.critical(f"Label {key} wasn't found in the comparison configuration.")
            exit()

        return conf[cls.CONFIGURATION_COMPARISON][key]

    @classmethod
    def get_user_conf(cls, app):
        """Get the configuration values related to the user registry behavior of the website

        Args:
            key (string): configuration key required
            app (Flask App): Flask application

        Returns:
            string: Configuration value related to the key
        """
        conf = cls.get_configuration(app)
        if not cls.CONFIGURATION_USER_FIELDS in conf:
            app.logger.critical(f"User configuration section not found.")
            exit()
        
        return conf[cls.CONFIGURATION_USER_FIELDS]
    
    @classmethod
    def get_behavior_conf(cls, key, app):
        """Get the configuration values related to the behavior of the website

        Args:
            key (string): configuration key required
            app (Flask App): Flask application

        Returns:
            string: Configuration value related to the key
        """
        conf = cls.get_configuration(app)
        if not key in conf[cls.CONFIGURATION_BEHAVIOR]:
            app.logger.critical(f"Label {key} wasn't found in the behavior configuration.")
            exit()
        
        return conf[cls.CONFIGURATION_BEHAVIOR][key]

    @classmethod
    def shoud_render(cls, section, app):
        """Method to know if a particular section should be rendered

        Args:
            section (string): configuration key required
            app (Flask App): Flask application

        Returns:
            bolean: True when the section should be render, False other case.
        """
        render = cls.get_behavior_conf(section, app)
        return render == "true" or render == "True" or render == '1'
    
    @classmethod
    def get_export_location(cls, app):
        """Get the path where the information export will be made

        Args:
            app (Flask app)

        Returns:
            string: export path
        """
        path = cls.get_behavior_conf(cls.BEHAVIOUR_EXPORT_PATH_LOCATION, app)
        return os.path.abspath(os.path.dirname(__file__)) + "/../" + path

    @classmethod
    def get_layout_text(cls, app):
        """Get the application layout configuration text

        Args:
            app (Flask App): Main flask applicaiton

        Returns:
            dict: Layout configured text
        """
        return {
            'website_title': cls.get_text(cls.WEBSITE_TITLE, app),
            'introduction_page_title': cls.get_text(cls.PAGE_TITLE_INTRODUCTION, app),
            'ethics_agreement_page_title': cls.get_text(cls.PAGE_TITLE_ETHICS_AGREEMENT, app),
            'user_registration_page_title': cls.get_text(cls.PAGE_TITLE_USER_REGISTRATION, app),
            'logout_page_title': cls.get_text(cls.PAGE_TITLE_LOGOUT, app),
            'item_preference_page_title': cls.get_text(cls.PAGE_TITLE_ITEM_PREFERENCE, app),
            'rank_page_title': cls.get_text(cls.PAGE_TITLE_RANK, app),
            'render_user_instructions': cls.shoud_render(cls.BEHAVIOUR_RENDER_USER_INSTRUCTION_PAGE, app),
            'render_user_ethics_agreement': cls.shoud_render(cls.BEHAVIOUR_RENDER_ETHICS_AGREEMENT_PAGE, app)
        }
    
    @classmethod
    def __load(cls, app):
        """Load and validate the website configuration

        Args:
            app (Flask): Flask application
        Returns:
            json: Website configuration file.
        """
        config_data = cls.__unmarshall(app)
        try:
            cls.__validate(config_data)
        except Exception as e:
            app.logger.critical(e)
            exit()

        return config_data
        
    @classmethod
    def __unmarshall(cls, app):
        """Load the configuration file and load it into a Json object.

        Args:
            app (Flask): Flask application

        Returns:
            json: Website configuration file.
        """
        location = cls.get_configuration_location(app)
        config_data = None
        try:
            with open(location, 'r') as config_file:
                config_data = json.load(config_file)
        except IOError as e:
            app.logger.critical("Website configuration file %s not found" % (location))
            exit()
        except ValueError:
            app.logger.critical("Website configuration file %s invalid json format" %  (location))
            exit()
        except Exception as e:
            app.logger.critical(e)
            exit()
        return config_data

    @classmethod
    def __validate(cls, app):
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