from http.client import HTTPResponse

from fastapi import APIRouter, Body
from pydantic import BaseModel

from .CustomTypes import ModelType, CreateSchemaType, ReadSchemaType
from typing import List, Type, Generic, Callable, Optional, Union, Sequence, Any
from fastapi.exceptions import HTTPException
from tortoise.exceptions import DoesNotExist, MultipleObjectsReturned
from fastapi import Response
from fastapi.params import Depends
PYDANTIC_SCHEMA = BaseModel
DEPENDENCIES = Optional[Sequence[Depends]]

class CrudBase(APIRouter):

    def __init__(self, model: Type[ModelType], read_schema: Type[ReadSchemaType],
                 create_schema: Optional[Type[PYDANTIC_SCHEMA]]) -> None:
        super().__init__()
        self.model = model
        self.create_schema = create_schema

    def get_one_by_id(self, *args, **kwargs) -> Callable:
        async def route(id: int) -> ModelType:
            try:
                await self.model.get(id=id)
                obj = await self.model.get(id=id)
                return obj
            except DoesNotExist:
                raise HTTPException(status_code=404, detail=f'{self.model.__name__} not found')
            except MultipleObjectsReturned:
                raise HTTPException(status_code=400,detail=f'{self.model.__name__} returned multiple objects with id={id}')
        return route

    def create(self, *args, **kwargs) -> Callable:
        async def route(model: self.create_schema) -> ModelType:
            try:
                obj = self.model.create(**model.dict())
                return await obj
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e) + "\n Maybe you have forgotten "
                                                                     "to register tortoise in fast api?")

        return route

    def list(self):
        async def route() -> List[ModelType]:
            objects = self.model.all()
            return await objects

        return route

    def update(self):
        async def route(id: int, body: self.create_schema) -> ModelType:
            try:
                obj = await self.model.get(id=id)
                obj = await obj.update_from_dict(**body)
                await obj.save()
                return obj
            except:
                pass

        return route

    def update_partly(self):
        async def route(id: int, body: self.create_schema) -> ModelType:
            try:
                obj = await self.model.get(id=id)
                obj = await obj.update_from_dict(**body)
                await obj.save()
                return obj
            except:
                pass

        return route

    def delete_one(self):
        async def route(id: int):
            try:
                obj = await self.model.get(id=id)
                await obj.delete()
                return Response(status_code=200)
            except DoesNotExist:
                raise HTTPException(status_code=404, detail=f'{self.model.__name__} not found')
            except MultipleObjectsReturned:
                raise HTTPException(status_code=400,
                                    detail=f'{self.model.__name__} returned multiple objects with id={id}')
        return route

    async def bulk_create(self, data: CreateSchemaType) -> List[ModelType]:
        pass

    async def bulk_update(self, data: CreateSchemaType) -> List[ModelType]:
        pass

    def bulk_update_partly(self, data: CreateSchemaType) -> List[ModelType]:
        pass


class AutoRouter(CrudBase):
    def __init__(self, model: Type[ModelType],
                 create_schema: Type[CreateSchemaType] | None = None,
                 read_schema: Type[ReadSchemaType] | None = None,
                 prefix: str | None = None) -> None:
        super().__init__(model=model, read_schema=read_schema, create_schema=create_schema)
        self.create_schema = create_schema
        self.read_schema = read_schema
        self.prefix = prefix
        dependencies: Union[bool, DEPENDENCIES] = True

        self._add_api_route(
            "",
            self.create(),
            methods=["POST"],
            response_model=self.create_schema,
            summary="Create One",
            dependencies=dependencies,
        )
        self._add_api_route(
            "/{id}",
            self.get_one_by_id(),
            methods=["GET"],
            response_model=self.read_schema,
            summary="get one",
            dependencies=dependencies,
        )

        self._add_api_route(
            "/{id}",
            self.delete_one(),
            methods=["DELETE"],
            summary="get one",
            dependencies=dependencies,
        )

        self._add_api_route(
            "",
            self.list(),
            methods=["GET"],
            response_model=List[self.read_schema],
            summary="get one",
            dependencies=dependencies,
        )

        self._add_api_route(
            "/{id}",
            self.update(),
            methods=["PUT"],
            response_model=self.read_schema,
            summary="get one",
            dependencies=dependencies,
        )

        self._add_api_route(
            "/{id}",
            self.update_partly(),
            methods=["PATCH"],
            response_model=self.read_schema,
            summary="get one",
            dependencies=dependencies,
        )

    def _add_api_route(
            self,
            path: str = '123',
            endpoint: Callable[..., Any] = None,
            dependencies: Union[bool, DEPENDENCIES] = None,
            error_responses: Optional[List[HTTPException]] = None,
            **kwargs: Any,
    ) -> None:
        dependencies = [] if isinstance(dependencies, bool) else dependencies
        responses: Any = (
            {err.status_code: {"detail": err.detail} for err in error_responses}
            if error_responses
            else None
        )

        super().add_api_route(
            path, endpoint, dependencies=dependencies, responses=responses, **kwargs
        )