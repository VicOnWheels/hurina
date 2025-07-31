import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import json
import base64

# Connexion à Google Sheet
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(st.secrets["GOOGLE_CREDENTIALS"])

# 🔐 Décode la clé privée
creds_dict["private_key"] = base64.b64decode(creds_dict["private_key"]).decode()

creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open("hurina_db").sheet1


# Interface Streamlit
st.title("Bienvenue sur Hurina")
st.write("Cette application te permet de suivre ton volume urinaire quotidien.")

volume = st.number_input("Volume urinaire (en mL)", min_value=0, step=10)
method = st.selectbox("Méthode utilisée", ["Sonde", "Naturel"])
comment = st.text_area("Commentaire (optionnel)", "")
if st.button("💾 Enregistrer"):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sheet.append_row([now, volume, method])
    st.success("Un pas de plus vers la victoire ✅")

# Historique
if st.checkbox("📊 Voir l'historique"):
    data = sheet.get_all_records()
    st.dataframe(data)
