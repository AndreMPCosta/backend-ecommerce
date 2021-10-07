import asyncio
from glob import glob
from os import remove
from os.path import exists
from shutil import rmtree
from sys import argv

from exceptions import AttributeNotUnique
from helpers.db_helper_v2 import get_all
from languages import languages
from models import ProductModel, UserModel, OrderModel, PaymentModel
from models.attribute import AttributeModel
from models.category import CategoryModel
from models.language import Language
from models.product_type import ProductTypeModel
from resources.attribute import attribute_schema
from resources.base import translations_helper, creator

categories = [
    {
        'name': 'Accessories'
    },
    {
        'name': 'Apparel'
    },
    {
        'name': 'Groceries'
    },
    {
        'name': 'Paints',
        'parent': 'Accessories'
    },
    {
        'name': 'Homewares',
        'parent': 'Accessories'
    },
    {
        'name': 'Audiobooks',
        'parent': 'Accessories'
    },
    {
        'name': 'T-shirts',
        'parent': 'Apparel'
    },
    {
        'name': 'Polo Shirts',
        'parent': 'Apparel'
    },
    {
        'name': 'Hoodies',
        'parent': 'Apparel'
    },
    {
        'name': 'Footwear',
        'parent': 'Apparel'
    },
    {
        'name': 'Juices',
        'parent': 'Groceries'
    },
    {
        'name': 'Alcohol',
        'parent': 'Groceries'
    },
]


async def help_populate_cats(cat):
    if 'parent' in cat.keys():
        parent_id = CategoryModel.get_by_name(cat.get('parent')).id
        category = CategoryModel(name=cat.get('name'), parent_id=parent_id)
    else:
        category = CategoryModel(name=cat.get('name'))
    category.save()
    tasks = []
    for field in category.translations:
        task = asyncio.ensure_future(translations_helper(field, category, 'en-US'))
        tasks.append(task)
    await asyncio.gather(*tasks)
    print(f"{cat.get('name')} added.")


async def help_populate_sub(cat):
    child = CategoryModel.get_by_name(cat.get('name'))
    parent = CategoryModel.get_by_name(cat.get('parent'))
    await child.add_parent(parent)
    await parent.add_subcategory(child)


attributes = [
    {
        'name': 'Medium',
        'options': [
            {
                'name': 'vinyl',
            },
            {
                'name': 'dvd',
            },
            {
                'name': 'vhs',
            },
            {
                'name': 'itunes',
            },
            {
                'name': 'cd',
            },
            {
                'name': 'mp3',
            },
        ]
    },
    {
        'name': 'ABV',
        'options': [
            {
                'name': 5.1,
            },
            {
                'name': 6.7,
            },
        ]
    },
    {
        'name': 'Material',
        'options': [
            {
                'name': 'cotton',
            },
            {
                'name': 'elastane',
            },
            {
                'name': 'polyester',
            },
        ]
    },
    {
        'name': 'Flavor',
        'options': [
            {
                'name': 'orange',
            },
            {
                'name': 'banana',
            },
            {
                'name': 'apple',
            },
        ]
    },
    {
        'name': 'Size',
        'options': [
            {
                'name': 's',
            },
            {
                'name': 'm',
            },
            {
                'name': 'l',
            },
            {
                'name': 'xl',
            },
            {
                'name': 'xxl',
            },
        ]
    },
    {
        'name': 'Color',
        'options': [
            {
                'name': 'Blue',
            },
            {
                'name': 'Red',
            },
        ]
    },
]


async def help_populate_attributes(attribute):
    await creator(AttributeModel, attribute_schema, attribute, AttributeNotUnique, 'en-US')
    # at = AttributeModel(name=attribute.get('name'))
    # at.save()
    at = AttributeModel.get_by_name(attribute.get('name'))
    at = await AttributeModel.inject_options(at, attribute, 'en-US')
    at.save()
    tasks = []
    # for field in at.translations:
    #     task = asyncio.ensure_future(translations_helper(field, at, 'en-US'))
    #     tasks.append(task)
    # await asyncio.gather(*tasks)
    print(f"{attribute.get('name')} added.")


product_types = [
    {
        'name': 'Clothing',
        'attributes': ['size']
    },
    {
        'name': 'Juice',
        'attributes': ['flavor']
    },
    {
        'name': 'Beer',
        'attributes': ['abv']
    },
    {
        'name': 'Audiobook',
        'attributes': ['medium']
    },

]


