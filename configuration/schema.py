from marshmallow import (Schema, fields, validates,
                         post_load, ValidationError, validate)
import cv2
import re
import os
import itertools

# Custom libraries
from model.schema import WebsiteControl
from configuration.website import Settings as WS


class Item(Schema):
    name = fields.Str(required=True, validate=[validate.Length(min=1, max=200)])
    displayName = fields.Str(required=True, validate=[validate.Length(min=1, max=200)])
    imageName = fields.Str(required=True, validate=[validate.Length(min=1, max=500)])

    # Allowed Items Image size
    MIN_WIDTH = 300
    MIN_HEIGHT = 300

    @validates('name')
    def _validate_name(self, name):
        match = re.match(r'^[a-z0-9_-]+$', name)
        if not match:
            raise ValidationError("Name can be only alpha numeric lower case values. I.e. "
                                  "this_is_a_valid_name")

    @validates('imageName')
    def _validate_image_path(self, image_name):
        path = os.path.abspath(os.path.dirname(__file__)) + "/../static/image/" + image_name
        if not os.path.exists(path):
            raise ValidationError(f"Image {image_name} not found on static/image/ folder.")

        try:
            im = cv2.imread(path)
            h, w, _ = im.shape
            if h < self.MIN_HEIGHT or w < self.MIN_WIDTH:
                raise ValidationError("All item images must be at least " +
                                      f"{self.MIN_HEIGHT}x{self.MIN_WIDTH}px")
        except Exception as e:
            raise ValidationError(str(e))


class Weight(Schema):
    item_1 = fields.Str(required=True, validate=[validate.Length(min=1, max=200)])
    item_2 = fields.Str(required=True, validate=[validate.Length(min=1, max=200)])
    weight = fields.Float(required=True, validate=[validate.Range(min=0.0, max=1.0)])

    @validates('item_1')
    @validates('item_2')
    def _validate_item_name(self, name):
        match = re.match(r'^[a-z0-9_-]+$', name)
        if not match:
            raise ValidationError("Weight items name can be only alpha numeric "
                                  "lower case values. I.e. this_is_a_valid_name")


class Group(Schema):
    name = fields.Str(required=True, validate=[validate.Length(min=1, max=200)])
    displayName = fields.Str(required=True, validate=[validate.Length(min=1, max=200)])
    items = fields.List(fields.Nested(Item()), required=True,
                        validate=[validate.Length(min=1, max=1000)])
    weight = fields.List(fields.Nested(Weight()), required=False,
                         validate=[validate.Length(min=1, max=499500)])

    @validates('items')
    def _validate_unique_names(self, items):
        names = []
        for f in items:
            if f['name'] in names:
                raise ValidationError("All items in the same group must have an unique name. "
                                      "Repeated name {}".format(f['name']))
            else:
                names.append(f['name'])

    @validates('weight')
    def _validate_weight_sum(self, weights):
        w = 0
        for g in weights:
            w += g['weight']

        if w < 0.98 or w > 1.02:
            raise ValidationError("Custom weights for item's pairs must sum close to 1. " +
                                  f"Actual weight sum {w}.")

    @post_load
    def _post_load_validation(self, data, **kwargs):
        if 'weight' not in data:
            return data

        # Validate item pairs name when defined
        items = data['items']
        weights = data['weight']
        items_name = [i['name'] for i in items]
        pairs = []
        for w in weights:
            if w['item_1'] not in items_name:
                raise ValidationError(f"{w['item_1']} not defined as item name.")
            if w['item_2'] not in items_name:
                raise ValidationError(f"{w['item_2']} not defined as item name.")

            # The order of the pair is important to validate the combinations
            pairs.append((w['item_1'], w['item_2']))
            pairs.append((w['item_2'], w['item_1']))

        # Validate that a weight was custom defined for all item pairs
        possible_pair_combinations = list(itertools.combinations(items_name, 2))
        for pair in possible_pair_combinations:
            if pair not in pairs:
                raise ValidationError(f"Custom weight for item pair {pair} needs to be defined.")
        return data

    @validates('name')
    def _validate_group_name(self, name):
        match = re.match(r'^[a-z0-9_-]+$', name)
        if not match:
            raise ValidationError("Group name can be only alpha numeric lower case values. I.e. "
                                  "this_is_a_valid_name")


