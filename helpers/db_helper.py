from typing import Type, List

from pydantic.types import T

from database import engine


async def count(_class: Type[T], field: str, value) -> int:
    final_count = await engine.count(_class, )
    return final_count


async def count_by_query(_class: Type[T], field: str, value) -> int:
    return await engine.count(_class, getattr(_class, field) == value)


async def count_by_query_list(_class: Type[T], field: str, value: list) -> int:
    return await engine.count(_class, getattr(_class, field).in_(value))


async def get_all(_class: Type[T]) -> List[T]:
    return await engine.find(_class)


async def get_last(_class: Type[T], field: str) -> T:
    return await engine.find_one(_class, sort=getattr(_class, field).desc())


async def get_one(_class: Type[T], field: str, value) -> T:
    # query_with_translations = [getattr(_class, field) == value]
    # for lang in available_languages:
    #     query_with_translations.append(getattr(_class, field) == get_text(lang, value))
    # query_with_translations = tuple(query_with_translations)
    return await engine.find_one(_class, getattr(_class, field) == value)


async def find(_class: Type[T], field: str, value) -> List[T]:
    found_objects = await engine.find(_class, getattr(_class, field) == value)
    if 0 < len(found_objects) < 2:
        found_objects = found_objects[0]
    return found_objects