async def help_populate_product_types(product_type):
    temp_ats = []
    for at in product_type.get('attributes'):
        temp_at = AttributeModel.get_by_slug(at)
        temp_ats.append(temp_at.id)
    pt = ProductTypeModel(name=product_type.get('name'), attributes=temp_ats)
    pt.save()
    tasks = []
    for field in pt.translations:
        task = asyncio.ensure_future(translations_helper(field, pt, 'en-US'))
        tasks.append(task)
    await asyncio.gather(*tasks)
    print(f"{product_type.get('name')} added.")


products = [
    {
        'name': 'Compal Juice',
        'price': 5.00,
        'product_type': 'Juice',
        'category': 'Juices'
    },
    {
        'name': 'Bathroom Songs',
        'price': 9.99,
        'product_type': 'Audiobook',
        'category': 'Audiobooks'
    },
    {
        'name': 'Seaman Beer',
        'price': 5.45,
        'product_type': 'Beer',
        'category': 'Alcohol'
    },
    {
        'name': 'Awesome Hoodie',
        'price': 11.00,
        'product_type': 'Clothing',
        'category': 'Hoodies',
        'attributes': [{
            'name': 'Color',
            'options': [
                {
                    'name': 'Blue',
                    'image': '',
                    'color': ''
                },
                {
                    'name': 'Red',
                    'image': '',
                    'color': ''
                },
            ]
        }]
    },
]


async def help_populate_products(product):
    pt = ProductTypeModel.get_by_name(product.get('product_type'))
    cat = CategoryModel.get_by_name(product.get('category'))
    p = ProductModel(
        name=product.get('name'),
        product_type=pt,
        price=product.get('price'),
        category=cat,
        attributes=product.get('attributes') if 'attributes' in product.keys() else []
    )
    p.save()
    tasks = []
    for field in p.translations:
        task = asyncio.ensure_future(translations_helper(field, p, 'en-US'))
        tasks.append(task)
    await asyncio.gather(*tasks)
    print(f"{product.get('name')} added.")


async def populate():
    tasks = []
    print('\nPopulating Categories:')
    for cat in categories:
        task = help_populate_cats(cat)
        tasks.append(task)
        # await response outside the for loop
    await asyncio.gather(*tasks)

    # tasks_2 = []
    # for cat in categories[3:]:
    #     task = help_populate_sub(cat)
    #     tasks_2.append(task)
    # await asyncio.gather(*tasks_2)

    tasks_3 = []
    print('\nPopulating Attributes:')
    for attribute in attributes:
        task = help_populate_attributes(attribute)
        tasks_3.append(task)

    await asyncio.gather(*tasks_3)

    tasks_4 = []
    print('\nPopulating Product Types:')
    for product_type in product_types:
        task = help_populate_product_types(product_type)
        tasks_4.append(task)

    await asyncio.gather(*tasks_4)

    tasks_5 = []
    print('\nPopulating Products:')
    for product in products:
        task = help_populate_products(product)
        tasks_5.append(task)

    await asyncio.gather(*tasks_5)

    # print(languages)

    # for lang in available_languages:
    #     db_language = await Language.get_language(lang)
    #
    #     await db_language.add_strings(languages.languages.get(lang), internal=True)


async def clear():
    print('\nClearing Categories:')
    for cat in CategoryModel.get_all():
        print(f"{cat.name} cleared.")
        cat.delete()

    print('\nClearing Attributes:')
    for attribute in AttributeModel.get_all():
        print(f"{attribute.name} cleared.")
        attribute.delete()
    #
    print('\nClearing Product Types:')
    for product_type in ProductTypeModel.get_all():
        print(f"{product_type.name} cleared.")
        product_type.delete()

    print('\nClearing Products:')
    for product in ProductModel.get_all():
        print(f"{product.name} cleared.")
        product.delete()

    print('\nClearing Orders:')
    for order in OrderModel.get_all():
        print(f"Order {order.id} deleted.")
        order.delete()
    for user in UserModel.get_all():
        print(f"Orders from {user.email} deleted.")
        user.orders = []
        user.cart = []
        user.save()

    print('\nClearing Payments:')
    for payment in PaymentModel.get_all():
        print(f"Order {payment.id} deleted.")
        payment.delete()

    print('\nClearing Translations:')
    for lang in get_all(Language, 'prefix'):
        print(f"Language '{lang.prefix}' cleared.")
        lang.strings = {}
        if exists(f'languages/{lang.prefix}.json'):
            remove(f"languages/{lang.prefix}.json")
        lang.save()
        languages.clear()
        # print(get_text('en-US', 'test'))

    print('\nClearing static folder:')
    if exists('static'):
        dirs = glob('static/*')
        for internal_dir in dirs:
            rmtree(internal_dir)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    if argv[1] == 'populate':
        loop.run_until_complete(populate())
    elif argv[1] == 'clear':
        loop.run_until_complete(clear())
    loop.close()
