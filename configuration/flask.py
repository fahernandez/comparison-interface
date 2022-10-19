"""Website configuration used by Flask library settings"""


class Settings(object):
    SECRET_KEY = 'jsd21@hGH11' # Change by your own secret key
    CONFIG_TYPE = 'development'
    WEBSITE_TITLE = 'Comparative Judgement'
    WEBSITE_ADMINISTRATOR = 'Site Administrator Name.'
    WEBSITE_ADMINISTRATOR_EMAIL = 'admin@admin.com'
    SQLALCHEMY_DATABASE_URI='sqlite:///./model/database.db'
    EXPORT_PATH_LOCATION='./model/database.xlsx'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SEND_FILE_MAX_AGE_DEFAULT = 10
    WEBSITE_SETUP_LOCATION = './configuration/website-example-1.json'
    RENDER_USER_ITEM_PREFERENCE = True
    RENDER_USER_INSTRUCTIONS = True
    RENDER_ETHICS_AGREEMENT = True
    USER_INSTRUCTIONS_LINK = "https://docs.google.com/document/d/e/2PACX-1vT2yGXStletU0XGL6DaA45tSr3skJLIi2u-m5T9t3gNEjjXdN__c4yJhhN0CyzuDsFltKUFfBDt2qEJ/pub?embedded=true"
    ETHICS_AGREEMENT_LINK = "https://docs.google.com/document/d/e/2PACX-1vT2yGXStletU0XGL6DaA45tSr3skJLIi2u-m5T9t3gNEjjXdN__c4yJhhN0CyzuDsFltKUFfBDt2qEJ/pub?embedded=true"