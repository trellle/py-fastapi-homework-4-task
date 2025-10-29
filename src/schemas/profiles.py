from datetime import date
from re import S

from fastapi import UploadFile, Form, File, HTTPException
from pydantic import BaseModel, field_validator, HttpUrl, Field

from validation import (
    validate_name,
    validate_image,
    validate_gender,
    validate_birth_date
)
from database.models.accounts import GenderEnum


class BaseUserProfileSchema(BaseModel):
    first_name: str
    last_name: str
    gender: GenderEnum
    date_of_birth: date
    info: str

    @field_validator("first_name")
    @classmethod
    def first_name_validator(cls, value: str):
        validate_name(value)
        return value

    @field_validator("last_name")
    @classmethod
    def last_name_validator(cls, value: str):
        validate_name(value)
        return value

    @field_validator("gender")
    @classmethod
    def gender_validator(cls, value: GenderEnum):
        validate_gender(value)
        return value

    @field_validator("date_of_birth")
    @classmethod
    def birth_date_validator(cls, value: date):
        validate_birth_date(value)
        return value

    @field_validator("info")
    @classmethod
    def info_validator(cls, value: str):
        if not value or not value.strip():
            raise ValueError("Name cannot be empty or contain only spaces.")
        return value


class UserProfileSchema(BaseUserProfileSchema):
    avatar: UploadFile

    @field_validator("avatar")
    @classmethod
    def avatar_validator(cls, value: UploadFile):
        validate_image(value)
        return value


class ProfileResponseSchema(BaseUserProfileSchema):
    id: int
    user_id: int
    avatar: str
