from marshmallow.fields import Nested
from marshmallow_mongoengine import ModelSchema

from models.category import CategoryModel


class CategorySchema(ModelSchema):
    # __nested__ = False

    class Meta:
        model = CategoryModel
        exclude = ('translations',)

    subcategories = Nested(
        'CategorySchema', many=True,
        exclude=('parent_id', 'translations')
    )