class ComparisonConfiguration(Schema):
    weightConfiguration = fields.Str(required=True)
    groups = fields.List(fields.Nested(Group()),
                         required=True,
                         validate=[validate.Length(min=1, max=100)])

    @post_load
    def _post_load_validation(self, data, **kwargs):
        weight_conf = data['weightConfiguration']
        groups = data['groups']
        item_weight_conf = sum([1 if "weight" in g else 0 for g in groups])

        if item_weight_conf != 0 and weight_conf == WebsiteControl.EQUAL_WEIGHT:
            raise ValidationError("Custom weight configuration is not allowed when "
                                  "the weight configuration was defined as 'equal'.")

        if item_weight_conf != len(groups) and weight_conf == WebsiteControl.CUSTOM_WEIGHT:
            raise ValidationError("Custom weight configuration is required for all groups "
                                  "when the weight configuration was defined as 'custom'.")

        return data


class WebsiteTextConfiguration(Schema):
    websiteTitle = fields.Str(required=True, validate=[validate.Length(min=1, max=100)])
    pageTitleLogout = fields.Str(required=True, validate=[validate.Length(min=1, max=50)])
    pageTitleUserRegistration = fields.Str(required=True, validate=[validate.Length(min=1, max=50)])
    pageTitleEthicsAgreement = fields.Str(required=True, validate=[validate.Length(min=1, max=50)])
    pageTitleIntroduction = fields.Str(required=True, validate=[validate.Length(min=1, max=50)])
    pageTitleItemPreference = fields.Str(required=True, validate=[validate.Length(min=1, max=50)])
    pageTitleRank = fields.Str(required=True, validate=[validate.Length(min=1, max=50)])
    userRegistrationGroupQuestionLabel = fields.Str(required=True,
                                                    validate=[validate.Length(min=1, max=500)])
    userRegistrationFormTitleLabel = fields.Str(required=True,
                                                validate=[validate.Length(min=1, max=50)])
    userRegistrationSummitButtonLabel = fields.Str(required=True,
                                                   validate=[validate.Length(min=1, max=50)])
    userRegistrationGroupSelectionErr = fields.Str(required=True,
                                                   validate=[validate.Length(min=1, max=500)])
    userRegistrationEthicsAgreementLabel = fields.Str(required=True,
                                                      validate=[validate.Length(min=1, max=500)])
    itemSelectionQuestionLabel = fields.Str(required=True,
                                            validate=[validate.Length(min=1, max=500)])
    itemSelectionYesButtonLabel = fields.Str(required=True,
                                             validate=[validate.Length(min=1, max=50)])
    itemSelectionNoButtonLabel = fields.Str(required=True,
                                            validate=[validate.Length(min=1, max=50)])
    itemSelectedIndicatorLabel = fields.Str(required=True,
                                            validate=[validate.Length(min=1, max=50)])
    rankItemTiedSelectionIndicatorLabel = fields.Str(required=True,
                                                     validate=[validate.Length(min=1, max=50)])
    rankItemItemRejudgeButtonLabel = fields.Str(required=True,
                                                validate=[validate.Length(min=1, max=50)])
    rankItemConfirmedButtonLabel = fields.Str(required=True,
                                              validate=[validate.Length(min=1, max=50)])
    rankItemSkippedButtonLabel = fields.Str(required=True,
                                            validate=[validate.Length(min=1, max=50)])
    rankItemInstructionLabel = fields.Str(required=True, validate=[validate.Length(min=1, max=500)])
    rankItemComparisonExecutedLabel = fields.Str(required=True,
                                                 validate=[validate.Length(min=1, max=50)])
    rankItemSkippedComparisonExecutedLabel = fields.Str(required=True,
                                                        validate=[validate.Length(min=1, max=50)])
    introductionContinueButtonLabel = fields.Str(required=True,
                                                 validate=[validate.Length(min=1, max=50)])
    ethicsAgreementBackButtonLabel = fields.Str(required=True,
                                                validate=[validate.Length(min=1, max=50)])


