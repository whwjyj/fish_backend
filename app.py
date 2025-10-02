# app.py
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
from datetime import timezone
from ultralytics import YOLO
import cv2
import numpy as np
import base64
import os
import io
import threading
import time
from concurrent.futures import ThreadPoolExecutor, Future, TimeoutError


app = Flask(__name__)
CORS(app)

app.config['SECRET_KEY'] = 'projectsecret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mariadb+mariadbconnector://han:0000@ec2-3-38-242-92.ap-northeast-2.compute.amazonaws.com:3306/ex1'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# ✅ 업로드 최대 크기 (예시 10MB)

db = SQLAlchemy(app)

# DB Models

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.String(20), primary_key=True, nullable=False)
    name = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    clause_service = db.Column(db.String(1), nullable=False)
    clause_personal = db.Column(db.String(1), nullable=False)
    result = db.relationship('Result', cascade='all, delete-orphan', overlaps="results")

class Result(db.Model):
    __tablename__ = 'result'
    id = db.Column(db.BigInteger, primary_key=True, nullable=False, autoincrement=True)
    pic1 = db.Column(db.LargeBinary, nullable=True)
    pic2 = db.Column(db.LargeBinary, nullable=True)
    user_id = db.Column(db.String(20), db.ForeignKey('user.id', ondelete='cascade'), nullable=False)
    user = db.relationship('User', backref=db.backref('results', lazy=True), overlaps="result")


# ✅ 모델은 앱 시작 시 한 번만 로드 — 반복 로드 비용 제거
MODEL_PATH = os.getenv('YOLO_MODEL_PATH', '/Users/joyongju/flask-/models/conv_parameter.pt')
model = YOLO(MODEL_PATH)

# 모델 디바이스 확인(권장: GPU 사용 시 빠름)
try:
    device_info = model.model.device
except Exception:
    device_info = None

# 어종 매핑
fish_class = {
    0: '넙치', 1: '연어', 2: '도미', 3: '방어', 4: '참치',
    5: '전어', 6: '전복', 7: '농어', 8: '민어', 9: '갈치',
    10: '고등어', 11: '문어', 12: '볼락'
}

def create_token(userID):
    access_token = jwt.encode({
        'user_id': userID,
        'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)
    }, app.config['SECRET_KEY'], algorithm='HS256')

    refresh_token = jwt.encode({
        'user_id': userID,
        'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=60)
    }, app.config['SECRET_KEY'], algorithm='HS256')

    return access_token, refresh_token

def check_token(token):
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        exp_time = datetime.datetime.fromtimestamp(payload['exp'], tz=timezone.utc)
        if exp_time < datetime.datetime.now(timezone.utc):
            return None
        return payload
    except jwt.InvalidTokenError:
        return None

def token_required_func():
    def decorator(f):
        def wrapper(*args, **kwargs):
            get_token = request.headers.get('Authorization')
            if not get_token:
                return jsonify({"message": "no token"}), 401
            try:
                token = get_token.split(" ")[1]
            except Exception:
                return jsonify({"message": "token format invalid"}), 401
            payload = check_token(token)
            if not payload:
                return jsonify({"message": "Token: invalid or expired"}), 401
            return f(payload, *args, **kwargs)
        wrapper.__name__ = f.__name__
        return wrapper
    return decorator


def preprocess_image_bytes(contents: bytes, max_size: int = 800):

    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Could not decode image")
    h, w = img.shape[:2]
    max_dim = max(h, w)
    if max_dim > max_size:
        scale = max_size / max_dim
        new_w = int(w * scale)
        new_h = int(h * scale)
        img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
    return img

def encode_image_jpeg(img, quality=80)

    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
    success, buffer = cv2.imencode('.jpg', img, encode_param)
    if not success:
        raise ValueError("Failed to encode image")
    return buffer.tobytes()

# ✅ 작은 고정 풀을 만들어 과도한 쓰레드 생성 방지
EXECUTOR = ThreadPoolExecutor(max_workers=4)
JOB_STORE = {}
JOB_LOCK = threading.Lock()

