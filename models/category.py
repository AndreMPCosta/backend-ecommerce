import asyncio
from typing import List, Optional

from mongoengine import Document, StringField, ListField, ReferenceField, signals, IntField

from helpers import convert_to_slug
from models.base import Base


class CategoryModel(Document, Base):
    meta = {
        'collection': 'categories'
    }
    name: str = StringField(required=True, max_length=70)
    description: Optional[str] = StringField(required=False, default="")
    parent_id: Optional['CategoryModel'] = ReferenceField('CategoryModel', required=False, null=True)
    image: Optional[str] = StringField(required=False, default="")
    subcategories: Optional[List['CategoryModel']] = ListField(ReferenceField('CategoryModel'), required=False,
                                                               default=[])
    slug: Optional[str] = StringField(required=False, default="")
    # products = ListField(ReferenceField('ProductModel'), required=False, default=[])
    translations: Optional[List[str]] = ListField(StringField(required=False), required=False,
                                                  default=['name', 'description'])
    number_of_products: Optional[int] = IntField(required=False, default=0)

    @classmethod
    def post_save(cls, _, document, **kwargs):
        if kwargs.get('created'):
            if document.parent_id:
                # print('linking parent_id from category model')
                parent = cls.get_by_id(document.parent_id.id)
                parent.subcategories.append(document)
                parent.save()
            if not document.slug:
                document.slug = convert_to_slug(document.name)
                document.save()

    async def remove_subcategory(self, subcategory):
        self.subcategories.remove(subcategory)
        self.save()

    async def add_subcategory(self, subcategory):
        self.subcategories.append(subcategory)
        self.save()

    async def add_parent(self, parent):
        self.parent_id = parent.id
        self.save()

    async def add_image(self, image, **kwargs):
        self.image = image
        self.save()

    async def delete_subcategories(self):
        tasks = []
        for sub in self.subcategories:
            task = asyncio.ensure_future(self.delete_subcategory(sub))
            tasks.append(task)
        await asyncio.gather(*tasks)

    @staticmethod
    async def delete_subcategory(subcategory):
        subcategory.delete()


signals.post_save.connect(CategoryModel.post_save, sender=CategoryModel)

if __name__ == '__main__':
    c = CategoryModel(
        name='test',
        description='description'
    )
    c.save()
    c = CategoryModel(
        name='test2',
        description='description2'
    )
    c.save()
