"""Flask specific setting configuration"""

class Settings(object):
    SECRET_KEY = 'jsd21@hGH11' # Change by your own secret key
    SQLALCHEMY_DATABASE_URI='sqlite:///tmp/database.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_MINUTES_VALIDITY = 240 # Session expire after 4 hours of inactivity