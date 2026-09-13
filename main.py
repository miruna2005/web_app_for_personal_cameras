import cv2
import time
import os
import json
import shutil
import glob
from datetime import datetime
from threading import Thread,Lock
from proiectcamere import CamereStream
from storage import get_cale_inregistrari
import os
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"
def incarca_configurare(cale="config.json"):
    try:
        with open(cale, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Fisierul {cale} lipseste! Programul se va opri.")
        exit(1)
    except json.JSONDecodeError as e:
        print(f"Eroare de sintaxa in {cale}: {e}. Programul se va opri.")
        exit(1)

config = incarca_configurare()
json_lock=Lock()
def verifica_curata_spatiu(director):
    limita_gb=config["stocare"]["limita_spatiu_gb"]
    zile_pastrate=config["stocare"]["zile_pastrate_video"]
    nume_fisier_json=config["stocare"]["fisier_evenimente"]
    if not os.path.exists(director):
        return
    limita_gb=limita_gb*1024*1024*1024
    _,_,liber=shutil.disk_usage(director)
    if liber<limita_gb:
        print("spatiu liber pe stick sub limita.Curatare...")
        timp_lim_sec=time.time()-(zile_pastrate*86400)
        fisiere_video=glob.glob(os.path.join(director,"*.mp4"))
        fisiere_sterse=0
        for fisier in fisiere_video:
            try:
                if os.path.getmtime(fisier)<timp_lim_sec:
                    os.remove(fisier)
                    fisiere_sterse+=1
            except OSError as e:
                print(f"nu s au putut sterge {fisier}:{e}")
            cale_json=os.path.join(director,nume_fisier_json)
            if os.path.exists(cale_json):
                with json_lock:
                    try:
                        with open(cale_json,"r")as f:
                            evenimente=json.load(f)
                            evenimente_valide=[ev for ev in evenimente if
                            os.path.exists(os.path.join(director,ev.get("fisier","")))]
                        with open(cale_json,"w") as f:
                            json.dump(evenimente_valide,f,indent=4)
                    except Exception as e:
                        print(f"Nu s a putut actualiza events.json:{e}")
def adauga_evenim_json(nume_camera, cale_fisier, cale_folder):
    cale_json = os.path.join(cale_folder, config["stocare"]["fisier_evenimente"])
    with json_lock:
        evenimente = []
        if os.path.exists(cale_json):
            try:
                with open(cale_json, "r") as f:
                    evenimente = json.load(f)
            except json.JSONDecodeError:
                evenimente = []
                
        noul_evenim = {
            "id": f"EVT-{int(time.time())}",
            "camera": nume_camera,
            "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "descriere": "Mișcare detectată",
            "fisier": os.path.basename(cale_fisier) 
        }
        evenimente.append(noul_evenim)
        
        with open(cale_json, "w") as f:
            json.dump(evenimente, f, indent=4)
    evenimente.append(noul_evenim)
def proceseaza_camere(nume_camera,stream):
    print(f"[{nume_camera}] procesare pornita")
    inregistrare_activa=False
    video_writer=None
    sec_fara_miscare=0
    cale_fisier_curent = ""
    setari_sens = config["video"]["sensibilitate"]
    rez_w, rez_h = config["video"]["rezolutie_procesare"]
    fps_inreg = config["video"]["fps_inregistrare"]
    scazator_fundal=cv2.createBackgroundSubtractorMOG2(history=setari_sens["history_cadre"],varThreshold=setari_sens["var_threshold"],detectShadows=False)#creeaza fundalul deafult(starea 0)
    #varThreshold sensibilitate/toleranta la miscare 50=imun la schimbari mici(crengi etc)
    k_size = setari_sens["blur_kernel"]
    while True:
        timp_start=time.time()
        cadru=stream.citeste_cadru()
        if cadru is None:
            time.sleep(0.05)
            continue
        cadru_mic=cv2.resize(cadru,(rez_w,rez_h))
        masca=scazator_fundal.apply(cadru_mic)#rezolutie mai mica&mapa a starilor
        masca=cv2.GaussianBlur(masca,(k_size,k_size),0)
        _, masca=cv2.threshold(masca,setari_sens["threshold_binar"],255,cv2.THRESH_BINARY)
        #cv2... ret 2 parametri prin _, ignora primul
        contururi,_=cv2.findContours(masca,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
        if contururi:
            arie_max = max(cv2.contourArea(c) for c in contururi)
            if arie_max > 100: ###################################################
                print(f"[{nume_camera}] Arie max miscare: {arie_max}")
        miscare_detectata=any(cv2.contourArea(c)>setari_sens["aria_minima_contur"] for c in contururi)
        if miscare_detectata and not inregistrare_activa:
            cale_folder, _ = get_cale_inregistrari()
            try:
                os.makedirs(cale_folder, exist_ok=True)
            except OSError as e:
                print(f"Nu pot scrie în {cale_folder}: {e}")
                cale_folder = config["stocare"]["nume_folder"]
                os.makedirs(cale_folder, exist_ok=True)
            
            verifica_curata_spatiu(cale_folder)
            print(f"[{nume_camera}] Mișcare Detectată - Pornesc înregistrarea.")
            
            inregistrare_activa = True
            sec_fara_miscare = 0
            timp_formatat = datetime.now().strftime("%Y-%m-%d_%H-%M-S")
            cale_fisier_curent = os.path.join(cale_folder, f"eveniment_{nume_camera}_{timp_formatat}.webm")
            
            inaltime, latime, _ = cadru.shape
            patru_cc = cv2.VideoWriter_fourcc(*'vp80')
            video_writer = cv2.VideoWriter(cale_fisier_curent, patru_cc, fps_inreg, (latime, inaltime))
        if inregistrare_activa:
            if video_writer is not None:
                video_writer.write(cadru)
            
            if miscare_detectata:
                sec_fara_miscare = 0
            else:
                sec_fara_miscare += 0.1
            if not miscare_detectata and sec_fara_miscare >= config["video"]["secunde_liniste_stop"]:
                print(f"[{nume_camera}] Liniște detectată. Închid înregistrarea.", flush=True)
                inregistrare_activa = False
                
                if video_writer is not None:
                    video_writer.release()
                    video_writer = None
                adauga_evenim_json(nume_camera, cale_fisier_curent, os.path.dirname(cale_fisier_curent))
        durata_procesare = time.time() - timp_start
        pauza_necesara = (1.0 / config["video"]["fps_inregistrare"]) - durata_procesare
        if pauza_necesara > 0:
            time.sleep(pauza_necesara)
if __name__ == "__main__":
    camere_streamuri = {}
    for nume_cam, detalii_cam in config["camere"].items():
        if detalii_cam.get("activa", False):
            camere_streamuri[nume_cam] = CamereStream(detalii_cam["url_stream"])
            
            t = Thread(target=proceseaza_camere, args=(nume_cam, camere_streamuri[nume_cam]))
            t.daemon = True
            t.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n Oprire curata initiata")
        for stream in camere_streamuri.values():
            stream.opreste()
        print("Sistem oprit curat.")