class UserField(Schema):
    name = fields.Str(required=True,
                      validate=[validate.Length(min=1, max=100)])
    displayName = fields.Str(required=True, validate=[validate.Length(min=1, max=100)])
    type = fields.Str(required=True, validate=[validate.OneOf([
        WS.USER_FIELD_TYPE_TEXT,
        WS.USER_FIELD_TYPE_INT,
        WS.USER_FIELD_TYPE_DROPDOWN,
        WS.USER_FIELD_TYPE_RADIO,
        WS.USER_FIELD_TYPE_EMAIL
    ])])
    maxLimit = fields.Int()
    minLimit = fields.Int()
    required = fields.Boolean(required=True)
    option = fields.List(fields.Str(), validate=[validate.Length(min=1, max=20)])

    @validates('name')
    def _validate_name(self, name):
        match = re.match(r'^[a-z0-9_-]+$', name)
        if not match:
            raise ValidationError("Name can be only alpha numeric lower case values. I.e. "
                                  "this_is_a_valid_name")

    @post_load
    def _post_load_validation(self, data, **kwargs):
        # Validate option definition for dropdown and radio fields
        if data['type'] in [WS.USER_FIELD_TYPE_DROPDOWN, WS.USER_FIELD_TYPE_RADIO] and \
           'option' not in data:
            raise ValidationError(f"{data['type']} fields require the definition "
                                  "of the option field.")

        # Validate no option definition for no dropdown or radio fields
        if data['type'] not in [WS.USER_FIELD_TYPE_DROPDOWN, WS.USER_FIELD_TYPE_RADIO] and \
           'option' in data:
            raise ValidationError(f"Option field cannot be defined for {data['type']} fields.")

        # Validate max limit for email, text and int fields
        if data['type'] in [
            WS.USER_FIELD_TYPE_TEXT,
                WS.USER_FIELD_TYPE_INT,
                WS.USER_FIELD_TYPE_EMAIL] and 'maxLimit' not in data:
            raise ValidationError(f"{data['type']} fields require the definition "
                                  "of the numerical maxLimit field.")

        # Validate not max limit for not email, text or int fields
        if data['type'] not in [
            WS.USER_FIELD_TYPE_TEXT,
                WS.USER_FIELD_TYPE_INT,
                WS.USER_FIELD_TYPE_EMAIL] and 'maxLimit' in data:
            raise ValidationError(f"MaxLimit field cannot be defined for {data['type']} fields.")

        # Validate min limit for int field
        if data['type'] in [WS.USER_FIELD_TYPE_INT] and 'minLimit' not in data:
            raise ValidationError(f"{data['type']} fields require the definition "
                                  "of the numerical minLimit field.")

        # Validate not min limit for not  int fields
        if data['type'] not in [WS.USER_FIELD_TYPE_INT] and 'minLimit' in data:
            raise ValidationError(f"MinLimit field cannot be defined for {data['type']} fields.")

        return data


class BehaviorConfiguration(Schema):
    exportPathLocation = fields.Str(required=True,
                                    validate=[
                                        validate.Length(min=1, max=500)])
    renderUserItemPreferencePage = fields.Boolean(required=True)
    renderUserInstructionPage = fields.Boolean(required=True)
    renderEthicsAgreementPage = fields.Boolean(required=True)
    userInstructionLink = fields.URL(required=False,
                                     validate=[validate.Length(min=1)])
    userEthicsAgreementLink = fields.URL(required=False,
                                         validate=[validate.Length(min=1)])

    @post_load
    def _post_load_validation(self, data, **kwargs):
        if data['renderEthicsAgreementPage'] and \
           'userEthicsAgreementLink' not in data:
            raise ValidationError("Field userEthicsAgreementLink is missing")

        if data['renderUserInstructionPage'] and \
           'userInstructionLink' not in data:
            raise ValidationError("Field userInstructionLink is missing")

        return data


class Configuration(Schema):
    behaviorConfiguration = fields.Nested(BehaviorConfiguration(), required=True)
    comparisonConfiguration = fields.Nested(ComparisonConfiguration(), required=True)
    websiteTextConfiguration = fields.Nested(WebsiteTextConfiguration(), required=True)
    userFieldsConfiguration = fields.List(
        fields.Nested(UserField()),
        required=True, validate=[validate.Length(min=1, max=20)])

    @validates('userFieldsConfiguration')
    def _validate_unique_names(self, fields):
        names = []
        for f in fields:
            if f['name'] in names:
                raise ValidationError("All user defined field must have an unique name. "
                                      "Repeated name {}".format(f['name']))
            else:
                names.append(f['name'])

    @post_load
    def _post_load_validation(self, data, **kwargs):
        # Validate user preference render behavior
        weight_conf = data['comparisonConfiguration']['weightConfiguration']
        render_item_preference = data['behaviorConfiguration']['renderUserItemPreferencePage']
        if weight_conf == WebsiteControl.CUSTOM_WEIGHT and render_item_preference:
            raise ValidationError("User item preference section cannot be render while defining "
                                  "a manual weight configuration. Please change "
                                  "renderUserItemPreferencePage to false")

        return data
