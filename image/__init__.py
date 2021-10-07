from dataclasses import dataclass, field
from typing import Dict

from PIL import Image


@dataclass
class ResponsiveImage:
    original_image: str
    fingerprint: str
    # sizes: Dict = field(default_factory=lambda: {
    #     '400w': '',
    #     '800w': '',
    #     '1200w': '',
    #     '1600w': ''
    # })
    sizes_number: Dict = field(default_factory=lambda: {
        '400': '1x',
        '800': '2x',
        '1200': '3x',
        '1600': '4x'
    })

    async def create(self):
        image = Image.open(self.original_image)
        for size, rep in {int(k): v for k, v in self.sizes_number.items()}.items():
            image.thumbnail((size, size))
            temp = self.original_image.rsplit('/', 1)
            path = temp[0]
            filename_with_extension = temp[1]
            temp_filename = filename_with_extension.rsplit('.')
            extension = temp_filename[1]
            image.save(f'{path}/{self.fingerprint}image-{rep}.{extension}')
            image = Image.open(self.original_image)
            # self.sizes[f'{size}w'] = f'{path}/image-{rep}.{extension}'
