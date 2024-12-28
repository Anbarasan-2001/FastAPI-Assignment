from decouple import config

MONGO_URI                   = config("MONGO_URI")
SECRET_KEY                  = config("SECRET_KEY")
ALGORITHM                   = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS   = 30
