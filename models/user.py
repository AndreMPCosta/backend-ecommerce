from os import getenv
from uuid import uuid4

from fastapi import Depends, HTTPException, status
from fastapi.security import SecurityScopes
from jose import JWTError
from jose.jwt import decode
from mongoengine import EmbeddedDocument, StringField, Document, EmailField, ReferenceField, IntField, \
    EmbeddedDocumentListField, signals, ListField, BooleanField, DictField

from auth import verify_password, oauth2_scheme, SECRET_KEY, ALGORITHM, TokenData, get_password_hash
from config import domain, IBAN
from helpers import send_email
from helpers.db_helper_v2 import get_one
from invoice import currencies
from languages.errors.messages import translations
from models.base import Base
from templates.email.reset_password_email import reset_template
from templates.email.verification_email import template

roles = ('regular', 'superuser')


class AddressModel(EmbeddedDocument):
    street: str = StringField(required=True, default="")
    city: str = StringField(required=False, default="")
    postal_code: str = StringField(required=False, default="")


class CartItem(EmbeddedDocument):
    product = ReferenceField('ProductModel')
    attributes = ListField(DictField())
    quantity: int = IntField(required=False, default=1, min_value=1)


class UserModel(Document, Base):
    meta = {
        'collection': 'users',
    }
    first_name: str = StringField(required=True, max_length=70, min_length=1)
    last_name: str = StringField(required=True, max_length=70, min_length=1)
    email: str = EmailField(required=True)
    password: str = StringField(required=True, max_length=100, min_length=4)
    addresses = EmbeddedDocumentListField('AddressModel', required=False)
    nif: str = StringField(required=False, min_length=0, max_length=9, default='')
    cart = EmbeddedDocumentListField(CartItem, default=[], required=False)
    role: str = StringField(choices=roles, default='regular')
    orders = ListField(ReferenceField('OrderModel'), default=[], required=False)
    active: bool = BooleanField(default=True)
    activation_token: str = StringField(default='')
    shipping_address: int = IntField(default=0)
    reset_password_token: str = StringField(default='')
    preferred_language: str = StringField(default='pt')

    @classmethod
    def post_init(cls, _, document):
        if not document.id:
            document.password = get_password_hash(document.password)

    @classmethod
    def get_by_email(cls, email):
        return get_one(cls, {'email': email})

    # Send User Verification Email
    def send_verification_email(self, locale):
        self.activation_token = uuid4().hex
        formatted_template = template.get(locale).format(
            name=self.first_name,
            to_frontend_link=f'https://{domain}/activate/{self.activation_token}')
        send_email({
            'subject': 'Verifique o seu endereço de email' if locale == 'pt' else 'Verify your email address',
            'message': formatted_template
        },
            to=self.email)
        self.save()

    # Send Bank Transfer Details:
    def send_bank_transfer_details(self, locale, order):
        from templates.email.bank_transfer_email import translations, html
        translations_object = translations.get(locale)
        formatted_template = html.format(
            greeting=translations_object.get('greeting').format(f'{self.first_name} {self.last_name}'),
            line_1=translations_object.get('line_1'),
            iban=IBAN,
            amount=translations_object.get('amount'),
            amount_value=str(format(float(order.shipping_cost) + float(order.amount), ".2f")),
            currency=currencies.get(order.currency),
            line_2=translations_object.get('line_2').format(order),
            button_label=translations_object.get('button_label'),
            order_url=f'http://localhost:8080/user/order_history?order_id={order.id}' if getenv('ENVIRONMENT') == 'dev'
            else f'https://{domain}/user/order_history?order_id={order.id}'
        )
        send_email({
            'subject': 'Detalhes Transferência Bancária' if locale == 'pt' else 'Bank Transfer Details',
            'message': formatted_template
        },
            to=self.email)

    # Send User Reset Password Email
    def send_reset_email(self, locale):
        self.reset_password_token = uuid4().hex
        formatted_template = reset_template.get(locale).format(
            link=f'https://{domain}/reset-password/{self.reset_password_token}')
        send_email({
            'subject': 'Reset de Password em Loja Mangalibe' if locale == 'pt'
            else 'Password Reset for Mangalibe Store',
            'message': formatted_template
        },
            to=self.email)
        self.save()

    # Cart Methods

    async def add_item(self, payload: dict):
        attributes = payload.get('attributes') if 'attributes' in payload else []
        cart_item = CartItem(product=payload.get('product'), attributes=attributes)
        if cart_item.product not in [item.product for item in self.cart]:
            self.cart.append(cart_item)
        else:
            from models.product import ProductModel
            p = ProductModel.get_by_id(payload.get('product'))
            items = self.cart.filter(product=p)
            if attributes in [item.attributes for item in items]:
                item = items.filter(attributes=cart_item.attributes).first()
                item.quantity += 1
            else:
                self.cart.append(cart_item)
        self.save()

    async def delete_item(self, payload: dict):
        from models.product import ProductModel
        p = ProductModel.get_by_id(payload.get('product'))
        # item = self.cart.filter(product=p).first()
        self.cart = self.cart.exclude(product=p, attributes=payload.get('attributes') if 'attributes'
                                                                                         in payload else [])
        self.save()

    async def update_quantity(self, payload: dict):
        from models.product import ProductModel
        p = ProductModel.get_by_id(payload.get('product'))
        self.cart.filter(product=p, attributes=payload.get('attributes') if 'attributes'
                                                                            in payload else []). \
            update(quantity=payload.get('quantity'))
        self.save()

    # Address Methods

    async def add_addresses(self, payload: dict):
        for address in payload.get('addresses'):
            temp_address = AddressModel(**address)
            self.addresses.append(temp_address)
        self.save()

    async def update_address(self, payload: dict, index: int):
        self.addresses[index] = AddressModel(**payload)
        self.save()

    async def delete_address(self, payload: dict):
        del self.addresses[payload.get('index')]
        self.save()

    async def create_order(self):
        from models.order import OrderModel
        self.orders.append(OrderModel(user=self, items=self.cart))
        self.save()

    # Auth
    @classmethod
    def authenticate_user(cls, email: str, password: str):
        user = cls.get_by_email(email)
        if not user:
            return False
        if not verify_password(password, user.password):
            return False
        return user

    @classmethod
    async def get_current_user(cls, security_scopes: SecurityScopes, token: str = Depends(oauth2_scheme)):
        if security_scopes.scopes:
            authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
        else:
            authenticate_value = f"Bearer"
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            email: str = payload.get("sub")
            if email is None:
                raise credentials_exception
            token_scopes = payload.get("scopes", [])
            token_data = TokenData(scopes=token_scopes, email=email)
        except JWTError:
            raise credentials_exception
        user = cls.get_by_email(email=token_data.email)
        if user is None:
            raise credentials_exception
        for scope in security_scopes.scopes:
            if scope not in token_data.scopes:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=translations.get('en-US').get('no_permissions'),
                    headers={"WWW-Authenticate": authenticate_value},
                )
        return user


signals.post_init.connect(UserModel.post_init, sender=UserModel)

if __name__ == '__main__':
    u = UserModel.get_by_email('random_email@domain.com')
    u.send_verification_email('pt')
