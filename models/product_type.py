from typing import Optional, List
from mongoengine import Document, StringField, ListField, ReferenceField, signals

from helpers import convert_to_slug
from models.base import Base


class ProductTypeModel(Document, Base):
    meta = {
        'collection': 'product_types'
    }
    name: str = StringField(required=True, max_length=70)
    attributes: Optional[List] = ListField(ReferenceField('AttributeModel'), required=False,
                                           default=[])
    # forced_attributes: Optional[List[ObjectId]] = []
    slug: Optional[str] = StringField(required=False, default="")
    translations: Optional[List[str]] = ListField(StringField(required=False), required=False,
                                                  default=['name'])

    @classmethod
    def post_save(cls, _, document, **kwargs):
        if kwargs.get('created'):
            if not document.slug:
                document.slug = convert_to_slug(document.name)
                document.save()

    async def add_attributes(self, attributes: List):
        self.attributes += attributes
        self.save()


signals.post_save.connect(ProductTypeModel.post_save, sender=ProductTypeModel)

if __name__ == '__main__':
    c = ProductTypeModel(
        name='Shoe'
    )
    # asyncio.run(c.add_attributes([AttributeModel.get_by_slug('size'), AttributeModel.get_by_slug('color').id]))
    c.save()
