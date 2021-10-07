from calendar import month_name
from locale import setlocale, LC_ALL
from os import getenv

from jinja2 import Template

from config import from_email, domain
from models import OrderModel, PaymentModel
from models.base import OID

mapping = {
    'pt': 'pt_PT',
    'en-US': 'en_US'
}

currencies = {
    'eur': '€',
    'usd': '$'
}

translations = {
    'pt': {
        'subject': 'Mangalibe - Encomenda # {} ',
        'line_1': 'Será notificado quando a sua encomenda for enviada. Enquanto espera, '
                  'porque não visitar a nossa página de Instagram?',
        'amount': 'Valor:',
        'line_2': 'Se possível incluir nos detalhes da transferência (se usar homebanking, por exemplo), a seguinte '
                  'referência de encomenda: {}',
        'button_label': 'Ver detalhes da encomenda',
        'invoice': 'Fatura',
        'date': 'Data',
        'payment_method': 'Método de Pagamento',
        'card': 'Cartão de Crédito',
        'bank_transfer': 'Transferência Bancária',
        'mbway': 'MbWay',
        'mb_reference': 'Referências Multibanco',
        'quantity': 'Quantidade',
        'price': 'Preço',
        'item': 'Produto',
        'taxes': 'IVA 23',
        'name': 'Nome',
        'shipping': 'Envio',
        'street': 'Rua',
        'city': 'Cidade',
        'postal_code': 'Código Postal',
        'order_status': 'VERIFICAR ESTADO DA ENCOMENDA',
        'thanks': 'Obrigado',
        'order': 'Encomenda',
        'order_date': 'Data Encomenda',
        'shipping_method': 'Método de Envio',
        'shipping_address': 'Morada Envio',
        'order_summary': 'Resumo da Encomenda',
        'payment_details': 'Detalhes Pagamento',
        'payments': {
            'card': 'Cartão Crédito',
            'bank_transfer': 'Transferência Bancária',
            'mbway': 'MBWAY',
            'mb_reference': 'Referências Multibanco'
        },
        'need_help': 'Precisa de ajuda? Tem alguma dúvida?'

    },
    'en-US': {
        'subject': 'Mangalibe - Order # {} ',
        'line_1': "We'll let you know when your order is on the way. Why not add us on IG while you're waiting?",
        'amount': 'Amount:',
        'line_2': 'If possible include in the transfer comments your order reference: {}',
        'button_label': 'View order details',
        'invoice': 'Invoice',
        'date': 'Date',
        'payment_method': 'Payment Method',
        'card': 'Credit Card',
        'bank_transfer': 'Bank Transfer',
        'mbway': 'MbWay',
        'mb_reference': 'ATM References',
        'quantity': 'Quantity',
        'price': 'Price',
        'item': 'Item',
        'taxes': 'Taxes 23',
        'name': 'Name',
        'shipping': 'Shipping',
        'street': 'Street',
        'city': 'City',
        'postal_code': 'Postal Code',
        'order_status': 'CHECK ORDER STATUS',
        'thanks': 'Thanks',
        'order': 'Order',
        'order_date': 'Order Date',
        'shipping_method': 'Shipping Method',
        'shipping_address': 'Shipping Address',
        'order_summary': 'Order Summary',
        'payment_details': 'Payment Details',
        'payments': {
            'card': 'Credit Card',
            'bank_transfer': 'Bank Transfer',
            'mbway': 'MBWAY',
            'mb_reference': 'ATM References'
        },
        'need_help': 'Need help? Hit us up.'
    }
}


def get_date(date, locale):
    setlocale(LC_ALL, mapping.get(locale))
    date_now = date
    return f'{month_name[date_now.month].capitalize()} {date_now.day}, {date_now.year}'


def send_order_email(order, payment, p="templates/email/order.html"):
    from helpers import get_image_from_cart, send_email
    with open(p, encoding="utf-8") as html_template:
        html = html_template.read()
        temp = Template(html)
    # Render Jinja blocks
    language = order.user.preferred_language
    out = temp.render(
        user=order.user,
        order=order,
        payment_method=translations.get(language).get(payment.method),
        translations=translations.get(language),
        date=get_date(order.updated_at, language),
        currencies=currencies,
        get_image=get_image_from_cart,
        domain=domain if getenv('ENVIRONMENT') == 'prod' else 'localhost:8080',
        order_url='http://{}/user/order_history?order_id={}' if getenv('ENVIRONMENT') == 'dev'
        else 'https://{}/user/order_history?order_id={}',
        support_email=from_email
    )
    # with open("out.html", 'w') as f:
    #     f.write(out)
    send_email({'subject': translations.get(order.user.preferred_language).get('subject').
               format(order.id),
                'message': out},
               to=order.user.email)


if __name__ == '__main__':
    example_order = OrderModel.get_by_id(OID('60e5d76e3c5dce5679eb065d'))
    example_payment = PaymentModel.get_by_custom_field('order', OID('60e5d76e3c5dce5679eb065d'))
    send_order_email(example_order, example_payment, p="order.html")
