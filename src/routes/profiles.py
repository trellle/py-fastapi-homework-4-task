from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from storages import S3StorageInterface
from sqlalchemy.orm import joinedload
from sqlalchemy import select
from database import get_db
from security.http import get_token
from config import get_jwt_auth_manager
from clients import get_s3_storage_client
from exceptions.security import TokenExpiredError
from exceptions.storage import BaseS3Error
from security.interfaces import JWTAuthManagerInterface
from schemas.profiles import UserProfileSchema, ProfileResponseSchema
from database.models.accounts import UserGroupEnum, UserModel, UserProfileModel

router = APIRouter()


@router.post("/users/{user_id}/profile/", response_model=ProfileResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_user_profile(payload: UserProfileSchema,
                              user_id: int,
                              jwt_manager: JWTAuthManagerInterface = Depends(get_jwt_auth_manager),
                              s3_client: S3StorageInterface = Depends(get_s3_storage_client),
                              db: AsyncSession = Depends(get_db),
                              token: str = Depends(get_token)):
    try:
        token_data = jwt_manager.decode_access_token(token)
    except TokenExpiredError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired.")
    response = await db.execute(select(UserModel).options(joinedload(UserModel.profile)).where(UserModel.id == user_id))
    user = response.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or not active.")
    user_id_token = token_data.get("user_id")
    response = await db.execute(select(UserModel).options(joinedload(UserModel.group)).where(UserModel.id == user_id_token))
    current_user = response.scalar_one_or_none()
    if not current_user:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Current user not found.")
    if current_user.id != user_id and current_user.group.name != UserGroupEnum.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="You don't have permission to edit this profile.")
    if user.profile:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already has a profile.")
    try:
        content = await payload.avatar.read()
        avatar_file = f"{user_id}_avatar.{payload.avatar.content_type.split("/")[1]}"
        await s3_client.upload_file(
            file_name=avatar_file,
            file_type=content
        )
        avatar_url = await s3_client.get_file_url(avatar_file)
    except BaseS3Error:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Failed to upload avatar. Please try again later.")
    else:
        user_profile = UserProfileModel(
            user_id=user_id,
            first_name=payload.first_name,
            last_name=payload.last_name,
            gender=payload.gender,
            date_of_birth=payload.date_of_birth,
            info=payload.info,
            avatar=avatar_url
        )
        db.add(user_profile)
        await db.commit()
        return user_profile
