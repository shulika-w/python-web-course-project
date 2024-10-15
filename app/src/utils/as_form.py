import inspect
from pydantic import (
    BaseModel,
    ValidationError,
)
from typing import Type

from fastapi import Form, UploadFile, File
from fastapi.exceptions import RequestValidationError


def as_form(cls: Type[BaseModel]):
    new_parameters = []

    for field_name, model_field in cls.model_fields.items():
        model_field: ModelField  # type: ignore
        if model_field.is_required:
            new_parameters.append(
                inspect.Parameter(
                    field_name,
                    inspect.Parameter.POSITIONAL_ONLY,
                    default=File(model_field.default)
                    if model_field.annotation == UploadFile
                    else Form(model_field.default),
                    annotation=model_field.annotation,
                )
            )
        else:
            new_parameters.append(
                inspect.Parameter(
                    field_name,
                    inspect.Parameter.POSITIONAL_ONLY,
                    default=File(None)
                    if model_field.annotation == UploadFile
                    else Form(None),
                    annotation=model_field.annotation,
                )
            )

    async def as_form_func(**data):
        try:
            return cls(**data)
        except ValidationError as e:
            raise RequestValidationError(e.errors())

    sig = inspect.signature(as_form_func)
    sig = sig.replace(parameters=new_parameters)
    as_form_func.__signature__ = sig  # type: ignore
    setattr(cls, "as_form", as_form_func)
    return cls
