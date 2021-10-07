from typing import Optional
from fastapi import APIRouter, status, Cookie, UploadFile, File, Security

from exceptions import OutputError, AttributeNotUnique, AttributeNotFound
from models.attribute import AttributeModel
from models.base import OID
from models.user import UserModel
from resources.base import creator, updater, getter, deleter, uploader
from schemas.attribute import AttributeSchema

router = APIRouter(
    tags=["attributes"],
)

attribute_schema = AttributeSchema()
attribute_list_schema = AttributeSchema(many=True)


@router.get("/attributes",
            status_code=status.HTTP_200_OK,
            responses={
                422: {
                    "model": OutputError,
                    "description": "Validation Error"
                }
            })
async def get_attributes(locale: Optional[str] = Cookie('pt')):
    return attribute_list_schema.dump(AttributeModel.get_all())


@router.get("/attributes/{_id}", status_code=status.HTTP_200_OK,
            responses={
                422: {
                    "model": OutputError,
                    "description": "Validation Error"
                }
            })
async def get_attribute(_id: OID, locale: Optional[str] = Cookie('pt')):
    return await getter(AttributeModel, attribute_schema, _id, AttributeNotFound, locale)


@router.post("/attributes",
             status_code=status.HTTP_201_CREATED,
             responses={
                 422: {
                     "model": OutputError,
                     "description": "Validation Error"
                 }
             })
async def create_attribute(attribute: dict, locale: Optional[str] = Cookie('pt'),
                           current_user: UserModel = Security(UserModel.get_current_user, scopes=["superuser"])):
    return await creator(AttributeModel, attribute_schema, attribute, AttributeNotUnique, locale)


@router.post("/attributes/{_id}/{option_name}/upload",
             status_code=status.HTTP_202_ACCEPTED,
             responses={
                 422: {
                     "model": OutputError,
                     "description": "Validation Error"
                 }
             })
async def create_upload_file(_id: OID, option_name, file: UploadFile = File(...),
                             current_user: UserModel = Security(UserModel.get_current_user, scopes=["superuser"])):
    return await uploader(AttributeModel, 'attributes', _id, file, option=option_name)


@router.patch("/attributes/{_id}", status_code=status.HTTP_200_OK,
              responses={
                  422: {
                      "model": OutputError,
                      "description": "Validation Error"
                  }
              })
async def update_attribute(payload: dict, _id: OID, locale: Optional[str] = Cookie('pt'),
                           current_user: UserModel = Security(UserModel.get_current_user, scopes=["superuser"])):
    return await updater(AttributeModel, attribute_schema, _id, payload, AttributeNotFound, locale,
                         slot=AttributeModel.inject_options, ignore_fields=['options'])


@router.delete("/attributes/{_id}", status_code=status.HTTP_200_OK,
               responses={
                   422: {
                       "model": OutputError,
                       "description": "Validation Error"
                   }
               })
async def delete_attribute(_id: OID, locale: Optional[str] = Cookie('pt'),
                           current_user: UserModel = Security(UserModel.get_current_user, scopes=["superuser"])):
    return await deleter(AttributeModel, _id, AttributeNotFound, locale, 'delete_attribute')
