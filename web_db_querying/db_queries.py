from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, text

app = FastAPI()

# Adjust path to go from /web_db_querying/ to /data/database/
engine = create_engine("sqlite:///data/database/courses.db", connect_args={"check_same_thread": False})

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
            query = text(f"SELECT * FROM {table_name} LIMIT 10")
            result = conn.execute(query)
            return [dict(row._mapping) for row in result]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    


#Placeholders
@app.get("/tables")
def list_tables():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
        return [row[0] for row in result]

@app.get("/query")
def query_table(table: str, column: str = None):
    try:
        with engine.connect() as conn:
            if column:
                query = text(f"SELECT {column} FROM {table} LIMIT 10")
            else:
                query = text(f"SELECT * FROM {table} LIMIT 10")
            result = conn.execute(query)
            return [dict(row._mapping) for row in result]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))