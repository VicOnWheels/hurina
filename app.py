import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, time, timedelta
import json
import base64
import pandas as pd
import altair as alt

from functions import load_df_from_sheet, delete_record, build_chart

# Connexion à Google Sheet
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(st.secrets["GOOGLE_CREDENTIALS"])
creds_dict["private_key"] = base64.b64decode(creds_dict["private_key"]).decode()

creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open("hurina_db").sheet1

# 🎨 Style
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display&display=swap');

    html, body, [class*="css"] {
        font-family: 'Playfair Display', serif;
        background-color: #FEF5EF;
    }

    .stApp {
        background-color: #FEF5EF;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# 🖼️ Logo
st.image("hurina_logo.png", width=200)

# 🎯 Titre
st.markdown("## 💧 Hurina - Suivi urinaire quotidien")
st.markdown("Bienvenue ! Saisis tes données pour suivre ton évolution 💪")
st.markdown("---")

# 🧾 Formulaire
col1, col2, col3 = st.columns(3)

# Heure locale à l'instant, arrondie à l'heure pleine
now_local = (datetime.now() + timedelta(hours=2)).replace(minute=0, second=0, microsecond=0)

# Créneaux 30 min : 00:00, 00:30, ..., 23:30
time_options = [time(h, m) for h in range(24) for m in (0, 30)]

# Trouver l'index correspondant à l'heure actuelle
default_time = now_local.time().replace(second=0, microsecond=0)
default_index = time_options.index(default_time) if default_time in time_options else 0

with col1:
    date_collected = st.date_input("📅 Date de la collecte", value=now_local.date())
    time_collected = st.selectbox("🕒 Heure de la collecte", time_options, index=default_index)
    datetime_collected = datetime.combine(date_collected, time_collected)

with col2:
    volume = st.number_input("Volume (mL)", min_value=0, step=10)

with col3:
    method = st.selectbox("⚙️ Méthode utilisée", ["Sonde", "Naturel"])

comment = st.text_area("📝 Commentaire (optionnel)", "")

if st.button("💾 Enregistrer"):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sheet.append_row([
        now,
        datetime_collected.strftime("%Y-%m-%d %H:%M:%S"),
        volume,
        method,
        comment
    ])
    st.success("✅ Donnée enregistrée avec succès ! Un pas de plus vers le succès 🚀")

st.markdown("---")

# ---------- UI ----------
if st.checkbox("📈 Afficher l'historique des enregistrements"):
    df = load_df_from_sheet(sheet)
    # affichage tableau historique sans __dt__
    st.dataframe(
        df.drop(columns=["__dt__"], errors="ignore"),
        use_container_width=True,
        hide_index=True
    )


    if df.empty:
        st.info("Aucune donnée exploitable pour l’historique.")
    else:
        st.dataframe(df, use_container_width=True)
        weekly = st.toggle("Regrouper par semaine", value=False)
        fig = build_chart(df, weekly)
        st.plotly_chart(fig, use_container_width=True, config=dict(displayModeBar=False, scrollZoom=True))


# 🗑️ Suppression d'une ligne
if st.checkbox("🗑️ Supprimer un enregistrement"):
    delete_record(sheet)
