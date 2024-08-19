from flask_sqlalchemy import SQLAlchemy
from flask import Flask, request, jsonify
import jwt
import datetime
from datetime import timezone

app = Flask(__name__)

app.config['SECRET_KEY'] = 'projectsecret'

app.config['SQLALCHEMY_DATABASE_URI'] = 'mariadb+mariadbconnector://han:0000@ec2-3-38-242-92.ap-northeast-2.compute.amazonaws.com:3306/ex1'
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.String(20), primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)

class Result(db.Model):
    __tablename__ = 'result'
    id = db.Column(db.BigInteger, primary_key=True)
    pic1 = db.Column(db.LargeBinary, nullable=True)
    pic2 = db.Column(db.LargeBinary, nullable=True)
    user_id = db.Column(db.String(20), db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('results', lazy=True))

# user id 이용해서 access token, refresh token 발급
def create_token(userID):
    access_token = jwt.encode({
        'user_id' : userID,
        'exp' : datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)
    }, app.config['SECRET_KEY'], algorithm='HS256')

    refresh_token = jwt.encode({
        'user_id' : userID,
        'exp' : datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=60)
    }, app.config['SECRET_KEY'], algorithm='HS256')

    return access_token, refresh_token

#로그인 시도
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    input_id = data.get('input_id')
    input_pw = data.get('input_password')

    DB_id = User.query.filter_by(id=input_id).first()

    if DB_id :
        DB_pw = DB_id.password
        if DB_pw == input_pw : #로그인 성공시 access token, refresh token 생성
            access_token, refresh_token = create_token(DB_id.id)
            return jsonify({
                "message" : "login success",
				        "access_token": access_token,
				        "refresh_token": refresh_token
                })
        else :
            return jsonify({"message" : "password is different"})

    else :
        return jsonify({"message" : "no account"})

#access 토큰 만료시 r token 사용해 접근 /  a,r token 새로 생성
#r 만료된, 올바르지 않은 토큰 -> except 처리
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

#요구시 토큰 검증
def token_require(f):
    def decorated_func(*args, **kwargs):
        get_token = request.headers.get('Authorization')
        if get_token:
            token = get_token.split(" ")[1]
            payload = check_token(token)
            if not payload :
                return jsonify({"message" : "token is invalid or expired"})
        else :
            return jsonify({"message" : "token is no exist"})

        return f(*args, **kwargs)
    return decorated_func

def check_token(token) :
    try :
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        # UNIX 타임스탬프를 datetime 객체로 변환하여 비교
        exp_time = datetime.datetime.fromtimestamp(payload['exp'], tz=timezone.utc)
        if exp_time < datetime.datetime.now(timezone.utc) :
            return None
        return payload
    except jwt.InvalidTokenError :
        return None

@app.route('/protected', methods=['GET'])
@token_require
def protected():
    return jsonify({"message": "This is a protected route"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
