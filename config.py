# config.py - environment/configuration helpers
import os
class Config:
    DB_HOST = os.getenv("DB_HOST","localhost")
    DB_USER = os.getenv("DB_USER","root")
    DB_PASSWORD = os.getenv("DB_PASSWORD","Ecommerce@1")
    DB_NAME = os.getenv("DB_NAME","student_placement_system")
    JWT_SECRET = os.getenv("JWT_SECRET","change_this_secret")