from datetime import datetime
from os import getenv
from pprint import pprint
from typing import Optional, List

import stripe
import xmltodict
from fastapi import APIRouter, status, Cookie, Security, Request, Depends
from fastapi.responses import JSONResponse

from config import STRIPE_API_KEY, shipping_rate, free_shipping
from exceptions import OutputError, PaymentNotFound
from helpers import get_image_from_cart
from languages.general_messages.messages import general_messages
from models import UserModel, PaymentModel, OrderModel
from models.base import OID
from models.user import CartItem
from resources.base import getter, updater
from schemas.payment import PaymentSchema
from templates.email.order import send_order_email

router = APIRouter(
    tags=["payments"],
)

stripe.api_key = STRIPE_API_KEY
payment_schema = PaymentSchema()


def convert_address_to_stripe(user):
    return {
        'address': {
            'city': user.addresses[user.shipping_address].city,
            'country': 'PT',
            'line1': user.addresses[user.shipping_address].street,
            'postal_code': user.addresses[user.shipping_address].postal_code
        },
        'name': f'{user.first_name} {user.last_name}'
    }


def convert_cart_to_stripe(cart, locale='pt') -> List[dict]:
    new_cart = []
    total = 0
    for cart_item in cart:
        image = get_image_from_cart(cart_item)
        temp = {
            'price_data': {
                'currency': cart_item.product.currency,
                'unit_amount': convert_to_cents(cart_item.product.price),
                'product_data': {
                    'name': cart_item.product.name,
                    # 'description': cart_item.product.description,
                    'images': [image],
                },
            },
            'quantity': cart_item.quantity
        }
        # if cart_item.product.description:
        #     temp['price_data']['product_data']['description'] = cart_item.product.description
        new_cart.append(temp)
        total += cart_item.product.price * cart_item.quantity
    new_cart.append({
        'price_data': {
            'currency': cart[0].product.currency,
            'unit_amount': convert_to_cents(shipping_rate) if total < free_shipping else 0,
            'product_data': {
                'name': general_messages.get(locale).get('shipping'),
                'description': general_messages.get(locale).get('CTT'),
            },
        },
        'quantity': 1
    })
    # new_cart.append({
    #     'name': general_messages.get(locale).get('shipping'),
    #     'currency': cart[0].product.currency,
    #     'amount': convert_to_cents(shipping_rate) if total < free_shipping else 0,
    # })
    return new_cart


def convert_to_cents(amount) -> int:
    return int(amount * 100)


@router.post("/create-payment-intent",
             status_code=status.HTTP_200_OK,
             responses={
                 422: {
                     "model": OutputError,
                     "description": "Validation Error"
                 }
             })
async def create_payment(payload: dict, current_user: UserModel = Depends(UserModel.get_current_user),
                         locale: Optional[str] = Cookie('pt')):
    # try:
    order = current_user.orders[-1] if 'order' not in payload else payload.get('order')
    payment = PaymentModel(order=order,
                           method=payload.get('method'))
    payment.save()

    send_order_email(order, payment)

    # current_user.cart = []
    # current_user.save()
    cart = current_user.cart

    if 'cart' in payload:
        cart = [CartItem(**item) for item in payload.get('cart')]

    # print(convert_cart_to_stripe(cart, locale))

    if payment.method == 'bank_transfer':
        current_user.send_bank_transfer_details(locale, order)

    elif payment.method == 'mb_reference':

        if order.status == 'done':
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={'message': 'Already paid.'})

        source = stripe.Source.create(
            type='multibanco',
            amount=convert_to_cents(float(order.amount) + float(order.shipping_cost)),
            currency='eur',
            usage='single_use',
            owner={
                'name': f'{current_user.first_name} {current_user.last_name}',
                'email': f'{current_user.email}',
            },
            metadata={
                'order_id': payment.order.id,
                'payment_id': payment.id,
                'client_reference_id': current_user.id,
            },
        )
        order.mb_reference = source.multibanco
        order.save()
        # sleep(5)
        # charge = stripe.Charge.create(
        #     amount=convert_to_cents(float(order.amount) + float(order.shipping_cost)),
        #     currency='eur',
        #     source=source.id,
        # )
        return JSONResponse(status_code=status.HTTP_200_OK, content={'mb_info': source.multibanco})

    elif payment.method == 'card':
        redirect_page = '/checkout'
        conversion_user = convert_address_to_stripe(current_user)
        customer = stripe.Customer.create(
            address=conversion_user.get('address'),
            name=conversion_user.get('name'),
            email=current_user.email,
            shipping=conversion_user,
        )
        if 'redirect_page' in payload:
            redirect_page = payload.get('redirect_page')

        checkout_session = stripe.checkout.Session.create(
            customer=customer.id,
            payment_method_types=['card'],
            # customer_email=current_user.email,
            locale=locale if locale != 'en-US' else 'en',
            # shipping_rates=['shr_1IyeZjHrKRlXLZE1pT9LmzpR'],
            # shipping_address_collection={
            #     'allowed_countries': ['PT'],
            # },
            # shipping=convert_address_to_stripe(current_user),
            line_items=convert_cart_to_stripe(cart, locale),
            metadata={
                'order_id': order.id,
                'payment_id': payment.id,
            },
            mode='payment',
            client_reference_id=current_user.id,
            success_url=f'http://localhost:8080/success/?order_id={order.id}&method=card'
            if getenv('ENVIRONMENT') == 'dev'
            else f'https://mangalibe.com/success/?order_id={order.id}&method=card',
            cancel_url=f'http://localhost:8080{redirect_page}'
            if getenv('ENVIRONMENT') == 'dev' else f'https://mangalibe.com{redirect_page}',
        )
        current_user.cart = []
        current_user.save()
        return JSONResponse(status_code=status.HTTP_200_OK, content={'id': checkout_session.id})

    # except Exception as e:
    #     return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={'detail': str(e)})


