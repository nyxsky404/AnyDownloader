from pydantic import BaseModel, HttpUrl, Field


class DownloadRequest(BaseModel):
    url: HttpUrl = Field(..., description="Video URL to download")

    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
            }
        }

class DownloadResponse(BaseModel):
    status: str
    message: str
    data: dict