def inference_and_save(user_id: str, original_bytes: bytes, job_id: str, quality=80):
    start = time.time()
    try:
        img = preprocess_image_bytes(original_bytes, max_size=800)
        results = model(img)[0]
        result_np = results.plot()
        # compress result image
        result_bytes = encode_image_jpeg(result_np, quality=quality)
        cls = []
        try:
            cls = results.boxes.cls.numpy().tolist()
            box_int = list(set(int(value) for value in cls))
            box_name = [fish_class[i] for i in fish_class if i in box_int]
        except Exception:
            box_name = []

        try:
            new_result = Result(user_id=user_id, pic1=original_bytes, pic2=result_bytes)
            db.session.add(new_result)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"[inference_and_save] DB error: {e}")

        elapsed = time.time() - start
        return {"status": "success", "list": box_name, "elapsed_ms": int(elapsed*1000)}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# API

@app.route('/take_pic', methods=['POST'])
@token_required_func()
def take_pic(payload):

    if 'file' not in request.files:
        return jsonify({"message": "no img. retry"}), 400

    file = request.files['file']
    get_token = request.headers.get('Authorization')
    token = get_token.split(" ")[1]
    payload_id = payload['user_id']

    original_bytes = file.read()
    if len(original_bytes) > 10 * 1024 * 1024:
        return jsonify({"message": "file too large"}), 413

    start_total = time.time()
    try:
        img = preprocess_image_bytes(original_bytes, max_size=800)
        t0 = time.time()
        results = model(img)[0]
        t1 = time.time()
        result_np = results.plot()
        result_bytes = encode_image_jpeg(result_np, quality=80)
        send = base64.b64encode(result_bytes).decode('utf-8')
        try:
            cls = results.boxes.cls.numpy().tolist()
            box_int = list(set(int(value) for value in cls))
            box_name = [fish_class[i] for i in fish_class if i in box_int]
        except Exception:
            box_name = []

        # DB save (wrapped)
        try:
            new_result = Result(user_id=payload_id, pic1=original_bytes, pic2=result_bytes)
            db.session.add(new_result)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"[take_pic] DB save error: {e}")

        total_elapsed_ms = int((time.time() - start_total)*1000)
        infer_elapsed_ms = int((t1 - t0)*1000)
        return jsonify({
            'image': send,
            'list': box_name,
            'timing': {'inference_ms': infer_elapsed_ms, 'total_ms': total_elapsed_ms}
        })
    except Exception as e:
        return jsonify({"message": "processing error", "details": str(e)}), 500


# API

@app.route('/take_pic_async', methods=['POST'])
@token_required_func()
def take_pic_async(payload):
    if 'file' not in request.files:
        return jsonify({"message": "no img. retry"}), 400

    file = request.files['file']
    original_bytes = file.read()
    if len(original_bytes) > 10 * 1024 * 1024:
        return jsonify({"message": "file too large"}), 413

    job_id = f"job-{int(time.time()*1000)}-{threading.get_ident()}"
    future: Future = EXECUTOR.submit(inference_and_save, payload['user_id'], original_bytes, job_id, 80)
    with JOB_LOCK:
        JOB_STORE[job_id] = future
    return jsonify({"job_id": job_id, "message": "Accepted"}), 202

@app.route('/job_result/<job_id>', methods=['GET'])
def job_result(job_id):
    with JOB_LOCK:
        future = JOB_STORE.get(job_id)
    if not future:
        return jsonify({"message": "job not found"}), 404

    if future.done():
        result = future.result()
        with JOB_LOCK:
            JOB_STORE.pop(job_id, None)
        return jsonify(result)
    else:
        return jsonify({"status": "running"}), 202

