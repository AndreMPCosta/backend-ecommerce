import asyncio
from datetime import datetime
from os import mkdir, listdir, remove
from os.path import exists, join, isfile
from shutil import copyfileobj
from typing import List, Callable, Union

from bson import ObjectId
from fastapi import status, UploadFile
from fastapi.responses import JSONResponse
from marshmallow import ValidationError

from auth import get_password_hash
from config import available_languages
from exceptions import Error
from helpers.db_helper_v2 import find
from image import ResponsiveImage
from languages import languages
from languages.errors.messages import translations
from languages.general_messages.messages import general_messages
from models.base import OID
from models.language import Language


def contains(element, *typ):
    for val in element:
        if isinstance(val, typ):
            return True
    return False


async def translations_helper(field: str, element, locale: str):
    if (isinstance(getattr(element, field), str) or not getattr(element, field)
            and not isinstance(getattr(element, field), list)):
        tasks = []
        for lang in available_languages:
            task = asyncio.ensure_future(lang_iterator(lang, locale, element, field))
            tasks.append(task)
        await asyncio.gather(*tasks)
    else:
        values = [value.name for value in getattr(element, field)]
        if contains(values, float, int):
            pass
        else:
            for index, child_element in enumerate(getattr(element, field)):
                tasks = []
                for lang in available_languages:
                    task = asyncio.ensure_future(lang_iterator_with_dict(lang, locale,
                                                                         element, field, child_element, index))
                    tasks.append(task)
                await asyncio.gather(*tasks)


async def lang_iterator(lang, locale, element, field):
    db_language = Language.get_language(lang)
    if lang == locale:
        temp_translations = {f'{element.id}_{field}': getattr(element, field)}
    else:
        temp_translations = {f'{element.id}_{field}': None}
    db_language.add_strings(temp_translations)
    languages.update_strings(lang, temp_translations)


async def lang_iterator_with_dict(lang, locale, element, field, child_element, index):
    db_language = Language.get_language(lang)
    if child_element:
        if lang == locale:
            temp_translations = {
                f'{element.id}_{field}_{index}': child_element.name}
        else:
            temp_translations = {f'{element.id}_{field}_{index}': ""}
        db_language.add_strings(temp_translations)
        languages.update_strings(lang, temp_translations)


async def getter(model, schema, _id, exception, locale):
    try:
        if model.__name__ != 'PaymentModel':
            obj = model.get_by_id(_id)
        else:
            obj = model.get_by_custom_field('order', _id)
        if not obj:
            raise exception
    except exception as e:
        e.msg_template = translations.get(locale).get(e.code) if translations.get(locale).get(e.code) \
            else e.msg_template
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND,
                            content={"error": e.message(_id)})
    except Error as e:
        e.msg_template = translations.get(locale).get(e.code) if translations.get(locale).get(e.code) \
            else e.msg_template
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"error": "Unexpected error"})
    return schema.dump(obj)


async def creator(model, schema, element, exception, locale, late_fields: dict = None):
    try:
        obj: model = schema.load(element, partial=True)
        if late_fields:
            for field, value in late_fields.items():
                setattr(obj, field, value)
        if model.__name__ not in ['UserModel', 'OrderModel']:
            if model.get_by_name(obj.name):
                raise exception
        elif model.__name__ == 'UserModel':
            if model.get_by_email(obj.email):
                raise exception
            # obj.send_verification_email(locale)
        else:
            pass
        obj.save()
        tasks = []
        if hasattr(obj, 'translations'):
            for field in obj.translations:
                task = asyncio.ensure_future(translations_helper(field, obj, locale))
                tasks.append(task)
            await asyncio.gather(*tasks)
        return schema.dump(obj)
    except ValidationError as e:
        return JSONResponse(status_code=400, content=e.messages)
    except exception as e:
        e.msg_template = translations.get(locale).get(e.code) if translations.get(locale).get(e.code) \
            else e.msg_template
        return JSONResponse(status_code=status.HTTP_409_CONFLICT,
                            content={
                                "error": e.message(element.get('name' if model.__name__ != 'UserModel' else 'email'))
                            })
    except Error as e:
        e.msg_template = translations.get(locale).get(e.code) if translations.get(locale).get(e.code) \
            else e.msg_template
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            content={"error": "Unexpected error"})


async def updater(model, schema, _id, payload: dict, exception, locale,
                  watch_fields: List[str] = None, slot: Callable = None, ignore_fields=None, force_model: dict = None):
    if ignore_fields is None:
        ignore_fields = []
    try:
        obj: model = model.get_by_id(_id)
        if model.__name__ == 'PaymentModel' and 'status' in payload:
            if payload.get('status') == 'completed':
                obj.order.status = 'done'
            else:
                obj.order.status = 'awaiting_payment'
            obj.order.save()
        if not obj:
            raise exception
        if model.__name__ == 'UserModel' and 'password' in payload:
            setattr(obj, 'password', get_password_hash(payload.get('password')))
            payload.pop('password', None)
        if model.__name__ == 'UserModel' and 'addresses' in payload:
            from models.user import AddressModel
            payload['addresses'] = [AddressModel(**address) for address in payload.get('addresses')]
        if model.__name__ == 'OrderModel' and 'status' in payload:
            for item in obj.items:
                item.product.update_quantity(item, replenish_stock=True)
                item.product.save()
        for k, v in payload.items():
            if slot:
                obj = await slot(obj, payload, locale)
            if watch_fields:
                if k in watch_fields:
                    if type(v) == list:
                        temp = []
                        for item in v:
                            temp.append(ObjectId(item))
                        v = temp
                    else:
                        v = ObjectId(v)
            if k not in ignore_fields:
                setattr(obj, k, v)
        if force_model:
            for field, _class in force_model.items():
                setattr(obj, field, _class.get_by_id(payload.get(field)))
        obj.save()
        # if model.__name__ == 'ProductModel' and 'product_type' in payload:
        #     obj.product_type_update()
    except exception as e:
        e.msg_template = translations.get(locale).get(e.code) if translations.get(locale).get(e.code) \
            else e.msg_template
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND,
                            content={"error": e.message(_id)})
    except Error as e:
        e.msg_template = translations.get(locale).get(e.code) if translations.get(locale).get(e.code) \
            else e.msg_template
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"error": "Unexpected error"})
    return schema.dump(obj)


