from calendar import month_name
from locale import setlocale, LC_ALL

from jinja2 import Template
from weasyprint import HTML

from helpers import send_email

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
        'title': 'Fatura # {}',
        'subject': 'Fatura Mangalibe - {} ',
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
    },
    'en-US': {
        'title': 'Invoice # {}',
        'subject': 'Invoice Mangalibe - {} ',
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
    }
}


def get_date(date, locale):
    setlocale(LC_ALL, mapping.get(locale))
    date_now = date
    return f'{month_name[date_now.month].capitalize()} {date_now.day}, {date_now.year}'


def generate_invoice(order, payment, locale):
    with open("invoice/invoice.html", encoding="utf-8") as html_template:
        html = html_template.read()
        temp = Template(html)
    # Render Jinja blocks
    out = temp.render(
        title=translations.get(locale).get('title').format(order.number),
        user=order.user,
        order=order,
        payment_method=translations.get(locale).get(payment.method),
        translations=translations.get(locale),
        date=get_date(order.updated_at, locale),
        currencies=currencies
    )
    HTML(string=out).write_pdf(f'invoice/invoices/{order.id}.pdf')
    # from_string(out, f'invoice/invoices/{order.id}.pdf')


def send_invoice(order, payment):
    with open("invoice/invoice.html", encoding="utf-8") as html_template:
        html = html_template.read()
        temp = Template(html)
    # Render Jinja blocks
    out = temp.render(
        title=translations.get(order.user.preferred_language).get('title').format(order.id),
        user=order.user,
        order=order,
        payment_method=translations.get(order.user.preferred_language).get(payment.method),
        translations=translations.get(order.user.preferred_language),
        date=get_date(order.updated_at, order.user.preferred_language),
        currencies=currencies
    )
    send_email({'subject': translations.get(order.user.preferred_language).get('subject').
               format(order.updated_at.strftime("%d/%m/%Y")),
                'message': out},
               filename=f'invoice/invoices/{order.id}.pdf' if order.user.nif else None,
               to=order.user.email)


if __name__ == '__main__':
    from models.user import UserModel
    from models.payment import PaymentModel

    user_test = UserModel.get_by_email('random_email@awesomedomain.com')
    order_test = user_test.orders[-1]
    payment_test = PaymentModel.get_by_custom_field('order', order_test.id)
    generate_invoice(order_test, payment_test, 'pt')
