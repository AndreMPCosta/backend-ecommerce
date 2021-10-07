from marshmallow.fields import Nested
from marshmallow_mongoengine import ModelSchema

from models import ProductModel


class Patch:
    pk = None

    def __init__(self, pk):
        self.pk = pk


class ProductSchema(ModelSchema):
    # __nested__ = False

    class Meta:
        model = ProductModel
        exclude = ('translations',)

    # attributes = Nested('AttributeSchema', many=True,
    #                     exclude=('translations',))
    product_type = Nested('ProductTypeSchema', exclude=('translations',))
