# Hive-server/models/base.py

from sqlalchemy.ext.declarative import declarative_base

# Base class for all SQLAlchemy declarative models.
# All your ORM models will inherit from this.
Base = declarative_base()