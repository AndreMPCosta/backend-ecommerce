from fastapi import APIRouter, status, Security, UploadFile, File

from exceptions import OutputError
from models import UserModel
from models.settings import SettingsModel
from resources.base import settings_uploader, settings_remover

router = APIRouter(
    tags=["settings"],
)


@router.get("/settings/media", status_code=status.HTTP_200_OK,
            responses={
                422: {
                    "model": OutputError,
                    "description": "Validation Error"
                }
            })
async def get_media():
    settings = SettingsModel.get_all()[0]
    if not settings.front_page_is_video:
        return {'media': settings.front_page_images,
                'isVideo': settings.front_page_is_video}
    else:
        return {'media': [settings.front_page_video],
                'isVideo': settings.front_page_is_video}


@router.patch("/settings", status_code=status.HTTP_200_OK,
              responses={
                  422: {
                      "model": OutputError,
                      "description": "Validation Error"
                  }
              })
async def patch_settings(payload: dict):
    settings = SettingsModel.get_all()[0]
    settings.front_page_is_video = payload.get('isVideo')
    settings.save()
    return {'message': 'success'}


@router.post("/settings/upload", status_code=status.HTTP_200_OK,
             responses={
                 422: {
                     "model": OutputError,
                     "description": "Validation Error"
                 }
             })
async def update_settings(is_video: bool = False, file: UploadFile = File(...),
                          current_user: UserModel = Security(UserModel.get_current_user, scopes=["superuser"])):
    return await settings_uploader(file, settings_video=is_video)


@router.delete("/settings", status_code=status.HTTP_200_OK,
               responses={
                   422: {
                       "model": OutputError,
                       "description": "Validation Error"
                   }
               })
async def delete_media(payload: dict, is_video: bool = False,
                       current_user: UserModel = Security(UserModel.get_current_user, scopes=["superuser"])):
    return await settings_remover(payload.get('paths'), settings_video=is_video)
