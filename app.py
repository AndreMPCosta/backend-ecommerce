from json import dump
from os import mkdir
from os.path import exists
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from config import available_languages, sample_logger, domain
from resources import category, attribute, product_type, product, language, user, payment, order, settings
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "http://localhost:8080",
    "http://localhost:5000",
    f"https://{domain}",
    f"https://dashboard.{domain}",
    "https://google.com",
    "https://www.google.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(language.router)
app.include_router(category.router)
app.include_router(attribute.router)
app.include_router(product_type.router)
app.include_router(product.router)
app.include_router(user.router)
app.include_router(payment.router)
app.include_router(order.router)
app.include_router(settings.router)


# app.state.languages = AppLanguage(prefixes=available_languages)

async def create_dirs():
    if not exists('./static/settings'):
        mkdir('./static/settings')
    if not exists('./static/settings/images'):
        mkdir('./static/settings/images')
    if not exists('./static/settings/video'):
        mkdir('./static/settings/video')
    if not exists('./static/categories'):
        mkdir('./static/categories')
    if not exists('./static/products'):
        mkdir('./static/products')
    if not exists('./static/attributes'):
        mkdir('./static/attributes')
    if not exists('./invoice/invoices'):
        mkdir('./invoice/invoices')


@app.on_event("startup")
async def startup_event():
    from models.language import Language
    for lang in available_languages:
        db_lang = Language.get_language(lang)
        if not db_lang:
            new_lang = Language(prefix=lang)
            new_lang.save()
            with open(f'languages/{lang}.json', 'w'):
                pass
        else:
            with open(f'languages/{db_lang.prefix}.json', 'w') as outfile:
                dump(db_lang.strings, outfile, sort_keys=True, indent=4)
    await create_dirs()

    from models.settings import SettingsModel
    if not SettingsModel.get_all():
        settings = SettingsModel()
        settings.save()

    # from models.product import ProductModel
    # products = ProductModel.get_all()
    # for p in products:
    #     p.quantities = []
    #     if p.product_type.attributes:
    #         if not p.attributes:
    #             for a in p.product_type.attributes:
    #                 temp = []
    #                 for o in a.options:
    #                     temp.append({'name': str(o.name), 'option': 10})
    #                 p.quantities.append({'name': a.name, 'option': temp})
    #         else:
    #             for a in p.attributes:
    #                 for o in a.get('options'):
    #                     temp = []
    #                     for a2 in p.product_type.attributes:
    #                         for o2 in a2.options:
    #                             temp.append({'name': str(o2.name), 'option': 20})
    #                     p.quantities.append({'name': o.get('name'), 'option': temp})
    #     else:
    #         p.quantity = 10
    #     p.own_sold_out = False
    #     p.save()


if not exists('./static'):
    mkdir('./static')

if not exists('./logs'):
    mkdir('./logs')
    Path('./logs/access.log').touch()
    Path('./logs/error.log').touch()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    # import uvicorn
    # uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True, workers=2)
    import asyncio
    import uvicorn

    # LOGGING_CONFIG["formatters"]["default"]["fmt"] = "%(asctime)s [%(name)s] %(levelprefix)s %(message)s"
    loop = asyncio.get_event_loop()
    config = uvicorn.Config(
        app="app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        workers=2,
        loop=loop,
        log_config=sample_logger,
    )
    server = uvicorn.Server(config)
    loop.run_until_complete(server.serve())
