from typing import Optional, Union
from fastapi import APIRouter, status, Cookie, UploadFile, File, Security

from exceptions import OutputError, ProductNotFound, ProductNotUnique
from models import ProductModel
from models.base import OID
from models.user import UserModel
from resources.base import creator, updater, getter, deleter, uploader
from schemas.product import ProductSchema

router = APIRouter(
    tags=["products"],
)

product_schema = ProductSchema()
product_list_schema = ProductSchema(many=True)


@router.get("/products", status_code=status.HTTP_200_OK,
            responses={
                422: {
                    "model": OutputError,
                    "description": "Validation Error"
                }
            })
async def get_products_by_category(category: Union[OID, str] = None, locale: Optional[str] = Cookie('pt')):
    if category:
        products = ProductModel.get_by_category(category)
    else:
        products = ProductModel.get_all()
    return product_list_schema.dump(products)


@router.get("/products/{_id}", status_code=status.HTTP_200_OK,
            responses={
                422: {
                    "model": OutputError,
                    "description": "Validation Error"
                }
            })
async def get_product(_id: OID, locale: Optional[str] = Cookie('pt')):
    return await getter(ProductModel, product_schema, _id, ProductNotFound, locale)


@router.post("/products",
             status_code=status.HTTP_201_CREATED,
             responses={
                 422: {
                     "model": OutputError,
                     "description": "Validation Error"
                 }
             })
async def create_product(product: dict, locale: Optional[str] = Cookie('pt'),
                         current_user: UserModel = Security(UserModel.get_current_user, scopes=["superuser"])):
    from models.product_type import ProductTypeModel
    return await creator(ProductModel, product_schema, product, ProductNotUnique, locale)


@router.post("/products/{_id}/upload",
             status_code=status.HTTP_202_ACCEPTED,
             responses={
                 422: {
                     "model": OutputError,
                     "description": "Validation Error"
                 }
             })
async def create_upload_file(_id: OID, file: UploadFile = File(...),
                             current_user: UserModel = Security(UserModel.get_current_user, scopes=["superuser"])):
    return await uploader(ProductModel, 'products', _id, file)


@router.post("/products/{_id}/{attr_name}/{option_name}/upload",
             status_code=status.HTTP_202_ACCEPTED,
             responses={
                 422: {
                     "model": OutputError,
                     "description": "Validation Error"
                 }
             })
async def create_upload_file(_id: OID, attr_name: str, option_name: str, file: UploadFile = File(...),
                             current_user: UserModel = Security(UserModel.get_current_user, scopes=["superuser"])):
    return await uploader(ProductModel, 'products', _id, file, attr_name=attr_name, option_name=option_name)


@router.patch("/products/{_id}", status_code=status.HTTP_200_OK,
              responses={
                  422: {
                      "model": OutputError,
                      "description": "Validation Error"
                  }
              })
async def update_product(payload: dict, _id: OID, locale: Optional[str] = Cookie('pt'),
                         current_user: UserModel = Security(UserModel.get_current_user, scopes=["superuser"])):
    from models.category import CategoryModel
    return await updater(ProductModel, product_schema, _id, payload, ProductNotFound, locale,
                         watch_fields=['product_type', 'category'],
                         force_model={'category': CategoryModel})


@router.delete("/products/{_id}", status_code=status.HTTP_200_OK,
               responses={
                   422: {
                       "model": OutputError,
                       "description": "Validation Error"
                   }
               })
async def delete_product(_id: OID, locale: Optional[str] = Cookie('pt'),
                         current_user: UserModel = Security(UserModel.get_current_user, scopes=["superuser"])):
    return await deleter(ProductModel, _id, ProductNotFound, locale, 'delete_product', is_product=True)
