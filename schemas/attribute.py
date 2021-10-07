from marshmallow_mongoengine import ModelSchema

from models.attribute import AttributeModel


class AttributeSchema(ModelSchema):
    # __nested__ = False

    class Meta:
        model = AttributeModel
        exclude = ('translations',)
