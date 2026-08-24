import os
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Initialize the SQLAlchemy instance targeting Flask context compatibility
db = SQLAlchemy()
migrate = Migrate()
# Helper to fetch database connection URI
# def get_database_url() -> str:
#     return os.getenv(
#         "DATABASE_URL",
#         "postgresql://postgres:postgres@localhost:5432/regulatory_db"
#     )


# Migrate for the database schema changes
# inSTall Flask-Migrate if not already installed
# pip install Flask-Migrate
# Step a flask db init(only at first)
# Step B: Run this every single time you add/edit/delete a column or model
# flask db migrate -m "Added phone_number column to user table"

# # Step C: Run this to actually apply those structural updates directly to your database
# flask db upgrade
