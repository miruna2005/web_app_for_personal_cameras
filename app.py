import os
import json
import cv2
from flask import Flask,jsonify,render_template,send_from_directory,Response
from storage import get_cale_inregistrari,config
app=Flask(__name__)
@app.route("/")
def index():
    return render_template("index.html")
@app.route("/api/status")
def get_status():
    _,e_pe_usb=get_cale_inregistrari()
    if e_pe_usb:
        mesaj="Stocare pe USB"
        stare="ok"
    else:
        mesaj="Stick deconectat.Stocare pe memoria interna!"
        stare="!"
    return jsonify({
        "stocare_usb":e_pe_usb,
        "mesaj":mesaj,
        "stare":stare
    })
@app.route("/api/events")
def get_events():
    cale_folder,_=get_cale_inregistrari()
    cale_json=os.path.join(cale_folder,config["stocare"]["fisier_evenimente"])
    if not os.path.exists(cale_json):
        return jsonify([])
    try:
        with open(cale_json,"r") as f:
            evenimente=json.load(f)
            evenimente.reverse()
            return jsonify(evenimente)
    except Exception as e:
        print(f"nu s a putut citi events.json",flush=True)
        return jsonify([])
@app.route("/video/<path:nume_fisier>")
def get_video(nume_fisier):
    cale_folder,_=get_cale_inregistrari()
    return send_from_directory(cale_folder,nume_fisier,mimetype='video/mp4')
@app.route("/api/cameras")
def get_cameras():
    camere_list = []
    for id_cam, detalii in config.get('camere', {}).items():
        camere_list.append({
            'id': id_cam,
            'nume': id_cam.replace('.', ' ').upper(),
            'activa': detalii.get('activa', False)
        })
        
    return jsonify(camere_list)
def genereaza_cadre(url_stream):
    os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"
    cap = cv2.VideoCapture(url_stream, cv2.CAP_FFMPEG)
    
    if not cap.isOpened():
        print("-> EROARE: OpenCV nu a putut deschide deloc streamul!", flush=True)
        return

    print("-> SUCCES: Stream-ul a fost deschis, încerc să citesc primul cadru...", flush=True)
    
    success, frame = cap.read()
    if not success:
        print("-> EROARE: S-a deschis conexiunea, dar cap.read() a returnat False (cadru gol)!", flush=True)
        cap.release()
        return

    print("-> SUCCES TOTAL: Primul cadru a fost citit cu succes!", flush=True)
    
    while True:
        success, frame = cap.read()
        if not success:
            break
        ret, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
@app.route("/video_feed/<id_cam>")
def video_feed(id_cam):
    detalii = config.get('camere', {}).get(id_cam)
    
    if not detalii or not detalii.get('url_stream'):
        return "Camera nu a fost gasita sau nu are URL", 404
        
    url = detalii['url_stream']
    return Response(genereaza_cadre(url), mimetype='multipart/x-mixed-replace; boundary=frame')
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