async def finish_payment(intent, payment_method='card'):
    if payment_method != 'mb_reference':
        payment = PaymentModel.get_by_id(intent.get('metadata').get('payment_id'))
        order = OrderModel.get_by_id(intent.get('metadata').get('order_id'))
        user = UserModel.get_by_id(intent.get('client_reference_id'))
    else:
        payment = PaymentModel.get_by_id(intent.get('source').get('metadata').get('payment_id'))
        order = OrderModel.get_by_id(intent.get('source').get('metadata').get('order_id'))
        user = UserModel.get_by_id(intent.get('source').get('metadata').get('client_reference_id'))
    payment.status = 'completed'
    payment.stripe_info = intent
    payment.save()
    order.status = 'done'
    order.updated_at = datetime.now()
    order.save()
    # user.cart = []
    # user.save()


@router.post("/stripe-hooks",
             status_code=status.HTTP_200_OK,
             responses={
                 422: {
                     "model": OutputError,
                     "description": "Validation Error"
                 }
             })
async def stripe_webhook(payload: dict):
    try:
        event = stripe.Event.construct_from(
            payload, stripe.api_key
        )
    except ValueError as e:
        # Invalid payload
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={'detail': str(e)})
        # Handle the event
    if event.type == 'payment_intent.succeeded':
        payment_intent = event.data.object  # contains a stripe.PaymentIntent
        # print(payment_intent)
        # print('Payment for {} succeeded'.format(payment_intent['amount']))
        # Then define and call a method to handle the successful payment intent.
        # handle_payment_intent_succeeded(payment_intent)
    elif event.type == 'checkout.session.completed':
        intent = event.data.object
        await finish_payment(intent)
    elif event.type == 'payment_method.attached':
        payment_method = event.data.object  # contains a stripe.PaymentMethod

        # Then define and call a method to handle the successful attachment of a PaymentMethod.
        # handle_payment_method_attached(payment_method)
        # ... handle other event types
    elif event.type == 'source.chargeable':
        print('chargeable')
        response = event.data.object
        charge = stripe.Charge.create(
            amount=response.amount,
            currency='eur',
            source=response.id,
        )
    elif event.type == 'charge.succeeded':
        print('charge_success')
        await finish_payment(event.data.object, payment_method='mb_reference')
    else:
        print('Unhandled event type {}'.format(event.type))

    return JSONResponse(status_code=status.HTTP_200_OK)


@router.post('/mbway-hooks',
             status_code=status.HTTP_200_OK
             )
async def mbway_webhook(request: Request):
    body = await request.body()
    # print(body.decode("utf-8"))
    obj = xmltodict.parse(body.decode("utf-8"))
    pprint(obj['soapenv:Envelope']['soapenv:Body']['ns2:financialOperationResult']['arg0'])
    return None


@router.get('/payments/{order_id}')
async def get_payment(order_id: OID, locale: Optional[str] = Cookie('pt'),
                      current_user: UserModel = Security(UserModel.get_current_user, scopes=["superuser"])):
    return await getter(PaymentModel, payment_schema, order_id, PaymentNotFound, locale)


@router.patch("/payments/{_id}", status_code=status.HTTP_200_OK,
              responses={
                  422: {
                      "model": OutputError,
                      "description": "Validation Error"
                  }
              })
async def update_payment(payload: dict, _id: OID, locale: Optional[str] = Cookie('pt'),
                         current_user: UserModel = Security(UserModel.get_current_user, scopes=["superuser"])):
    return await updater(PaymentModel, payment_schema, _id, payload, PaymentNotFound, locale)
