from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, status, Cookie, Depends, HTTPException, Security
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm

from auth import Token, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from exceptions import OutputError, UserNotUnique, UserNotFound, Error
from languages.errors.messages import translations
from languages.general_messages.messages import general_messages
from models.base import OID
from models.user import UserModel
from resources.base import creator, updater, getter
from resources.order import order_schema
from schemas.user import UserSchema, UserDashboardSchema

router = APIRouter(
    tags=["users"],
)

user_schema = UserSchema()
user_dashboard_schema = UserDashboardSchema()
user_list_schema = UserDashboardSchema(many=True)


async def helper_login(form_data, locale: Optional[str], dashboard=False):
    user = UserModel.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=translations.get(locale).get('wrong_login'),
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=translations.get(locale).get('user_not_active'),
            headers={"WWW-Authenticate": "Bearer"},
        )
    if dashboard:
        if user.role != 'superuser':
            return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED,
                                content={'detail': translations.get(locale).get('no_permissions')})

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "scopes": [user.role]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


async def add_update_item(item: dict, user, locale: str, function=None):
    try:
        if not user:
            raise UserNotFound

        await getattr(user, function)(item)
        return user_schema.dump(user)
    except UserNotFound as e:
        e.msg_template = translations.get(locale).get(e.code) if translations.get(locale).get(e.code) \
            else e.msg_template
        return JSONResponse(status_code=status.HTTP_409_CONFLICT, content=
        {
            "error": e.message(user.email)
        })
    except Error as e:
        e.msg_template = translations.get(locale).get(e.code) if translations.get(locale).get(e.code) \
            else e.msg_template
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            content={"error": "Unexpected error"})


@router.post("/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(),
                                 locale: Optional[str] = Cookie('pt')):
    # if not test_recaptcha(form_data.client_secret):
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail=translations.get(locale).get('bot_error'),
    #         headers={"WWW-Authenticate": "Bearer"},
    #     )
    return await helper_login(form_data, locale)


@router.post("/dashboard/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(),
                                 locale: Optional[str] = Cookie('pt')):
    return await helper_login(form_data, locale, dashboard=True)


@router.get("/dashboard/me")
async def read_users_me(current_user: UserModel = Security(UserModel.get_current_user, scopes=["superuser"])):
    return user_dashboard_schema.dump(current_user)


@router.get("/users/me")
async def get_me(current_user: UserModel = Depends(UserModel.get_current_user)):
    return user_schema.dump(current_user)


@router.get("/users/me/orders/last")
async def get_last_order(current_user: UserModel = Depends(UserModel.get_current_user)):
    return order_schema.dump(current_user.orders[-1])


@router.get("/users/me/orders")
async def get_me(current_user: UserModel = Depends(UserModel.get_current_user)):
    user_schema.context['orders'] = True
    return user_schema.dump(current_user)


@router.get("/users/{_id}",
            status_code=status.HTTP_200_OK,
            responses={
                422: {
                    "model": OutputError,
                    "description": "Validation Error"
                }
            })
async def get_user(_id: OID, current_user: UserModel = Security(UserModel.get_current_user, scopes=["superuser"]),
                   locale: Optional[str] = Cookie('pt')):
    return await getter(UserModel, user_dashboard_schema, _id, UserNotFound, locale)


@router.get("/users",
            status_code=status.HTTP_200_OK,
            responses={
                422: {
                    "model": OutputError,
                    "description": "Validation Error"
                }
            })
async def get_users(current_user: UserModel = Security(UserModel.get_current_user, scopes=["superuser"])):
    return user_list_schema.dump(UserModel.get_all())


@router.patch("/users/{_id}",
              status_code=status.HTTP_200_OK,
              responses={
                  422: {
                      "model": OutputError,
                      "description": "Validation Error"
                  }
              })
async def update_user(_id: OID, payload: dict,
                      current_user: UserModel = Security(UserModel.get_current_user, scopes=["superuser"]),
                      locale: Optional[str] = Cookie('pt')):
    return await updater(UserModel, user_dashboard_schema, _id, payload, UserNotFound, locale)


@router.post("/users",
             status_code=status.HTTP_201_CREATED,
             responses={
                 422: {
                     "model": OutputError,
                     "description": "Validation Error"
                 }
             })
async def create_user(user: dict, locale: Optional[str] = Cookie('pt')):
    # if not test_recaptcha(user.get('client_secret')):
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail=translations.get(locale).get('bot_error'),
    #         headers={"WWW-Authenticate": "Bearer"},
    #     )
    # user.pop('client_secret', None)
    return await creator(UserModel, user_schema, user, UserNotUnique, locale)


@router.put("/users/cart/add",
            status_code=status.HTTP_200_OK,
            responses={
                422: {
                    "model": OutputError,
                    "description": "Validation Error"
                }
            })