@app.route('/get_result', methods=['POST'])
@token_required_func()
def get_result(payload):
    payload_id = payload['user_id']
    user_results = Result.query.filter_by(user_id=payload_id).all()
    if not user_results:
        return jsonify({'message': 'no result'})
    pics = []
    for result in user_results:
        if result.pic2:
            buffer = np.frombuffer(result.pic2, dtype=np.ubyte)
            pic = base64.b64encode(buffer).decode('utf-8')
            pics.append(pic)
    return jsonify(pics)

@app.route('/delete_images', methods=['POST'])
@token_required_func()
def delete_images(payload):
    data = request.json
    indices = data.get('indices')
    if not indices:
        return jsonify({'error': 'No images specified'}), 400
    payload_id = payload['user_id']
    try:
        for index in indices:
            result = Result.query.filter_by(user_id=payload_id).offset(index).first()
            if result:
                db.session.delete(result)
        db.session.commit()
        return jsonify({'message': 'Images deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/join/check', methods=['POST'])
def clause():
    data = request.json
    input_cl1 = data.get('input_cl1')
    input_cl2 = data.get('input_cl2')
    if input_cl1 == 'y' and input_cl2 == 'y':
        return jsonify({"message": "next"}), 200
    else:
        return jsonify({"message": "필수동의 체크해주세요."}), 400

@app.route('/join/information', methods=['POST'])
def information():
    data = request.json
    input_id = data.get('input_id')
    input_name = data.get('input_name')
    input_pw = data.get('input_password')
    input_pw_check = data.get('input_password_check')
    if not input_name or not input_id or not input_pw or not input_pw_check:
        return jsonify({"message": "input all"}), 400
    DB_id = User.query.filter_by(id=input_id).first()
    if DB_id:
        return jsonify({"message": "이미 있는 아이디 입니다."}), 409
    if input_pw != input_pw_check:
        return jsonify({"message": "비밀번호를 확인해 주세요."}), 400
    try:
        hashed_password = generate_password_hash(input_pw, method='sha256')
        new_user = User(id=input_id, name=input_name, password=hashed_password, clause_service='Y', clause_personal='Y')
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"message": "success"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "error", "details": str(e)}), 500

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    input_id = data.get('input_id')
    input_pw = data.get('input_password')
    DB_id = User.query.filter_by(id=input_id).first()
    if DB_id and check_password_hash(DB_id.password, input_pw):
        access_token, refresh_token = create_token(DB_id.id)
        return jsonify({
            "message": "login success",
            "access_token": access_token,
            "refresh_token": refresh_token
        })
    elif DB_id:
        return jsonify({"message": "password is different"}), 401
    else:
        return jsonify({"message": "no account"}), 404

@app.route('/token/refresh', methods=['POST'])
def refresh_token():
    data = request.json
    refresh_token = data.get('refresh_token')
    try:
        decoded_token = jwt.decode(refresh_token, app.config['SECRET_KEY'], algorithms=['HS256'])
        userID = decoded_token['user_id']
        access_token, new_refresh_token = create_token(userID)
        return jsonify({"access_token": access_token, "refresh_token": new_refresh_token})
    except jwt.ExpiredSignatureError:
        return jsonify({"message": "Refresh token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"message": "Invalid token"}), 401

@app.route('/protected', methods=['GET'])
@token_required_func()
def protected(payload):
    return jsonify({"message": "This is a protected route", "user": payload['user_id']})

@app.route('/unregister', methods=['POST'])
@token_required_func()
def unregister(payload):
    payload_id = payload['user_id']
    data = request.json
    input_pw = data.get('input_pw')
    input_pw_re = data.get('input_pw_re')
    if not input_pw or not input_pw_re:
        return jsonify({"message": "input all"}), 400
    if input_pw != input_pw_re:
        return jsonify({"message": "enter the same password"}), 400
    user = User.query.filter_by(id=payload_id).first()
    try:
        if user and check_password_hash(user.password, input_pw):
            db.session.delete(user)
            db.session.commit()
            return jsonify({"message": "delete success"})
        else:
            return jsonify({"message": "incorrect password"}), 401
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "error", "details": str(e)}), 500


# Run
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
