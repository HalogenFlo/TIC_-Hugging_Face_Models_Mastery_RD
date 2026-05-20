from pydantic import BaseModel, Field

class Banking77Request(BaseModel):
    text: str = Field(description="The costumer message to classify.")