async def add_item(item: dict, current_user: UserModel = Depends(UserModel.get_current_user),
                   locale: Optional[str] = Cookie('pt')):
    return await add_update_item(item, current_user, locale, function='add_item')


@router.patch("/users/cart/update",
              status_code=status.HTTP_200_OK,
              responses={
                  422: {
                      "model": OutputError,
                      "description": "Validation Error"
                  }
              })
async def add_item(item: dict, current_user: UserModel = Depends(UserModel.get_current_user),
                   locale: Optional[str] = Cookie('pt')):
    return await add_update_item(item, current_user, locale, function='update_quantity')


@router.delete("/users/cart/delete",
               status_code=status.HTTP_200_OK,
               responses={
                   422: {
                       "model": OutputError,
                       "description": "Validation Error"
                   }
               })
async def delete_item(item: dict, current_user: UserModel = Depends(UserModel.get_current_user),
                      locale: Optional[str] = Cookie('pt')):
    return await add_update_item(item, current_user, locale, function='delete_item')


@router.put("/users/addresses/add",
            status_code=status.HTTP_200_OK,
            responses={
                422: {
                    "model": OutputError,
                    "description": "Validation Error"
                }
            })
async def add_address(address: dict, current_user: UserModel = Depends(UserModel.get_current_user),
                      locale: Optional[str] = Cookie('pt')):
    return await add_update_item(address, current_user, locale, function='add_addresses')


@router.patch("/users/addresses/update",
              status_code=status.HTTP_200_OK,
              responses={
                  422: {
                      "model": OutputError,
                      "description": "Validation Error"
                  }
              })
async def update_address(item: dict, current_user: UserModel = Depends(UserModel.get_current_user),
                         locale: Optional[str] = Cookie('pt')):
    return await add_update_item(item, current_user, locale, function='update_address')


@router.delete("/users/addresses/delete",
               status_code=status.HTTP_200_OK,
               responses={
                   422: {
                       "model": OutputError,
                       "description": "Validation Error"
                   }
               })
async def delete_address(item: dict, current_user: UserModel = Depends(UserModel.get_current_user),
                         locale: Optional[str] = Cookie('pt')):
    return await add_update_item(item, current_user, locale, function='delete_address')


@router.patch("/users",
              status_code=status.HTTP_200_OK,
              responses={
                  422: {
                      "model": OutputError,
                      "description": "Validation Error"
                  }
              })
async def change_user(payload: dict, current_user: UserModel = Depends(UserModel.get_current_user),
                      locale: Optional[str] = Cookie('pt')):
    return await updater(UserModel, user_schema, current_user.id, payload, UserNotFound, locale)


@router.get("/activate/{activation_token}", )
async def activate_user(activation_token: str, locale: Optional[str] = Cookie('pt')):
    user = UserModel.get_by_custom_field('activation_token', activation_token)
    if not user:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND,
                            content={
                                "error": "Este código de ativação não é válido."
                                           "" if locale == 'pt' else 'This activation code is not valid.'})
    if user.active:
        return JSONResponse(status_code=status.HTTP_208_ALREADY_REPORTED,
                            content={
                                "message": "Esta conta já está ativada."
                                           "" if locale == 'pt' else 'This account is already verified.'})
    user.active = True
    user.save()
    return JSONResponse(status_code=status.HTTP_200_OK,
                        content={"message": general_messages.get(locale).get('account_activated').format(user.email)})


@router.post("/users/reset-password",
             status_code=status.HTTP_201_CREATED,
             responses={
                 422: {
                     "model": OutputError,
                     "description": "Validation Error"
                 }
             })
async def create_reset_password_email(payload: dict, locale: Optional[str] = Cookie('pt')):
    user = UserModel.get_by_email(payload.get('email'))
    if not user:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND,
                            content={
                                "error": "O email não foi encontrado nos nossos registos." if locale == 'pt' else
                                "The email was not found on our records."})
    user.send_reset_email(locale)
    return JSONResponse(status_code=status.HTTP_200_OK,
                        content={
                            "message": "Por favor verifique o seu email e siga as instruções." if locale == 'pt' else
                            "Please check your email address and follow the instructions."})


@router.post("/users/new-password/{token}",
             status_code=status.HTTP_200_OK,
             responses={
                 422: {
                     "model": OutputError,
                     "description": "Validation Error"
                 }
             })
async def change_password(token: str, payload: dict, locale: Optional[str] = Cookie('pt')):
    user = UserModel.get_by_custom_field('reset_password_token', token)
    if user:
        user.reset_password_token = ''
        user.save()
    if not user:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND,
                            content={
                                "error": "Token inválido/expirado." if locale == 'pt' else
                                "Invalid/Expired Token."})
    return await updater(UserModel, user_schema, user.id, payload, UserNotFound, locale)
