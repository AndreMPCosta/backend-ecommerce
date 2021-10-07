from datetime import datetime
from os import getcwd
from os.path import join
from typing import Optional

from fastapi import Depends, Cookie, APIRouter, status, Security
from fastapi.responses import JSONResponse, FileResponse

from exceptions import OutputError, OrderNotFound, PaymentNotFound
from invoice import generate_invoice, send_invoice
from models import UserModel, OrderModel, PaymentModel
from models.base import OID
from resources.base import creator, getter, updater
from schemas.order import OrderSchema

router = APIRouter(
    tags=["orders"],
)

order_schema = OrderSchema()
order_list_schema = OrderSchema(many=True)
order_schema_individual = OrderSchema(many=False)


@router.post("/orders",
             status_code=status.HTTP_201_CREATED,
             responses={
                 422: {
                     "model": OutputError,
                     "description": "Validation Error"
                 }
             })
async def create_order(payload: dict, locale: Optional[str] = Cookie('pt'),
                       current_user: UserModel = Depends(UserModel.get_current_user)):
    order = {'user': current_user.id,
             'shipping_address': payload.get('shipping_address'),
             'billing_address': payload.get('billing_address'),
             'payment_method': payload.get('payment_method'),
             }
    if 'nif' in payload:
        order['nif'] = payload.get('nif')
    return await creator(OrderModel, order_schema, order, Exception, locale)


@router.patch("/orders/cancel",
              status_code=status.HTTP_200_OK,
              responses={
                  422: {
                      "model": OutputError,
                      "description": "Validation Error"
                  }
              })
async def cancel_order(payload: dict, locale: Optional[str] = Cookie('pt'),
                       current_user: UserModel = Depends(UserModel.get_current_user)):
    _id = payload.get('id')
    if OrderModel.get_by_id(_id).status == 'cancelled':
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST,
                            content={
                                "message": "Order is already cancelled."})
    if current_user.role != 'superuser':
        if not any(str(x.id) == str(_id) for x in current_user.orders):
            return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED,
                                content={
                                    "message": "Unauthorized"})
    return await updater(OrderModel, order_schema, _id, {'status': 'cancelled'}, OrderNotFound, locale)


@router.get("/orders", status_code=status.HTTP_200_OK,
            responses={
                422: {
                    "model": OutputError,
                    "description": "Validation Error"
                }
            })
async def get_orders(locale: Optional[str] = Cookie('pt'), page: Optional[int] = None,
                     current_user: UserModel = Security(UserModel.get_current_user, scopes=["superuser"])):
    if not page:
        orders = OrderModel.get_all(field='number', reverse=True)
    else:
        orders = OrderModel.limit((page - 1) * 20 if page == 1 else (page - 1) * 20 + 1, page * 20 + 1, '-number')
    return order_list_schema.dump(orders)


@router.get("/orders/total", status_code=status.HTTP_200_OK,
            responses={
                422: {
                    "model": OutputError,
                    "description": "Validation Error"
                }
            })
async def get_orders(locale: Optional[str] = Cookie('pt'),
                     current_user: UserModel = Security(UserModel.get_current_user, scopes=["superuser"])):
    number_of_orders = OrderModel.count_all()
    return {'total_orders': number_of_orders}


@router.get("/orders/{_id}", status_code=status.HTTP_200_OK,
            responses={
                422: {
                    "model": OutputError,
                    "description": "Validation Error"
                }
            })
async def get_order(_id: OID, locale: Optional[str] = Cookie('pt'),
                    current_user: UserModel = Security(UserModel.get_current_user, scopes=["superuser"])):
    return await getter(OrderModel, order_schema_individual, _id, OrderNotFound, locale)


@router.patch("/orders/{_id}", status_code=status.HTTP_200_OK,
              responses={
                  422: {
                      "model": OutputError,
                      "description": "Validation Error"
                  }
              })
async def update_order(payload: dict, _id: OID, locale: Optional[str] = Cookie('pt'),
                       current_user: UserModel = Security(UserModel.get_current_user, scopes=["superuser"])):
    return await updater(OrderModel, order_schema, _id, payload, OrderNotFound, locale)


@router.post("/orders/generate-invoice",
             status_code=status.HTTP_201_CREATED,
             responses={
                 422: {
                     "model": OutputError,
                     "description": "Validation Error"
                 }
             })
async def create_invoice(payload: dict, locale: Optional[str] = Cookie('pt'),
                         current_user: UserModel = Security(UserModel.get_current_user, scopes=["superuser"])):
    try:
        order = OrderModel.get_by_id(payload.get('id'))
        if not order:
            raise OrderNotFound
        payment = PaymentModel.get_by_custom_field('order', payload.get('id'))
        if not payment:
            raise PaymentNotFound
        generate_invoice(order, payment, order.user.preferred_language)
        order.is_invoice_generated = True
        order.last_updated_at_invoice = datetime.now()
        order.save()
    except OrderNotFound:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND,
                            content={
                                "message": "Ordem não encontrada." if locale == 'pt' else
                                "Order not found."})
    except PaymentNotFound:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND,
                            content={
                                "message": "Pagamento não encontrado." if locale == 'pt' else
                                "Payment not found."})
    return JSONResponse(status_code=status.HTTP_200_OK, content={'message': 'Fatura gerada com sucesso.'
    if locale == 'pt' else
    'Invoice created successfully.'})


@router.post("/orders/send-invoice",
             status_code=status.HTTP_200_OK,
             responses={
                 422: {
                     "model": OutputError,
                     "description": "Validation Error"
                 }
             })
async def email_invoice(payload: dict, locale: Optional[str] = Cookie('pt'),
                        current_user: UserModel = Security(UserModel.get_current_user, scopes=["superuser"])):
    try:
        order = OrderModel.get_by_id(payload.get('id'))
        if not order:
            raise OrderNotFound
        payment = PaymentModel.get_by_custom_field('order', payload.get('id'))
        if not payment:
            raise PaymentNotFound
        send_invoice(order, payment)
    except OrderNotFound:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND,
                            content={
                                "message": "Ordem não encontrada." if locale == 'pt' else
                                "Order not found."})
    except PaymentNotFound:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND,
                            content={
                                "message": "Pagamento não encontrado." if locale == 'pt' else
                                "Payment not found."})
    return JSONResponse(status_code=status.HTTP_200_OK, content={'message': 'Email enviado com sucesso.'
    if locale == 'pt' else
    'Email sent successfully.'})


@router.get("/orders/invoices/{_id}", status_code=status.HTTP_200_OK,
            responses={
                422: {
                    "model": OutputError,
                    "description": "Validation Error"
                }
            })
async def get_invoice(_id: OID, current_user: UserModel = Security(UserModel.get_current_user, scopes=["superuser"])):
    return FileResponse(join(getcwd(), "invoice/invoices/", f"{_id}.pdf"))
