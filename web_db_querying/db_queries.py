from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
import os

app = FastAPI()

# Allow all origins for CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)

#
# Use Heroku PostgreSQL connection
postgres_url = os.environ["DATABASE_URL"]
if postgres_url.startswith("postgres://"):
    postgres_url = postgres_url.replace("postgres://", "postgresql://", 1)

engine = create_engine(postgres_url)
@app.get("/table/{table_name}/{column_name}/{value}")
def query_by_column_value(table_name: str, column_name: str, value: str):
    try:
        with engine.connect() as conn:
            query = text(f"SELECT * FROM {table_name} WHERE {column_name} = :val")
            result = conn.execute(query, {"val": value})
            return [dict(row._mapping) for row in result]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@app.get("/table/{table_name}/{column_name}")
def query_by_column(table_name: str, column_name: str):
    try:
        with engine.connect() as conn:
            query = text(f"SELECT {column_name} FROM {table_name}")
            result = conn.execute(query)
            return [dict(row._mapping) for row in result]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@app.get("/table/{table_name}")
def query_table(table_name: str):
    try:
        with engine.connect() as conn:
            query = text(f"SELECT * FROM {table_name}")
            result = conn.execute(query)
            return [dict(row._mapping) for row in result]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    


#Placeholders
@app.get("/tables")
def list_tables():
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE';"
        ))
        return [row[0] for row in result]

@app.get("/query")
def query_table(table: str, column: str = None):
    try:
        with engine.connect() as conn:
            if column:
                query = text(f"SELECT {column} FROM {table}")
            else:
                query = text(f"SELECT * FROM {table}")
            result = conn.execute(query)
            return [dict(row._mapping) for row in result]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))