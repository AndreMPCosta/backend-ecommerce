from fastapi import APIRouter, status, Response, BackgroundTasks
from fastapi.responses import JSONResponse

from exceptions import Error, OutputError
from languages import languages
from models.language import Language

router = APIRouter(
    tags=["languages"],
)


@router.put("/languages", status_code=status.HTTP_201_CREATED,
            responses={
                422: {
                    "model": OutputError,
                    "description": "Validation Error"
                }
            })
async def add_update_language(language: dict, response: Response, background_tasks: BackgroundTasks):
    try:
        db_language = Language.get_language(language.get('prefix'))
        if db_language:
            db_language.add_strings(language.get('strings'))
            background_tasks.add_task(languages.update_strings, language.get('prefix'), language.get('strings'))
            response.status_code = status.HTTP_200_OK
            return db_language
        else:
            db_language.save()
    except Error as e:
        return JSONResponse(status_code=422, content={"error": e.message(language.get('prefix'))})
    return language
