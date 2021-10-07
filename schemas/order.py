from marshmallow import post_dump
from marshmallow_mongoengine import ModelSchema

from models import OrderModel, UserModel, ProductModel


class OrderSchema(ModelSchema):
    # __nested__ = False

    class Meta:
        model = OrderModel

    @post_dump
    def convert_user_id(self, out_data, **kwargs):
        user = UserModel.get_by_id(out_data.get("user"))
        shipping_address = out_data.get('shipping_address')
        out_shipping_address = {}
        # for k in shipping_address._fields.keys():
        #     out_shipping_address.update({k: getattr(shipping_address, k)})
        out_data['user'] = {'name': f'{user.first_name} {user.last_name}',
                            'email': user.email,
                            'shipping_address': shipping_address}

        if not kwargs.get('many'):
            for item in out_data.get('items'):
                product = ProductModel.get_by_id(item.get('product'))
                item['out_product'] = {
                    'image': product.image,
                    'name': product.name,
                    'price': product.price,
                    'currency': product.currency,
                }
                item['total'] = product.price * item.get('quantity')
        return out_data
