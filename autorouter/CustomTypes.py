from typing import TypeVar
from tortoise.models import Model
from pydantic import BaseModel

ModelType = TypeVar('ModelType', bound=Model)
CreateSchemaType = TypeVar('CreateSchemaType', bound=BaseModel)
ReadSchemaType = TypeVar('ReadSchemaType', bound=BaseModel)