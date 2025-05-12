echo "Starting Heroku build at $(date)"
release: python web_db_querying/app.py
echo "Completed Heroku build at $(date)"

echo "Started query at $(date)"
web: uvicorn web_db_querying.db_queries:app --host=0.0.0.0 --port=${PORT:-5000}
echo "Completed query at $(date)"