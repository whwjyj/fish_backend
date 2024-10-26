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
import os  # 추가된 부분

app = Flask(__name__)
CORS(app)

app.config['SECRET_KEY'] = 'projectsecret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mariadb+mariadbconnector://han:0000@ec2-3-38-242-92.ap-northeast-2.compute.amazonaws.com:3306/ex1'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

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

# YOLOv8 모델 로드
model = YOLO("/Users/joyongju/flask-/models/conv_parameter.pt")

fish_class = {
    0: '넙치',
    1: '연어',
    2: '도미',
    3: '방어',
    4: '참치',
    5: '전어',
    6: '전복',
    7: '농어',
    8: '민어',
    9: '갈치',
    10: '고등어',
    11: '문어',
    12: '볼락'
}

def preprocess_image(contents):
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return img

@app.route('/take_pic', methods=['POST'])
def take_pic():
    file = request.files['file']
    if not file:
        return jsonify({"message": "no img. retry"})

    get_token = request.headers.get('Authorization')
    if not get_token:
        return jsonify({"message": "no token"})

    token = get_token.split(" ")[1]
    payload = check_token(token)
    if not payload:
        return jsonify({"message": "Token: invalid or expired"})
    payload_id = payload['user_id']
    user = User.query.filter_by(id=payload_id).first()
    user_in = user.id

    original_byte = file.read()
    img = preprocess_image(original_byte)

    # YOLO 예측 수행
    results = model(img)[0]

    # 예측 결과 이미지 생성 및 인코딩
    result_np = results.plot()
    _, buffer = cv2.imencode('.jpg', result_np)
    result_byte = buffer.tobytes()
    send = base64.b64encode(buffer).decode('utf-8')

    # 예측된 물고기 이름 리스트 생성
    cls = results.boxes.cls.numpy().tolist()
    box_int = list(set(int(value) for value in cls))
    box_name = [fish_class[i] for i in fish_class if i in box_int]

    # 결과를 DB에 저장
    new_result = Result(user_id=user_in, pic1=original_byte, pic2=result_byte)
    db.session.add(new_result)
    db.session.commit()

    return jsonify({'image': send, "list": box_name})

# 결과 조회
@app.route('/get_result', methods=['POST'])
def get_result():
    get_token = request.headers.get('Authorization')
    if not get_token:
        return jsonify({"message": "no token"})

    token = get_token.split(" ")[1]
    payload = check_token(token)
    if not payload:
        return jsonify({"message": "Token : invalid or expired"})
    payload_id = payload['user_id']
    user = User.query.filter_by(id=payload_id).first()
    user_in = user.id

    user_results = Result.query.filter_by(user_id=user_in).all()

    if not user_results:
        return jsonify({'message': 'no result'})

    pics = []
    for result in user_results:
        if result.pic2:
            buffer = np.frombuffer(result.pic2, dtype=np.ubyte)
            pic = base64.b64encode(buffer).decode('utf-8')
            pics.append(pic)

    return jsonify(pics)

