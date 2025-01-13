from flask import Flask, render_template, request, redirect, send_file, url_for, jsonify
from flask_pymongo import PyMongo
from models import User
from werkzeug.utils import secure_filename
from datetime import datetime
from bson import ObjectId
import os
import random
import string
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import cloudinary
import cloudinary.uploader
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from gridfs import GridFS
from bson import ObjectId
from gridfs import GridFS
import io


app = Flask(__name__)


app.config['SECRET_KEY'] = 'streamsphere'
app.config['MONGO_URI'] = "mongodb+srv://Ghulam:Ghulam1001@cluster0.eicmr.mongodb.net/streamsphere?retryWrites=true&w=majority"
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  

cloudinary.config(
    cloud_name="duku3zctg",
    api_key="179741952874928",
    api_secret="Y3BLT3yhO8ZrXUBKIuIrgAvPuB0"
)


mongo = PyMongo(app)
fs = GridFS(mongo.db)

ALLOWED_EXTENSIONS = {'mp4', 'mov', 'avi', 'webm'}
UPLOAD_FOLDER = 'static/profile_pics'
ALLOWED_EXTENSIONS_Pic = {'png', 'jpg', 'jpeg', 'gif'}

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
class User(UserMixin):
    def __init__(self, user_data):
        self.user_data = user_data
        self.id = str(user_data['_id'])
        self.username = user_data['username']
        self.role = user_data.get('role', 'user')

@login_manager.user_loader
def load_user(user_id):
    user_data = mongo.db.users.find_one({'_id': ObjectId(user_id)})
    return User(user_data) if user_data else None

@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        print("Login attempt for:", data['username'])
        
        user_data = mongo.db.users.find_one({'username': data['username']})
        print("Found user data:", user_data)
        
        if user_data and check_password_hash(user_data['password'], data['password']):
            print("Password verified successfully")
            user = User(user_data)
            login_user(user)
            
            return jsonify({
                'success': True,
                'username': user.username,
                'role': user.role
            })
        
        print("Password verification failed")
        return jsonify({'error': 'Invalid username or password'}), 401
        
    except Exception as e:
        print(f"Login error: {str(e)}")
        return jsonify({'error': str(e)}), 500
    
@app.route('/register', methods=['POST']) 
def register():
    try:
        data = request.get_json()
        print("Register attempt:", data['username']) 
        
        if mongo.db.users.find_one({'username': data['username']}):
            return jsonify({'error': 'Username already exists'}), 400
            
        user = {
            'username': data['username'],
            'password': generate_password_hash(data['password']),
            'role': data.get('role', 'user'),
            'created_at': datetime.utcnow()
        }
        
        mongo.db.users.insert_one(user)
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"Register error: {str(e)}")
        return jsonify({'error': str(e)}), 500
    
@login_manager.user_loader
def load_user(user_id):
    try:
        user_data = mongo.db.users.find_one({'_id': ObjectId(user_id)})
        return User(user_data) if user_data else None
    except Exception as e:
        print(f"Error loading user: {str(e)}")
        return None
    


def cleanup_cloudinary_video(public_id):
    try:
        cloudinary.uploader.destroy(public_id, resource_type="video")
    except Exception as e:
        print(f"Error deleting from Cloudinary: {str(e)}")

@app.teardown_appcontext
def cleanup_resources(exception=None):    
    pass