async def deleter(model, _id, exception, locale, success_message, is_product=False):
    try:
        obj: model = model.get_by_id(_id)
        if not obj:
            raise exception
        if is_product:
            obj.helper_delete()
        for language in Language.get_all():
            for field in obj.translations:
                language.strings.pop(f'{obj.id}_{field}')
            language.save()
        obj.delete()
    except exception as e:
        e.msg_template = translations.get(locale).get(e.code) if translations.get(locale).get(e.code) \
            else e.msg_template
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND,
                            content={"error": e.message(_id)})
    except Error as e:
        e.msg_template = translations.get(locale).get(e.code) if translations.get(locale).get(e.code) \
            else e.msg_template
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"error": "Unexpected error"})
    return {'message': general_messages.get(locale).get(success_message).format(obj.name)}


async def finder(model, payload, locale):
    try:
        objs = find(model, payload)
        return objs
    except Error as e:
        e.msg_template = translations.get(locale).get(e.code) if translations.get(locale).get(e.code) \
            else e.msg_template
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"error": "Unexpected error"})


async def uploader(model, model_name: str, _id: Union[OID, None], file: UploadFile, option=None, attr_name=None,
                   option_name=None):
    path = f'./static/{model_name}/{_id}' if not option else f'./static/{model_name}/{_id}/{option}'
    fingerprint = datetime.now().strftime("%d_%m_%Y_%H_%M_%S_")
    if attr_name and option_name:
        path = f'./static/{model_name}/{_id}/{attr_name}/{option_name}'
    if not exists(path) and not option and not attr_name:
        mkdir(path)
    elif not exists(path) and option:
        if not exists(f'./static/{model_name}/{_id}'):
            mkdir(f'./static/{model_name}/{_id}')
        if not exists(path):
            mkdir(path)
    elif not exists(path) and attr_name:
        if not exists(f'./static/{model_name}/{_id}'):
            mkdir(f'./static/{model_name}/{_id}')
        if not exists(f'./static/{model_name}/{_id}/{attr_name}'):
            mkdir(f'./static/{model_name}/{_id}/{attr_name}')
        if not exists(path):
            mkdir(path)
    else:
        for f in listdir(path):
            if isfile(join(path, f)):
                remove(join(path, f))
    extension = file.filename.rsplit('.', 1)[1]
    with open(f"{path}/{fingerprint}image.{extension}", "wb") as buffer:
        copyfileobj(file.file, buffer)
    responsive_image = ResponsiveImage(original_image=f"{path}/{fingerprint}"
                                                      f"image.{extension}",
                                       fingerprint=fingerprint)
    await responsive_image.create()
    obj = model.get_by_id(_id)
    if not obj:
        return {
            'message': f"The id '{_id}' was not found."
        }
    elif not attr_name:
        await obj.add_image(f'{path.replace("./", "")}/{fingerprint}'
                            f'image.{extension}', option_name=option)
    else:
        await obj.add_attribute_image(f'{path.replace("./", "")}/{fingerprint}'
                                      f'image.{extension}', attr_name, option_name)
    return {"message": 'success'}


async def settings_uploader(file: UploadFile, settings_video: bool):
    from models.settings import SettingsModel
    settings = SettingsModel.get_all()[0]
    extension = file.filename.rsplit('.', 1)[1]
    fingerprint = datetime.now().strftime("%d_%m_%Y_%H_%M_%S_%f_")
    if not settings_video:
        path = f'./static/settings/images'
        with open(f"{path}/{fingerprint}image.{extension}", "wb") as buffer:
            copyfileobj(file.file, buffer)
        responsive_image = ResponsiveImage(original_image=f"{path}/{fingerprint}"
                                                          f"image.{extension}",
                                           fingerprint=fingerprint)
        await responsive_image.create()
        settings.front_page_images.append(f'{path.replace("./", "")}/{fingerprint}'
                                          f'image.{extension}')
        settings.front_page_is_video = False
    else:
        path = f'./static/settings/video'
        settings.front_page_video = f'{path.replace("./", "")}/{fingerprint}video.{extension}'
        with open(f'{path}/{fingerprint}video.{extension}', "wb") as buffer:
            copyfileobj(file.file, buffer)
        settings.front_page_is_video = True
    settings.save()


async def settings_remover(paths: List[str], settings_video: bool):
    from models.settings import SettingsModel
    settings = SettingsModel.get_all()[0]
    sizes = ['', '-1x', '-2x', '-3x', '-4x']
    if settings_video:
        path = f'./static/settings/video'
        for f in listdir(path):
            if isfile(join(path, f)):
                remove(join(path, f))
        settings.front_page_video = ''
    else:
        if paths:
            for path in paths:
                i = path.find('.')
                settings.front_page_images.remove(path)
                for size in sizes:
                    try:
                        remove(f'./{path[:i]}{size}{path[i:]}')
                    except FileNotFoundError:
                        pass
    settings.save()