# 이미지 삭제 기능 추가
@app.route('/delete_images', methods=['POST'])
def delete_images():
    data = request.json
    indices = data.get('indices')

    if not indices:
        return jsonify({'error': 'No images specified'}), 400

    get_token = request.headers.get('Authorization')
    if not get_token:
        return jsonify({"message": "no token"})

    token = get_token.split(" ")[1]
    payload = check_token(token)
    if not payload:
        return jsonify({"message": "Token: invalid or expired"})
    payload_id = payload['user_id']

    try:
        for index in indices:
            # 인덱스에 해당하는 이미지 레코드를 가져오기
            result = Result.query.filter_by(user_id=payload_id).offset(index).first()
            if result:
                db.session.delete(result)  # 레코드 삭제
                # 여기서 파일 시스템에서 실제 이미지 파일을 삭제하는 로직 추가 가능
        db.session.commit()
        return jsonify({'message': 'Images deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# 회원가입 시 약관 동의 체크
@app.route('/join/check', methods=['POST'])
def clause():
    data = request.json
    input_cl1 = data.get('input_cl1')
    input_cl2 = data.get('input_cl2')

    if input_cl1 == 'y' and input_cl2 == 'y':
        return jsonify({"message": "next"}), 200
    else:
        return jsonify({"message": "필수동의 체크해주세요."}), 400

# 회원가입
@app.route('/join/information', methods=['POST'])
def information():
    data = request.json
    input_id = data.get('input_id')
    input_name = data.get('input_name')
    input_pw = data.get('input_password')
    input_pw_check = data.get('input_password_check')

    if not input_name or not input_id or not input_pw or not input_pw_check:
        return jsonify({"message": "input all"}), 400
    else:
        DB_id = User.query.filter_by(id=input_id).first()
        if DB_id:
            return jsonify({"message": "이미 있는 아이디 입니다."}), 409
        elif input_pw != input_pw_check:
            return jsonify({"message": "비밀번호를 확인해 주세요."}), 400
        else:
            try:
                hashed_password = generate_password_hash(input_pw, method='sha256')
                new_user = User(id=input_id, name=input_name, password=hashed_password, clause_service='Y', clause_personal='Y')
                db.session.add(new_user)
                db.session.commit()
                return jsonify({"message": "success"}), 201
            except Exception as e:
                db.session.rollback()
                return jsonify({"message": "error", "details": str(e)}), 500

# 로그인 시도
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    input_id = data.get('input_id')
    input_pw = data.get('input_password')

    DB_id = User.query.filter_by(id=input_id).first()

    if DB_id:
        if check_password_hash(DB_id.password, input_pw):
            access_token, refresh_token = create_token(DB_id.id)
            return jsonify({
                "message": "login success",
                "access_token": access_token,
                "refresh_token": refresh_token
            })
        else:
            return jsonify({"message": "password is different"})
    else:
        return jsonify({"message": "no account"})

# user id 이용해서 access token, refresh token 발급
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

# access 토큰 만료 시 r token 사용해 접근 / a,r token 새로 생성
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
        return jsonify({"message": "Refresh token expired"})
    except jwt.InvalidTokenError:
        return jsonify({"message": "Invalid token"})

# 요구 시 토큰 검증
def token_require(f):
    def decorated_func(*args, **kwargs):
        get_token = request.headers.get('Authorization')
        if get_token:
            token = get_token.split(" ")[1]
            payload = check_token(token)
            if not payload:
                return jsonify({"message": "token is invalid or expired"})
        else:
            return jsonify({"message": "token is no exist"})

        return f(*args, **kwargs)
    return decorated_func

def check_token(token):
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        exp_time = datetime.datetime.fromtimestamp(payload['exp'], tz=timezone.utc)
        if exp_time < datetime.datetime.now(timezone.utc):
            return None
        return payload
    except jwt.InvalidTokenError:
        return None

@app.route('/protected', methods=['GET'])
@token_require
def protected():
    return jsonify({"message": "This is a protected route"})

# 회원 탈퇴 기능
@app.route('/unregister', methods=['POST'])
def unregister():
    get_token = request.headers.get('Authorization')
    if not get_token:
        return jsonify({"message": "no token"})

    token = get_token.split(" ")[1]
    payload = check_token(token)
    if not payload:
        return jsonify({"message": "Token: invalid or expired"})

    payload_id = payload['user_id']
    user = User.query.filter_by(id=payload_id).first()

    data = request.json
    input_pw = data.get('input_pw')
    input_pw_re = data.get('input_pw_re')

    if not input_pw or not input_pw_re:
        return jsonify({"message": "input all"})
    if input_pw != input_pw_re:
        return jsonify({"message": "enter the same password"})

    try:
        if check_password_hash(user.password, input_pw):  # 해시된 비밀번호 비교
            db.session.delete(user)
            db.session.commit()
            return jsonify({"message": "delete success"})
        else:
            return jsonify({"message": "incorrect password"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "error", "details": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
