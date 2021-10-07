from typing import Type, List, Union
from pydantic.types import T


def get_all(_class: Type[T], field: str = 'name', reverse=False) -> List[T]:
    return _class.objects.order_by(field if not reverse else f'-{field}')


def get_one(_class: Type[T], payload: dict) -> T:
    return _class.objects(**payload).first()


def find(_class: Type[T], payload: dict) -> List[T]:
    return _class.objects(**payload)


def count(_class: Type[T], payload: dict) -> List[T]:
    return _class.objects(**payload).count()


def count_all(_class: Type[T]) -> List[T]:
    return _class.objects.count()


def limit(_class: Type[T], start: Union[int, None] = None, stop: Union[int, None] = None,
          order_by: str = None) -> List[T]:
    if stop is None:
        return _class.objects[start:].order_by(order_by)
    if start is None:
        return _class.objects[:stop].order_by(order_by)
    return _class.objects[start:stop].order_by(order_by)
