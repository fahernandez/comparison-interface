from marshmallow import ValidationError
# Custom imports
from configuration.website import Settings as WS
from configuration.schema import Configuration as ConfigSchema


class Validation:
    def __init__(self, app) -> None:
        self.__app = app

    def validate(self) -> list:
        """Execute the website configuration validation.

        Returns:
            list: _description_
        """
        conf = WS.get_configuration(self.__app)
        schema = ConfigSchema()
        try:
            schema.load(conf)
        except ValidationError as err:
            self.__app.logger.critical(err)
            exit()
