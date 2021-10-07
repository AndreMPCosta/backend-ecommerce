from datetime import datetime

from mongoengine import Document, ReferenceField, IntField, DecimalField, \
    signals, StringField, EmbeddedDocumentListField, DateTimeField, BooleanField, DictField

from config import free_shipping
from models.base import Base
from models.user import CartItem


class OrderModel(Document, Base):
    meta = {
        'collection': 'orders'
    }

    user = ReferenceField('UserModel')
    nif: str = StringField(default='')
    items = EmbeddedDocumentListField(CartItem, required=False, default=[])
    amount: float = DecimalField(min_value=0, default=0)
    created_at: datetime = DateTimeField(default=datetime.now())
    updated_at: datetime = DateTimeField(default=datetime.now())
    currency: str = StringField(default='eur')
    status: str = StringField(default='awaiting_payment', required=False)
    number: int = IntField(default=0)
    shipped: str = StringField(default='awaiting_shipment')
    shipping_cost: float = DecimalField(default=5.00)
    is_invoice_generated: bool = BooleanField(default=False)
    last_updated_at_invoice: datetime = DateTimeField(required=False)
    mb_reference = DictField(required=False)
    shipping_address = DictField(required=False)
    billing_address = DictField(required=False)
    payment_method: str = StringField(default='')

    @classmethod
    def post_save(cls, _, document, **kwargs):
        if kwargs.get('created'):
            document.items = document.user.cart
            document.created_at = datetime.now()
            document.updated_at = datetime.now()
            for item in document.user.cart:
                document.amount += item.product.price * item.quantity
                item.product.update_quantity(item)
            if document.amount > free_shipping:
                document.shipping_cost = 0
            document.number = cls.count({})
            document.save()
            document.user.orders.append(document)
            document.user.save()


signals.post_save.connect(OrderModel.post_save, sender=OrderModel)
