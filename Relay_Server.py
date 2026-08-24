from flask import Flask, request, Response
import threading
import time
 
app = Flask(__name__)
 
latest_frame = None
frame_lock = threading.Lock()
last_update_time = 0
 
@app.route('/upload', methods=['POST'])
def upload():
    """ESP32-CAM이 여기로 JPEG 프레임을 POST 함"""
    global latest_frame, last_update_time
    with frame_lock:
        latest_frame = request.data
        last_update_time = time.time()
    return "OK", 200
 
def generate():
    """MJPEG 멀티파트 스트림 생성기"""
    while True:
        with frame_lock:
            frame = latest_frame
        if frame is not None:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        time.sleep(0.08)  # 서버 부하 조절용, 필요시 조정
 
@app.route('/stream')
def stream():
    return Response(generate(),
                     mimetype='multipart/x-mixed-replace; boundary=frame')
 
@app.route('/')
def index():
    """핸드폰 브라우저로 열어서 보는 페이지"""
    return '''
    <html>
      <head><title>ESP32-CAM 실시간 영상</title></head>
      <body style="margin:0;background:#111;text-align:center;">
        <img src="/stream" style="max-width:100%;margin-top:20px;">
      </body>
    </html>
    '''
 
@app.route('/status')
def status():
    with frame_lock:
        has_frame = latest_frame is not None
        age = time.time() - last_update_time if last_update_time else None
    return {"has_frame": has_frame, "last_frame_age_sec": age}
 
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
