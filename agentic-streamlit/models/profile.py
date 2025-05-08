from pydantic import BaseModel

class UserProfile(BaseModel):
    name: str
    bio: str
    urls: str
    stances: str
    tone: str
    post_freq: str
    avoid_topics: str