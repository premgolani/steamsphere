from flask import Flask
from flask_pymongo import PyMongo
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)


app.config['MONGO_URI'] = "mongodb+srv://Ghulam:Ghulam1001@cluster0.eicmr.mongodb.net/streamsphere?retryWrites=true&w=majority"
mongo = PyMongo(app)


try:
    
    mongo.db.command('ping')
    print("MongoDB connected successfully!")
    
    
    mongo.db.test.insert_one({"test": "connection"})
    print("Write test successful!")
    
    
    mongo.db.test.delete_one({"test": "connection"})
    
except Exception as e:
    print(f"MongoDB connection error: {str(e)}")
    exit(1)


with app.app_context():
    try:
        mongo.db.users.create_index('username', unique=True)
        print("Database indexes created successfully!")
    except Exception as e:
        print(f"Error creating indexes: {str(e)}")