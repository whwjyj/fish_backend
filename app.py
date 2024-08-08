from flask import Flask, request, jsonify
from flask_cors import CORS
from ultralytics import YOLO
import cv2
import numpy as np

app = Flask(__name__)
CORS(app)

# YOLOv8 모델 로드
model = YOLO("models/yolov8n_best.pt")

def preprocess_image(contents):
    # 바이트 스트림을 numpy 배열로 변환
    nparr = np.frombuffer(contents, np.uint8)
    # OpenCV를 사용하여 이미지를 디코딩
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return img

def postprocess_results(results):
    # YOLO 모델의 예측 결과에서 필요한 정보 추출
    labels = []
    boxes = []
    confidences = []

    for result in results.boxes:
        xyxy = result.xyxy.numpy().astype(int).tolist()[0]  # 바운딩 박스 좌표
        confidence = result.conf.numpy().tolist()[0]  # 신뢰도
        label = result.cls.numpy().tolist()[0]  # 클래스 라벨

        boxes.append(xyxy)
        confidences.append(confidence)
        labels.append(label)

    return {"labels": labels, "boxes": boxes, "confidences": confidences}

@app.route('/predict', methods=['POST'])
def predict():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    contents = file.read()
    img = preprocess_image(contents)

    # 디버깅: 전처리된 이미지 출력
    print("Preprocessed image shape:", img.shape)

    results = model(img)[0]  # 첫 번째 결과 가져오기

    # 디버깅: 모델 결과 출력
    print("Model raw results:", results)

    processed_results = postprocess_results(results)

    # 디버깅: 후처리된 결과 출력
    print("Processed results:", processed_results)

    return jsonify(processed_results)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)