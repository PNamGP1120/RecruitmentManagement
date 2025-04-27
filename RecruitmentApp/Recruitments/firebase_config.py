import firebase_admin
from firebase_admin import credentials
from firebase_admin import db  # Import trực tiếp db từ firebase_admin
import os

# Lấy đường dẫn tuyệt đối đến tệp JSON cấu hình Firebase của bạn
FIREBASE_CREDENTIAL_PATH = os.path.join(os.path.dirname(__file__), "recruitmentchat-firebase.json")

cred = credentials.Certificate(FIREBASE_CREDENTIAL_PATH)

try:
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://recruitmentchat-a3fde-default-rtdb.firebaseio.com/'
    })
    print("Firebase Admin SDK đã được khởi tạo thành công với databaseURL được cung cấp!")
except Exception as e:
    print(f"Lỗi khi khởi tạo Firebase Admin SDK: {e}")

ref = db.reference()