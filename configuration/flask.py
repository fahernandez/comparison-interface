"""Website configuration used by Flask library settings"""


class Settings(object):
    SECRET_KEY = 'jsd21@hGH11' # Change by your own secret key
    CONFIG_TYPE = 'development'
    WEBSITE_TITLE = 'Comparative Judgement'
    WEBSITE_ADMINISTRATOR = 'Site Administrator Name.'
    WEBSITE_ADMINISTRATOR_EMAIL = 'admin@admin.com'
    SQLALCHEMY_DATABASE_URI='sqlite:///./model/database.db'
    EXPORT_PATH_LOCATION='model/database.xlsx'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SEND_FILE_MAX_AGE_DEFAULT = 10
    WEBSITE_SETUP_LOCATION = 'configuration/website-south-yorkshire.json'
    RENDER_USER_ITEM_PREFERENCE = False