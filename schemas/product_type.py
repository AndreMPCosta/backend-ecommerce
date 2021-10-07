from marshmallow.fields import Nested
from marshmallow_mongoengine import ModelSchema

from models.product_type import ProductTypeModel


class ProductTypeSchema(ModelSchema):
    # __nested__ = False

    class Meta:
        model = ProductTypeModel
        exclude = ('translations',)

    attributes = Nested('AttributeSchema', many=True, exclude=('translations',))
