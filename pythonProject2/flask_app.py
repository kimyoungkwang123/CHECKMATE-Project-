import urllib.request

import cv2
import face_recognition
from flask import Flask, request, jsonify
import numpy as np
from PIL import Image, ExifTags
from io import BytesIO
from db_connect import connect
from traceback import format_exc

app = Flask(__name__)

@app.route('/receive_image', methods=['POST'])
def receive_image():
    print("요청을 받았습니다!")
    try:

        # 1. HTTP 요청에서 사용자 ID를 추출
        clickBtn=request.form.get("clickBtn")
        print("1번 : 출석, 2번 : 퇴근, 3번 : 외출, 4번 : 복귀 "+"\n버튼값 -> "+clickBtn)
        employee_no = request.form.get("no")
        print("직원 번호 : "+employee_no)
        print("=======================================")
        if not employee_no:
            raise ValueError("UserID header is missing")

        uploaded_image = process_image(request.files['image'])


        # 2. 사용자 ID를 load_db_image 함수에 전달
        db_image = load_db_image(employee_no)


        uploaded_encode, db_encode = get_encodings(uploaded_image, db_image)

        # compare_faces 함수의 로직을 여기에 넣기
        faceDis = face_recognition.face_distance([uploaded_encode], db_encode)
        similarity = 1 - faceDis[0]
        print("0 = 성공 1 = 실패")
        if similarity > 0.6:
            # 0은성공1은실패
            msg = "0"
            print("성공 여부 :"f" {msg} 유사도 ==> {similarity}")
        else:
            msg = "1"
            print("성공 여부 :"f" {msg} 유사도 ==> {similarity}")

            # JSON 응답 생성
        response = jsonify({
            "msg": msg,
            "clickBtn": clickBtn

        })
        response.status_code = 200  # HTTP 상태 코드 설정
        return response

    except Exception as e:
        print("Error:", str(e))
        print(format_exc())  # 오류의 traceback 출력
        return str(e), 500

def orient_image(img):
    try:
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == 'Orientation':
                break

        exif = img._getexif()  # 이미지의 Exif 데이터를 가져옵니다.
        if exif is not None and orientation in exif:
            orientation_value = exif[orientation]

            # Orientation 값에 따라 이미지를 회전합니다.
            if orientation_value == 2:
                img = img.transpose(Image.FLIP_LEFT_RIGHT)
            elif orientation_value == 3:
                img = img.rotate(180)
            elif orientation_value == 4:
                img = img.rotate(180).transpose(Image.FLIP_LEFT_RIGHT)
            elif orientation_value == 5:
                img = img.rotate(-90, expand=True).transpose(Image.FLIP_LEFT_RIGHT)
            elif orientation_value == 6:
                img = img.rotate(-90, expand=True)
            elif orientation_value == 7:
                img = img.rotate(90, expand=True).transpose(Image.FLIP_LEFT_RIGHT)
            elif orientation_value == 8:
                img = img.rotate(90, expand=True)
    except (AttributeError, KeyError, IndexError):
        # Exif 데이터가 없거나 유효하지 않은 경우 무시합니다.
        pass
    return img

# 안드로이드에서 가져온사진정보
def process_image(image_file):
    image_data = BytesIO(image_file.read())
    image = Image.open(image_data)

    # 이미지를 올바른 방향으로 회전시킵니다.
    image = orient_image(image)

    image_np = np.array(image)
    if image_np.shape[-1] == 4:
        image_np = cv2.cvtColor(image_np, cv2.COLOR_RGBA2RGB)
    return image_np

# db에 가져온 url정보
def load_db_image(employee_no):

    db_image_url = connect(employee_no)
    response = urllib.request.urlopen(db_image_url)
    db_image_data = response.read()
    db_image = Image.open(BytesIO(db_image_data))
    db_image_np = np.array(db_image)
    if db_image_np.shape[-1] == 4:
        db_image_np = cv2.cvtColor(db_image_np, cv2.COLOR_RGBA2RGB)
    return db_image_np

# db에가져온사진이랑 안드로이드에서 가져온사진을 face_recognition
def get_encodings(img1, img2):
    enc1 = face_recognition.face_encodings(img1, model='cnn')
    enc2 = face_recognition.face_encodings(img2, model='cnn')
    if not enc1:
        raise ValueError("No face detected in the uploaded image")
    if not enc2:
        raise ValueError("No face detected in the database image")
    return enc1[0], enc2[0]

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5005)