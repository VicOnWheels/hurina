import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import json
import base64
import pandas as pd
import altair as alt

# Connexion à Google Sheet
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(st.secrets["GOOGLE_CREDENTIALS"])
creds_dict["private_key"] = base64.b64decode(creds_dict["private_key"]).decode()

creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open("hurina_db").sheet1

st.markdown(
    """
    <style>
    body {
        background-color: #fdecef;
    }
    .stApp {
        background-color: #fdecef;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("Bienvenue sur Hurina")


# 🎨 Titre
st.markdown("## 💧 Hurina - Suivi urinaire quotidien")
st.markdown("Bienvenue ! Saisis tes données pour suivre ton évolution 💪")

st.markdown("---")

# 🧾 Formulaire
col1, col2 = st.columns(2)
with col1:
    volume = st.number_input("💦 Volume urinaire (en mL)", min_value=0, step=10)
with col2:
    method = st.selectbox("⚙️ Méthode utilisée", ["Sonde", "Naturel"])

comment = st.text_area("📝 Commentaire (optionnel)", "")

if st.button("💾 Enregistrer"):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sheet.append_row([now, volume, method, comment])
    st.success("✅ Donnée enregistrée avec succès ! Un pas de plus vers le succès 🚀")

st.markdown("---")

# 📊 Historique et graphique
if st.checkbox("📈 Afficher l'historique des enregistrements"):
    records = sheet.get_all_records()
    df = pd.DataFrame(records)

    # Transformation des données pour le graphique
    df["Horodatage"] = pd.to_datetime(df["Horodatage"])
    df = df.sort_values("Horodatage")

    st.dataframe(df, use_container_width=True)

    # Graphique Altair
    chart = alt.Chart(df).mark_line(point=True).encode(
        x=alt.X("Horodatage:T", title="Date"),
        y=alt.Y("Volume urinaire (en mL):Q", title="Volume (mL)"),
        tooltip=["Horodatage:T", "Volume urinaire (en mL):Q", "Méthode utilisée", "Commentaire (optionnel)"]
    ).properties(
        title="📊 Évolution du volume urinaire",
        width="container"
    ).interactive()

    st.altair_chart(chart, use_container_width=True)
