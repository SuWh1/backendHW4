from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ItemBase(BaseModel):
    title: str
    description: Optional[str] = None
    is_active: bool = True


class ItemCreate(ItemBase):
    pass


class ItemUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class ItemResponse(ItemBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class FileUploadResponse(BaseModel):
    id: int
    filename: str
    s3_key: str
    s3_url: str
    content_type: Optional[str]
    file_size: Optional[int]
    created_at: datetime
    
    class Config:
        from_attributes = True 