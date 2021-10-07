from typing import Type, Union

from bson import ObjectId
from bson.errors import InvalidId

from helpers.db_helper_v2 import get_one, get_all, count, find, limit, count_all

from pydantic.types import T


class OID(str):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        try:
            return ObjectId(str(v))
        except InvalidId:
            raise ValueError("Not a valid ObjectId")


class Base:

    @classmethod
    def get_by_name(cls, name):
        return get_one(cls, {'name': name})

    @classmethod
    def get_by_id(cls: Type[T], _id: Union[OID, ObjectId]) -> T:
        return get_one(cls, {'id': _id})

    @classmethod
    def get_by_custom_field(cls, name: str, value):
        return get_one(cls, {name: value})

    @classmethod
    def get_by_slug(cls, slug: str):
        return get_one(cls, {'slug': slug})

    @classmethod
    def get_all(cls, field: str = 'name', reverse=False):
        return get_all(cls, field, reverse)

    @classmethod
    def count(cls, payload: dict):
        return count(cls, payload)

    @classmethod
    def count_all(cls):
        return count_all(cls)

    @classmethod
    def find(cls, payload: dict):
        return find(cls, payload)

    @classmethod
    def limit(cls, start:  Union[int, None] = None, stop:  Union[int, None] = None, order_by: str = None):
        return limit(cls, start, stop, order_by)

    # def add_translation(self, lang: str, payload: dict):
    #     find_lang = await Language.get_language(lang)
    #     await find_lang.add_strings(payload)
    #     await self.save()
