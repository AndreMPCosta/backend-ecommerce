from marshmallow_mongoengine import ModelSchema

from models import PaymentModel


class PaymentSchema(ModelSchema):
    # __nested__ = False

    class Meta:
        model = PaymentModel
