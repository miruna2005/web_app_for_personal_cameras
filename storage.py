import os
import json
def incarca_configurare(cale="config.json"):
    try:
        with open(cale,"r")as f:
            return json.load(f)
    except Exception as e:
        print(f"err la citirea config")
        exit(1)
config=incarca_configurare()
def get_cale_inregistrari():
    baza_media=config["stocare"]["baza_media_usb"]
    nume_folder=config["stocare"]["nume_folder"]
    if os.path.exists(baza_media):
        dispozitive = [os.path.join(baza_media, d) for d in os.listdir(baza_media) 
                       if os.path.isdir(os.path.join(baza_media, d))]
        if dispozitive:
            cale_folder = os.path.join(dispozitive[0], nume_folder)
            return cale_folder, True
    return nume_folder,False