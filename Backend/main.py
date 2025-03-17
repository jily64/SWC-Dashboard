from fastapi import FastAPI, Depends
from fastapi.responses import RedirectResponse
from fastapi.exceptions import HTTPException
from fastapi.security import OAuth2AuthorizationCodeBearer
from adapters import DBadapter
import httpx
import os
from dotenv import load_dotenv
from models import Bases

load_dotenv()

app = FastAPI()

oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl="https://discord.com/api/oauth2/authorize",
    tokenUrl="https://discord.com/api/oauth2/token",
)

CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI")

POSTGRES_DBNAME = os.getenv("POSTGRES_DBNAME")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")
POSTGRES_SCHEMA_NAME = os.getenv("POSTGRES_SCHEMA_NAME")

BOT_TOKEN =os.getenv("BOT_TOKEN")

db = DBadapter.Adapter(host=POSTGRES_HOST, port=POSTGRES_PORT, dbname=POSTGRES_DBNAME, schema_name=POSTGRES_SCHEMA_NAME, user=POSTGRES_USER, password=POSTGRES_PASSWORD)
db.connect()

@app.get("/auth/discord")
async def login():
    return RedirectResponse(
        f"https://discord.com/api/oauth2/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&response_type=code&scope=identify+guilds+email+guilds.members.read"
    )

@app.get("/auth/discord/callback")
async def callback(code: str):
    async with httpx.AsyncClient() as client:
        # Обмен кода на токен
        token_response = await client.post(
            "https://discord.com/api/oauth2/token",
            data={
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": REDIRECT_URI,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        
        token_data = token_response.json()
        access_token = token_data.get("access_token")

        user_response = await client.get(
            "https://discord.com/api/users/@me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        
        user_data = user_response.json()

        guilds_response = await client.get(
            "https://discord.com/api/users/@me/guilds",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        
        guilds_data = guilds_response.json()

        member_response = await client.get(
            f"https://discord.com/api/guilds/691788414101618819/members/{user_data['id']}",
            headers={"Authorization": f"Bot {BOT_TOKEN}"},
        )
            
        member_data = member_response.json()

        check_if_user_exists = db.select(table='users', where_clause=f"ds_id='{user_data["id"]}'")

        if check_if_user_exists != []:
            to_db = {
            "username": user_data['username'],
            "global_name": user_data["global_name"],
            "avatar_url": user_data['avatar']
            }
            db.update(table='users', where_clause=f"ds_id='{user_data['id']}'", updates=to_db)
        else:
            to_db = {
                "ds_id": user_data['id'],
                "username": user_data['username'],
                "global_name": user_data["global_name"],
                "avatar_url": user_data['avatar']
            }

            db.insert(table='users', data=to_db)

        return {"user": user_data, "member_data": member_data}

@app.get("/api/user/{id}")
async def get_user(id:str):
    user = db.select(table='users', where_clause=f"ds_id='{id}'")

    if user == []:
        raise HTTPException(status_code=404, detail="No user with such ID")
    
    user = user[0]
    user = {
        "id": user[0],
        "ds_id": user[1],
        "global_name": user[2],
        "username": user[3],
        "avatar_url": user[4],
    }
    return Bases.User(**user)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

