import os
import json
from flask import Flask,jsonfy,render_template,send_from_directory
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
    return jsonfy({
        "stocare_usb":e_pe_usb,
        "mesaj":mesaj,
        "stare":stare
    })
@app.route("api/events")
def get_events():
    cale_folder,_=get_cale_inregistrari()
    cale_json=os.path.join(cale_folder,config["stocare"]["fisier_evenimente"])
    if not os.path.exists(cale_json):
        return jsonfy([])
    try:
        with open(cale_json,"r") as f:
            evenimente=json.load(f)
            evenimente.reverse()
            return jsonfy(evenimente)
    except Exception as e:
        print(f"nu s a putut citi events.json",flush=True)
        return jsonfy([])
@app.route("/video/<path:nume_fisier>")
def get_video(nume_fisier):
    cale_folder,_=get_cale_inregistrari()
    return send_from_directory(cale_folder,nume_fisier,mimetype='video/mp4')