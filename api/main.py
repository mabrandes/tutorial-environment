from fastapi import FastAPI
import psycopg2
import os

app = FastAPI()

def get_connection():
    return psycopg2.connect(
        host=os.environ["DB_HOST"],
        port=os.environ["DB_PORT"],
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
    )

@app.get("/")
def read_root():
    return {"message": "API is running!"}

@app.get("/tables")
def list_tables():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""SELECT table_name FROM information_schema.tables WHERE table_schema='public'""")
    tables = cur.fetchall()
    cur.close()
    conn.close()
    return {"tables": [t[0] for t in tables]}

@app.get("/query/{table_name}")
def query_table(table_name: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM {table_name}")
    rows = cur.fetchall()
    columns = [desc[0] for desc in cur.description]
    cur.close()
    conn.close()
    return {"columns": columns, "rows": rows}
