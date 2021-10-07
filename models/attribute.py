import asyncio
from typing import List

from mongoengine import Document, StringField, ListField, signals, EmbeddedDocument, \
    EmbeddedDocumentField, DynamicField

from helpers import convert_to_slug
from models.base import Base, OID
from models.language import Language


class OptionsModel(EmbeddedDocument):
    name = DynamicField(required=True)
    image: str = StringField(required=False, default="")
    color: str = StringField(required=False, default="")


class AttributeModel(Document, Base):
    meta = {
        'collection': 'attributes'
    }
    name: str = StringField(required=True, max_length=70)
    options: List['OptionsModel'] = ListField(EmbeddedDocumentField(OptionsModel))
    slug: str = StringField(required=False, null=True)
    translations: List[str] = ListField(StringField(required=False), required=False, default=['name'])

    @classmethod
    def post_init(cls, _, document):
        if not document.slug:
            document.slug = convert_to_slug(document.name)

    @staticmethod
    async def create_option(option):
        return OptionsModel(**option)

    async def add_options(self, options: List[dict]):
        tasks = []
        for option in options:
            task = asyncio.ensure_future(self.create_option(option))
            tasks.append(task)
        created_options = await asyncio.gather(*tasks)
        self.options += created_options
        self.save()

    async def add_image(self, image, option_name, **kwargs):
        for option in self.options:
            if option.name == option_name:
                option.image = image
                break
        self.save()

    # @staticmethod
    # async def clear_options_translations(_id: OID, index: int, option: OptionsModel, languages: List[Language]):
    #     for lang in languages:
    #         lang.strings.pop(f'{obj.id}_options_{index}': option.get('name'), None)

    @staticmethod
    def inject_after_clear(_id: OID, index: int, option: dict, language, locale: str):
        language.add_strings({
            f'{_id}_options_{index}': option.get('name') if locale == language.prefix else ''
            if not language.strings.get(f'{_id}_options_{index}')
            else language.strings.get(f'{_id}_options_{index}')
        })
        language.save()

    @classmethod
    async def inject_options(cls, obj, payload, locale):
        languages = Language.get_all()
        options_out = []
        old_length = len(obj.options)
        new_length = len(payload.get('options'))
        if old_length > new_length:
            indexes_to_pop = range(old_length, new_length - 1, -1)
            for lang in languages:
                for x in indexes_to_pop:
                    lang.strings.pop(f'{obj.id}_options_{x}', None)

        for index, option in enumerate(payload.get('options')):
            for language in languages:
                if isinstance(option.get('name'), str):
                    cls.inject_after_clear(obj.id, index, option, language, locale)
            options_out.append(OptionsModel(**option))
        obj.options = options_out
        return obj


signals.post_init.connect(AttributeModel.post_init, sender=AttributeModel)

if __name__ == '__main__':
    c = AttributeModel(
        name='Color',
    )
    asyncio.run(c.add_options([
        {
            'value': 'Yellow',
        },

    ]))

    c.save()
