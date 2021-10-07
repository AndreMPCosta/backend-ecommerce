from typing import Optional, Union, List, Any

from bson import ObjectId
from fastapi import APIRouter, status, Cookie

from exceptions import OutputError, ProductTypeNotFound, ProductTypeNotUnique
from models.base import OID
from models.product_type import ProductTypeModel
from resources.base import creator, updater, getter, deleter
from schemas.product_type import ProductTypeSchema

router = APIRouter(
    tags=["product-types"],
)

product_type_schema = ProductTypeSchema()
product_type_list_schema = ProductTypeSchema(many=True)


@router.get("/product-types",
            status_code=status.HTTP_200_OK,
            responses={
                422: {
                    "model": OutputError,
                    "description": "Validation Error"
                }
            })
async def get_product_types(locale: Optional[str] = Cookie('pt'), by_name: int = 0):
    product_types: Union[List[ProductTypeModel], list[dict[str, Union[str, Any]]]] = ProductTypeModel.get_all()
    if by_name:
        product_types = [{'name': product_type.name,
                          'id': product_type.id} for product_type in product_types]
    return product_type_list_schema.dump(product_types)


@router.get("/product-types/{_id}", status_code=status.HTTP_200_OK,
            responses={
                422: {
                    "model": OutputError,
                    "description": "Validation Error"
                }
            })
async def get_product_type(_id: OID, locale: Optional[str] = Cookie('pt')):
    return await getter(ProductTypeModel, product_type_schema, _id, ProductTypeNotFound, locale)


@router.post("/product-types",
             status_code=status.HTTP_201_CREATED,
             responses={
                 422: {
                     "model": OutputError,
                     "description": "Validation Error"
                 }
             })
async def create_product_type(product_type: dict, locale: Optional[str] = Cookie('pt')):
    if 'attributes' in product_type.keys():
        product_type['attributes'] = [ObjectId(a) for a in product_type['attributes']]
        late_fields = {
            'attributes': product_type.get('attributes')
        }
        product_type.pop('attributes', None)
    else:
        late_fields = None
    return await creator(ProductTypeModel, product_type_schema, product_type, ProductTypeNotUnique, locale,
                         late_fields=late_fields)


@router.patch("/product-types/{_id}", status_code=status.HTTP_200_OK,
              responses={
                  422: {
                      "model": OutputError,
                      "description": "Validation Error"
                  }
              })
async def update_product_type(payload: dict, _id: OID, locale: Optional[str] = Cookie('pt')):
    return await updater(ProductTypeModel, product_type_schema, _id, payload, ProductTypeNotFound, locale,
                         watch_fields=['attributes'])


@router.delete("/product-types/{_id}", status_code=status.HTTP_200_OK,
               responses={
                   422: {
                       "model": OutputError,
                       "description": "Validation Error"
                   }
               })
async def delete_product_type(_id: OID, locale: Optional[str] = Cookie('pt')):
    return await deleter(ProductTypeModel, _id, ProductTypeNotFound, locale, 'delete_product_type')
