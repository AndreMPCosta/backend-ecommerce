from typing import Optional, List

from mongoengine import Document, ListField, StringField, BooleanField

from models.base import Base


class SettingsModel(Document, Base):
    meta = {
        'collection': 'settings'
    }

    front_page_images: Optional[List[str]] = ListField(StringField(required=False), required=False, default=[])
    front_page_video: Optional[List[str]] = StringField(required=False, default='')
    front_page_is_video: bool = BooleanField(required=True, default=False)
