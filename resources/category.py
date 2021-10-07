from typing import Optional, List, Union, Any
from fastapi import APIRouter, status, Cookie, UploadFile, File, Query, Security
from fastapi.responses import JSONResponse
from starlette.responses import Response

from exceptions import OutputError, CategoryNotUnique, Error, CategoryNotFound
from languages.errors.messages import translations
from languages.general_messages.messages import general_messages
from models.base import OID
from models.category import CategoryModel
from models.user import UserModel
from resources.base import creator, getter, finder, uploader
from schemas.category import CategorySchema

router = APIRouter(
    tags=["categories"],
)

category_schema = CategorySchema()
category_list_schema = CategorySchema(many=True)


@router.get("/categories",
            status_code=status.HTTP_200_OK,
            responses={
                422: {
                    "model": OutputError,
                    "description": "Validation Error"
                }
            })
async def get_categories(locale: Optional[str] = Cookie('pt'), compact: int = 0,
                         by_name: int = 0, filter_categories: Optional[List[str]] = Query(None)):
    categories: Union[List[CategoryModel], list[dict[str, Union[str, Any]]]] = CategoryModel.get_all()
    if compact:
        filtered_categories = [cat for cat in categories if not cat.parent_id]
        return category_list_schema.dump(filtered_categories)
    elif filter_categories:
        categories = await finder(CategoryModel, {
            'id__in': filter_categories
        }, locale)
    elif by_name:
        categories = [{'name': category.name,
                       'id': category.id} for category in categories]
    return category_list_schema.dump(categories)


@router.get("/categories/{_id}", status_code=status.HTTP_200_OK,
            responses={
                422: {
                    "model": OutputError,
                    "description": "Validation Error"
                }
            })
async def get_category(_id: OID, locale: Optional[str] = Cookie('pt')):
    return await getter(CategoryModel, category_schema, _id, CategoryNotFound, locale)


@router.post("/categories",
             status_code=status.HTTP_201_CREATED,
             responses={
                 422: {
                     "model": OutputError,
                     "description": "Validation Error"
                 }
             })
async def create_category(category: dict, locale: Optional[str] = Cookie('pt'),
                          current_user: UserModel = Security(UserModel.get_current_user, scopes=["superuser"])):
    return await creator(CategoryModel, category_schema, category, CategoryNotUnique, locale)


@router.post("/categories/{_id}/upload",
             status_code=status.HTTP_202_ACCEPTED,
             responses={
                 422: {
                     "model": OutputError,
                     "description": "Validation Error"
                 }
             })
async def create_upload_file(response: Response, _id: OID, file: UploadFile = File(...),
                             current_user: UserModel = Security(UserModel.get_current_user, scopes=["superuser"])):
    return await uploader(CategoryModel, 'categories', _id, file)


@router.patch("/categories/{_id}", status_code=status.HTTP_200_OK,
              responses={
                  422: {
                      "model": OutputError,
                      "description": "Validation Error"
                  }
              })
async def update_category(payload: dict, _id: OID, locale: Optional[str] = Cookie('pt'),
                          current_user: UserModel = Security(UserModel.get_current_user, scopes=["superuser"])):
    try:
        db_category: CategoryModel = CategoryModel.get_by_id(_id)
        if not db_category:
            raise CategoryNotFound
        for k, v in payload.items():
            setattr(db_category, k, v)
        if 'subcategories' in payload:
            temp = []
            for subcategory in payload.get('subcategories'):
                if OID(subcategory) != db_category.id:
                    temp_category = CategoryModel.get_by_id(OID(subcategory))
                    temp_category.parent_id = db_category.id
                    temp_category.save()
                    temp.append(temp_category)
            db_category.subcategories = temp
        db_category.save()
    except CategoryNotFound as e:
        e.msg_template = translations.get(locale).get(e.code) if translations.get(locale).get(e.code) \
            else e.msg_template
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND,
                            content={"error": e.message(_id)})
    except Error as e:
        e.msg_template = translations.get(locale).get(e.code) if translations.get(locale).get(e.code) \
            else e.msg_template
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"error": "Unexpected error"})
    return category_schema.dump(db_category)


@router.delete("/categories/{_id}", status_code=status.HTTP_200_OK,
               responses={
                   422: {
                       "model": OutputError,
                       "description": "Validation Error"
                   }
               })
async def delete_category(_id: OID, locale: Optional[str] = Cookie('pt'),
                          current_user: UserModel = Security(UserModel.get_current_user, scopes=["superuser"])):
    try:
        db_category: CategoryModel = CategoryModel.get_by_id(_id)
        if not db_category:
            raise CategoryNotFound
        temp_name = db_category.name
        if db_category.subcategories:
            await db_category.delete_subcategories()
        if db_category.parent_id:
            parent = CategoryModel.get_by_id(db_category.parent_id.id)
            await parent.remove_subcategory(db_category)
        db_category.delete()
    except CategoryNotFound as e:
        e.msg_template = translations.get(locale).get(e.code) if translations.get(locale).get(e.code) \
            else e.msg_template
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND,
                            content={"error": e.message(_id)})
    except Error as e:
        e.msg_template = translations.get(locale).get(e.code) if translations.get(locale).get(e.code) \
            else e.msg_template
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"error": "Unexpected error"})
    return {'message': general_messages.get(locale).get('delete_category').format(temp_name)}
