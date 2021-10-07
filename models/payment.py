from datetime import datetime

from mongoengine import Document, ReferenceField, StringField, DictField, DateTimeField

from models.base import Base

methods = ('card', 'bank_transfer', 'mbway', 'mb_reference')
status = ('pending', 'rejected', 'completed')


class PaymentModel(Document, Base):
    meta = {
        'collection': 'payments'
    }

    order = ReferenceField('OrderModel')
    method: str = StringField(required=True, choices=methods)
    status: str = StringField(choices=status, default='pending')
    created_at: datetime = DateTimeField(default=datetime.now())
    updated_at: datetime = DateTimeField(default=datetime.now())
    stripe_info: dict = DictField(required=False)
