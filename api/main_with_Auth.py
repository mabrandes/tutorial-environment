from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import psycopg2
import os

# === App ===
app = FastAPI()

# === DB Connection ===
def get_connection():
    return psycopg2.connect(
        host=os.environ["DB_HOST"],
        port=os.environ["DB_PORT"],
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
    )

# === Auth Config ===
# When token is created, it gets this key assigned, to later check with requests check if token is generated here
SECRET_KEY = "Hasfk7&/%Sd_%$" 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# hashed passwords: encripted passwords
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_user_from_db(email):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(" SELECT id, name, email, password " \
                "FROM users " \
                "WHERE email = %s", (email,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    if row:
        user = {
            "id": row[0],
            "name": row[1],
            "email": row[2],
            "hashed_password": row[3],
        }
        return user

    return None

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def authenticate_user(email: str, password: str):

    user = get_user_from_db(email)

    if not user:
        return False
    
    if not verify_password(password, user["hashed_password"]):
        return False

    return user

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = get_user_from_db(email)
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# === Login endpoint ===
@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user["email"]})
    return {"access_token": access_token, "token_type": "bearer"}

# === Public root endpoint ===
@app.get("/")
def read_root():
    return {"message": "API is running!"}

# === Protected endpoint: list tables ===
@app.get("/tables")
def list_tables(current_user: dict = Depends(get_current_user)):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""SELECT table_name FROM information_schema.tables WHERE table_schema='public'""")
    tables = cur.fetchall()
    cur.close()
    conn.close()
    return {"tables": [t[0] for t in tables]}

# === Protected endpoint: query table ===
@app.get("/query/{table_name}")
def query_table(table_name: str, current_user: dict = Depends(get_current_user)):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM {table_name}")
    rows = cur.fetchall()
    columns = [desc[0] for desc in cur.description]
    cur.close()
    conn.close()
    return {"columns": columns, "rows": rows}
