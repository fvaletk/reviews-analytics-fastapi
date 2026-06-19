from typing import Optional

from pydantic import BaseModel, model_validator


class ScrapeRequest(BaseModel):
    app_store_id: Optional[str] = None
    app_store_country: Optional[str] = "us"
    play_store_id: Optional[str] = None
    max_reviews: int = 500

    @model_validator(mode="after")
    def at_least_one_store(self) -> "ScrapeRequest":
        if not self.app_store_id and not self.play_store_id:
            raise ValueError("At least one of app_store_id or play_store_id is required")
        return self


class ScrapeResponse(BaseModel):
    reviews: list[dict]
    errors: list[str]
    partial: bool
    app_store_count: int
    play_store_count: int
