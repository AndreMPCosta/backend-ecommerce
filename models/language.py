from typing import List

from mongoengine import Document, StringField, DictField

from helpers.db_helper_v2 import get_one, get_all
from languages import languages


class Language(Document):
    prefix = StringField(required=True, default="", null=True)
    strings = DictField(required=False, default={})

    meta = {
        'collection': 'languages'
    }

    @classmethod
    def get_language(cls, prefix: str) -> "Language":
        return get_one(cls, {'prefix': prefix})

    def add_strings(self, strings: dict, internal=False):
        self.strings.update(strings)
        if not internal:
            languages.update_strings(self.prefix, strings)
        self.save()

    @classmethod
    def get_all(cls) -> List["Language"]:
        return get_all(cls, 'prefix')