@app.route('/logout')
@login_required
def logout():
    try:
        logout_user()
        return jsonify({"success": True, "message": "Logged out successfully"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_unique_filename(original_filename):
    """Generate a unique filename while preserving the original extension."""
    ext = original_filename.rsplit('.', 1)[1].lower()
    random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"{timestamp}_{random_string}.{ext}"

def initialize_indexes():
    """Initialize indexes for better performance."""
    try:
        if 'videos' not in mongo.db.list_collection_names():
            mongo.db.create_collection('videos')

        mongo.db.videos.create_index([('created_at', -1)])
        mongo.db.videos.create_index([('user_id', 1)])
        print("Indexes created successfully")
    except Exception as e:
        print(f"Error creating indexes: {str(e)}")
        
   
    
@app.route('/')
def home():
    try:
        sort = request.args.get('sort', 'recent')
        page = request.args.get('page', 1, type=int)
        per_page = 10

        
        query = {}
        
        
        if sort == 'recent':
            sort_settings = [('created_at', -1)]
        elif sort == 'loved':
            sort_settings = [('likes', -1), ('created_at', -1)]
        else:  
            sort_settings = [('created_at', 1)]

        
        videos = list(
            mongo.db.videos.aggregate([
                {'$project': {
                    'title': 1,
                    'video_url': 1,
                    'username': 1,
                    'created_at': 1,
                    'user_id': 1,
                    'likes': 1,
                    'comments': 1,
                    'likes_count': {'$size': {'$ifNull': ['$likes', []]}},
                    'comments_count': {'$size': {'$ifNull': ['$comments', []]}}
                }},
                {'$sort': 
                    {'likes_count': -1} if sort == 'loved' 
                    else {'created_at': -1} if sort == 'recent'
                    else {'created_at': 1}
                },
                {'$skip': (page - 1) * per_page},
                {'$limit': per_page}
            ])
        )

        
        for video in videos:
            video['_id'] = str(video['_id'])
            video['user_id'] = str(video['user_id'])
            video['likes'] = [str(like) for like in video.get('likes', [])]

        
        total_videos = mongo.db.videos.count_documents(query)

        return render_template(
            'home.html',
            videos=videos,
            current_sort=sort,
            page=page,
            total_pages=(total_videos + per_page - 1) // per_page
        )
    except Exception as e:
        print(f"Error in home route: {str(e)}")
        return render_template('home.html', videos=[], page=1, total_pages=1)
    
    
@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        try:
            if 'file' not in request.files:
                print("No file in request.files")
                return jsonify({'error': 'No video file uploaded'}), 400
            
            video = request.files['file']
            if video.filename == '':
                print("Empty filename")
                return jsonify({'error': 'No selected file'}), 400

            print(f"Uploading file: {video.filename}")
            
            
            upload_result = cloudinary.uploader.upload(
            video,
            resource_type="video",
            folder="streamsphere_videos",  
            chunk_size=6000000,
            )

            print(f"Cloudinary upload result: {upload_result}")

            
            video_data = {
                'title': request.form.get('title', ''),
                'description': request.form.get('description', ''),
                'video_url': upload_result['secure_url'],
                'public_id': upload_result['public_id'],
                'user_id': ObjectId(current_user.id),
                'username': current_user.username,
                'created_at': datetime.utcnow(),
                'likes': [],
                'views': 0,
                'comments': []
            }
            
            result = mongo.db.videos.insert_one(video_data)
            print(f"MongoDB insert result: {result.inserted_id}")
            
            return jsonify({'success': True, 'message': 'Video uploaded successfully!'})

        except Exception as e:
            print(f"Upload error: {str(e)}")
            return jsonify({'error': str(e)}), 500

    return render_template('upload.html')

@app.route('/profile/<username>', methods=['GET'])
@app.route('/profile', methods=['GET'])
def profile(username=None):
    try:
        if username:
            user_data = mongo.db.users.find_one({'username': username})
            if not user_data:
                return redirect(url_for('home'))
            profile_user = User(user_data)
        else:
            if not current_user.is_authenticated:
                return redirect(url_for('home'))
            profile_user = current_user

        
        videos = list(mongo.db.videos.find({
            'user_id': ObjectId(profile_user.id)
        }).sort('created_at', -1))

        
        total_likes = sum(len(video.get('likes', [])) for video in videos)

        
        for video in videos:
            video['_id'] = str(video['_id'])
            video['likes'] = len(video.get('likes', []))
            video['comments'] = len(video.get('comments', []))

        return render_template('profile.html',
                            user=profile_user,
                            videos=videos,
                            total_likes=total_likes)
    except Exception as e:
        print(f"Profile error: {str(e)}")
        return redirect(url_for('home'))
    
@app.route('/update_profile_pic', methods=['POST'])
@login_required
def update_profile_pic():
    if 'profile_pic' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded'})
    
    file = request.files['profile_pic']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'})
        
    if file and allowed_file(file.filename):
        try:
            # Delete old profile picture if exists
            old_pic_id = current_user.user_data.get('profile_pic_id')
            if old_pic_id:
                try:
                    fs.delete(ObjectId(old_pic_id))
                except:
                    pass  # Ignore if old file doesn't exist

            # Store new picture in GridFS
            file_id = fs.put(
                file.read(),
                filename=secure_filename(f"{current_user.id}_{file.filename}"),
                content_type=file.content_type
            )
            
            # Update user profile with new file ID
            mongo.db.users.update_one(
                {'_id': ObjectId(current_user.id)},
                {'$set': {'profile_pic_id': str(file_id)}}
            )
            
            return jsonify({
                'success': True,
                'message': 'Profile picture updated successfully',
                'image_url': url_for('serve_profile_pic', file_id=str(file_id))
            })
            
        except Exception as e:
            print(f"Profile picture update error: {str(e)}")
            return jsonify({'success': False, 'error': str(e)})
    
    return jsonify({'success': False, 'error': 'Invalid file type'})

@app.route('/profile_pic/<file_id>')
def serve_profile_pic(file_id):
    try:
        file_data = fs.get(ObjectId(file_id))
        return send_file(
            io.BytesIO(file_data.read()),
            mimetype=file_data.content_type
        )
    except Exception as e:
        print(f"Error serving profile pic: {str(e)}")
        return send_file('static/default-avatar.png')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS_Pic
    
@app.route('/delete_video/<video_id>', methods=['POST'])
@login_required
def delete_video(video_id):
    try:
        video = mongo.db.videos.find_one({'_id': ObjectId(video_id)})
        
        if video and str(video['user_id']) == current_user.id:
            
            cloudinary.uploader.destroy(video['public_id'], resource_type="video")
            
            
            mongo.db.videos.delete_one({'_id': ObjectId(video_id)})
            
            return jsonify({'success': True, 'message': 'Video deleted successfully'})
            
        return jsonify({'error': 'Video not found or unauthorized'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500
@app.route('/like/<video_id>', methods=['POST'])
@login_required
def like_video(video_id):
    try:
        video = mongo.db.videos.find_one({'_id': ObjectId(video_id)})
        if not video:
            return jsonify({'error': 'Video not found'}), 404

        user_id = str(current_user.id)
        likes = [str(like) for like in video.get('likes', [])]
        
        if user_id in likes:
            mongo.db.videos.update_one(
                {'_id': ObjectId(video_id)},
                {'$pull': {'likes': ObjectId(user_id)}}
            )
        else:
            mongo.db.videos.update_one(
                {'_id': ObjectId(video_id)},
                {'$addToSet': {'likes': ObjectId(user_id)}}
            )
        
        updated_video = mongo.db.videos.find_one({'_id': ObjectId(video_id)})
        return jsonify({
            'likes': len(updated_video.get('likes', [])),
            'is_liked': user_id in [str(like) for like in updated_video.get('likes', [])]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/comment/<video_id>', methods=['POST'])
@login_required
def add_comment(video_id):
    try:
        data = request.get_json()
        comment = {
            'user_id': ObjectId(current_user.id),
            'username': current_user.username,
            'text': data['comment'],
            'timestamp': datetime.utcnow()
        }
        
        mongo.db.videos.update_one(
            {'_id': ObjectId(video_id)},
            {'$push': {'comments': comment}}
        )
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/comments/<video_id>', methods=['GET'])
def get_comments(video_id):
    try:
        video = mongo.db.videos.find_one({'_id': ObjectId(video_id)})
        if not video:
            return jsonify({'error': 'Video not found'}), 404
        
        comments = video.get('comments', [])
        
        for comment in comments:
            comment['user_id'] = str(comment['user_id'])
            
        return jsonify(comments)
    except Exception as e:
        print(f"Error fetching comments: {str(e)}")
        return jsonify({'error': str(e)}), 500
    
if __name__ == '__main__':
    
    initialize_indexes()
    app.run(debug=True)
