from flask_login import UserMixin
from bson import ObjectId

class User(UserMixin):
    def __init__(self, user_data):
        if user_data:
            self.user_data = user_data
            self.id = str(user_data['_id'])
            self.username = user_data['username']
            self.role = user_data.get('role', 'consumer')
            
            
        else:
            raise ValueError("User data cannot be None")

    def get_id(self):
        return str(self.id)