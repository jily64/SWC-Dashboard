from pydantic import BaseModel

class User(BaseModel):
    ds_id:str
    username:str
    global_name:str
    avatar_url:str