from typing import Optional, List, Union

from bson import ObjectId
from mongoengine import Document, ListField, ReferenceField, StringField, signals, DictField, DecimalField, \
    BooleanField, IntField

from helpers import convert_to_slug
from helpers.db_helper_v2 import find, count
from models import ProductTypeModel
from models.base import Base
from models.category import CategoryModel
from models.user import CartItem


class ProductModel(Document, Base):
    meta = {
        'collection': 'products'
    }
    name: str = StringField(required=True, max_length=70)
    description: Optional[str] = StringField(required=False, default="")
    composition: Optional[str] = StringField(required=False, default="")
    image: Optional[str] = StringField(required=False, default="")
    alt_image: Optional[str] = StringField(required=False, default="")
    weight: Optional[str] = DecimalField(required=False, null=True, min_value=0, precision=2)
    price: float = DecimalField(required=True, min_value=0, precision=2)
    currency: Optional[str] = StringField(required=False, default='eur')
    # attributes: Optional[List] = ListField(ReferenceField('AttributeModel'), required=False,
    #                                        default=[])
    attributes: Optional[List] = ListField(DictField(), default=[])
    product_type: Optional = ReferenceField('ProductTypeModel', required=False)
    category: Optional['CategoryModel'] = ReferenceField('CategoryModel')  # ObjectIdField(required=True)
    slug: Optional[str] = StringField(required=False, default="")
    translations: List[str] = ListField(StringField(required=False), required=False, default=['name', 'description'])
    own_sold_out: bool = BooleanField(default=False)
    sold_out: List[str] = ListField(StringField(required=False), required=False, default=[])
    quantities: List[dict] = ListField(DictField(default={}), default=[])
    quantity: int = IntField(required=False, min_value=0)

    # @classmethod
    # def post_init(cls, _, document):
    #     if not document.slug:
    #         document.slug = convert_to_slug(document.name)
    #     if not document.id:
    #         from models.category_v2 import CategoryModel
    #         # cat = CategoryModel.get_by_id(document.category.id)
    #         document.category.number_of_products += 1
    #         document.category.save()
    #         if document.category.parent_id:
    #             parent = document.category.parent_id
    #             parent.number_of_products += 1
    #             parent.save()

    @staticmethod
    def fill_quantities(document, p_type_id):
        p_type = ProductTypeModel.get_by_id(p_type_id)
        if p_type.attributes:
            if not document.attributes:
                for a in p_type.attributes:
                    for o in a.options:
                        document.quantities.append({'name': str(o.name), 'option': 1})
            else:
                for a in document.attributes:
                    for o in a.get('options'):
                        temp = []
                        for a2 in p_type.attributes:
                            for o2 in a2.options:
                                temp.append({'name': str(o2.name), 'option': 1})
                        if not temp:
                            temp = 1
                        document.quantities.append({'name': o.get('name'), 'option': temp})

    @classmethod
    def pre_save(cls, _, document, **kwargs):
        if not document.id:
            if not document.slug:
                document.slug = convert_to_slug(document.name)
        if document.id:
            p_type_id = document.product_type
            if isinstance(p_type_id, ProductTypeModel):
                p_type_id = p_type_id.id
            if p_type_id != cls.get_by_id(document.id).product_type.id:
                document.quantities = []
                cls.fill_quantities(document, p_type_id)
            if document.attributes:
                for idx, attribute in enumerate(document.attributes):
                    if attribute.get('name') not in [x.get('name') for x in document.quantities]:
                        document.quantities.append({
                            'name': attribute.get('name'),
                            'option': []
                        })
                        for option in attribute.get('options'):
                            document.quantities[idx]['option'].append({
                                'name': option.get('name'),
                                'option': 1
                            })
                    else:
                        for option in attribute.get('options'):
                            if option.get('name') not in [x.get('name') for x in document.quantities[idx]['option']]:
                                document.quantities[idx]['option'].append({
                                    'name': option.get('name'),
                                    'option': 1
                                })

                # document.quantities.append()

    @classmethod
    def post_save(cls, _, document, **kwargs):
        if kwargs.get('created'):
            # if document.product_type:
            #     document.attributes = document.product_type.attributes
            #     document.save()
            document.category.number_of_products += 1
            document.category.save()
            if document.category.parent_id:
                parent = document.category.parent_id
                parent.number_of_products += 1
                parent.save()
            document.product_type = ProductTypeModel.get_by_id(document.product_type.id)
            if document.product_type.attributes:
                if not document.attributes:
                    for a in document.product_type.attributes:
                        for o in a.options:
                            document.quantities.append({'name': str(o.name), 'option': 1})
                else:
                    for a in document.attributes:
                        for o in a.get('options'):
                            temp = []
                            for a2 in document.product_type.attributes:
                                for o2 in a2.options:
                                    temp.append({'name': str(o2.name), 'option': 1})
                            document.quantities.append({'name': o.get('name'), 'option': temp})
        # updates, removals = document._delta()
        # if 'product_type' in updates:
        #     cls.product_type_update(document)

    async def add_attributes(self, attributes: List):
        self.attributes += attributes
        self.save()

    def helper_delete(self):
        self.category.number_of_products -= 1
        self.category.save()
        if self.category.parent_id:
            self.category.parent_id.number_of_products -= 1
            self.category.parent_id.save()

    @classmethod
    def get_by_category(cls, param: Union[str, ObjectId]):
        if isinstance(param, ObjectId):
            cat: CategoryModel = CategoryModel.get_by_id(param)
        else:
            cat: CategoryModel = CategoryModel.get_by_name(param)
        if cat:
            if not cat.parent_id:
                temp = [category.id for category in cat.subcategories]
            else:
                temp = [cat.id]
            return find(cls, {'category__in': temp})
        return []

    async def add_image(self, image, **kwargs):
        self.image = image
        self.save()

    async def add_attribute_image(self, image, attr_name, option_name):
        attr_index = next((index for (index, d) in enumerate(self.attributes) if d["name"] == attr_name), None)
        option_index = next((index for (index, d) in enumerate(self.attributes[attr_index].get('options')) if d["name"]
                             == option_name), None)
        self.attributes[attr_index].get('options')[option_index]['image'] = image
        self.save()
        # self.attributes
        # self.attributes[attr_name] = image
        # self.save()

    @classmethod
    def count_by_category(cls, param: Union[str, ObjectId]):
        if isinstance(param, ObjectId):
            return find(cls, {'category': param})
        else:
            cat: CategoryModel = CategoryModel.get_by_name(param)
            if not cat.parent_id:
                temp = [category.id for category in cat.subcategories]
            else:
                temp = [cat.id]
            return count(cls, {'category__in': temp})

    def update_quantity(self, payload: CartItem, replenish_stock=False):
        if len(payload.attributes) == 0:
            if not replenish_stock:
                self.quantity -= payload.quantity
            else:
                self.quantity += payload.quantity
        else:
            for index1, attribute in enumerate(self.quantities):
                if attribute.get('name') in [item.get('option') for item in payload.attributes]:
                    for a in payload.attributes:
                        for index2, item in enumerate(attribute.get('option')):
                            if a.get('option') == item.get('name'):
                                if not replenish_stock:
                                    self.quantities[index1]['option'][index2]['option'] -= payload.quantity
                                else:
                                    self.quantities[index1]['option'][index2]['option'] += payload.quantity
        self.save()


signals.pre_save.connect(ProductModel.pre_save, sender=ProductModel)
signals.post_save.connect(ProductModel.post_save, sender=ProductModel)

if __name__ == '__main__':
    c = ProductModel(
        name='Bathroom Songs 2',
        product_type='60a9adbda192373c9095471b',
        price=10.99,
        category='60a9adb1a192373c9095470b'
    )
    # asyncio.run(c.add_attributes([ProductModel.get_by_slug('size'), ProductModel.get_by_slug('color').id]))
    c.save()
