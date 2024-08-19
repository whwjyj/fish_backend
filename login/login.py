from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

app.config['SECRET_KEY'] = 'projectsecret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mariadb+mariadbconnector://han:0000@ec2-3-38-242-92.ap-northeast-2.compute.amazonaws.com:3306/ex1'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.String(20), primary_key=True, nullable=False)
    name = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(255), nullable=False)  # 충분한 길이 설정
    clause_service = db.Column(db.String(1), nullable=False)
    clause_personal = db.Column(db.String(1), nullable=False)

@app.route('/join/check', methods=['POST'])
def clause():
    data = request.json
    input_cl1 = data.get('input_cl1')
    input_cl2 = data.get('input_cl2')

    if input_cl1 == 'y' and input_cl2 == 'y':
        return jsonify({"message": "next"})
    else:
        return jsonify({"message": "please agree all"})

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
            return jsonify({"message": "this ID is already in use"}), 409
        elif input_pw != input_pw_check:
            return jsonify({"message": "check your password"}), 400
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
