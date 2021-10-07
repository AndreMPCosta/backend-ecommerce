# define Python user-defined exceptions
from pydantic import PydanticValueError, BaseModel


class Error(PydanticValueError):
    """Base class for other exceptions"""
    code: str = ''
    msg_template: str = ''
    holder = ''

    def message(self, *args):
        return self.msg_template.format(*args if args else self.holder)


class OutputError(BaseModel):
    msg_template: str = ''


class GeneralError(Error):
    code = 'general_error'
    msg_template = "Unexpected error."


class LanguageExists(BaseModel):
    code = 'language_exists'
    msg_template = "The language '{}' already exists."


class CategoryNotUnique(Error):
    code = 'category_not_unique'
    msg_template = "The category '{}' already exists."


class CategoryNotFound(Error):
    code = 'category_not_found'
    msg_template = "The category '{}' was not found."


class LanguageNotAvailable(Error):
    code = 'language_not_available'
    msg_template = "The language '{}' is not available."


class ProductTypeNotUnique(Error):
    code = 'product_type_not_unique'
    msg_template = "The product type '{}' already exists."


class ProductTypeNotFound(Error):
    code = 'product_type_not_found'
    msg_template = "The product type '{}' was not found."


class AttributeNotUnique(Error):
    code = 'attribute_not_unique'
    msg_template = "The attribute '{}' already exists."


class AttributeNotFound(Error):
    code = 'attribute_not_found'
    msg_template = "The attribute '{}' was not found."


class ProductNotUnique(Error):
    code = 'product_not_unique'
    msg_template = "The product '{}' already exists."


class ProductNotFound(Error):
    code = 'product_not_found'
    msg_template = "The product '{}' was not found."


class UserNotUnique(Error):
    code = 'user_not_unique'
    msg_template = "The user '{}' already exists."


class UserNotFound(Error):
    code = 'user_not_found'
    msg_template = "The user '{}' was not found."


class OrderNotFound(Error):
    code = 'order_not_found'
    msg_template = "The order '{}' was not found."


class PaymentNotFound(Error):
    code = 'payment_not_found'
    msg_template = "The payment with the order id '{}' was not found."


class CartEmpty(Error):
    code = 'cart_empty'
    msg_template = "Can't create order with an empty cart."
