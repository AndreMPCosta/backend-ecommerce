from marshmallow import post_dump
from marshmallow_mongoengine import ModelSchema

from models import OrderModel
from models.user import UserModel


def helper_builder(order):
    order_object = OrderModel.get_by_id(order)
    number_of_items = 0
    for item in order_object.items:
        number_of_items += item.quantity
    return {
        'id': str(order_object.id),
        'number': order_object.number,
        'updated_at': order_object.updated_at,
        'status': order_object.status,
        'amount': order_object.amount,
        'currency': order_object.currency,
        'shipped': order_object.shipped,
        'number_of_items': number_of_items,
        'shipping_cost': order_object.shipping_cost,
        'shipping_address': order_object.shipping_address,
        'billing_address': order_object.billing_address,
        'payment_method': order_object.payment_method,
        'mb_reference': order_object.mb_reference if 'mb_reference' in order_object else None,
        'items': [{
            'product': str(item.product.id),
            'attributes': item.attributes,
            'quantity': item.quantity,
        } for item in order_object.items],
    }


def unwrap_orders(out_data, **kwargs):
    if not kwargs.get('many'):
        orders = []
        if 'orders' in out_data:
            for order in reversed(out_data.get('orders')):
                orders.append(helper_builder(order))
        out_data['orders_out'] = orders
    return out_data


class UserSchema(ModelSchema):
    # __nested__ = False

    class Meta:
        model = UserModel
        load_only = ('password',)
        dump_only = ('id', 'cart', 'role')

    @post_dump
    def post_dump(self, out_data, **kwargs):
        if 'cart' not in out_data:
            out_data['cart'] = []
        if 'addresses' not in out_data:
            out_data['addresses'] = []
        if not self.context.get('orders'):
            return out_data
        self.context = {}
        return unwrap_orders(out_data, **kwargs)


class UserDashboardSchema(ModelSchema):
    class Meta:
        model = UserModel
        load_only = ('password',)
        dump_only = ('id', 'cart')

    @post_dump
    def post_dump(self, out_data, **kwargs):
        return unwrap_orders(out_data, **kwargs)
