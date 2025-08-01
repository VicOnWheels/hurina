import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from datetime import datetime, timedelta
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

now_local = datetime.now() + timedelta(hours=2)  # Ajustement pour l'heure locale (UTC+2)

with col1:
    date_collected = st.date_input("📅 Date de la collecte", value=now_local.date())
    time_collected = st.time_input("🕒 Heure de la collecte", value=now_local.time())
    datetime_collected = datetime.combine(date_collected, time_collected)

with col2:
    volume = st.number_input("💦 Volume urinaire (en mL)", min_value=0, step=10)
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

# 📊 Historique et graphique
if st.checkbox("📈 Afficher l'historique des enregistrements"):
    records = sheet.get_all_records()
    df = pd.DataFrame(records)

    if not df.empty:
        # Conversion date
        df["Horodatage"] = pd.to_datetime(df["Horodatage"])
        df = df.sort_values("Horodatage")

        st.dataframe(df, use_container_width=True)

        # 📈 Graphique
        chart = alt.Chart(df).mark_line(point=True).encode(
            x=alt.X("Horodatage:T", title="Date"),
            y=alt.Y("Volume urinaire (en mL):Q", title="Volume (mL)"),
            tooltip=["Horodatage:T", "Volume urinaire (en mL):Q", "Méthode utilisée", "Commentaire (optionnel)"]
        ).properties(
            title="📊 Évolution du volume urinaire",
            width="container"
        ).interactive()

        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("Aucun enregistrement à afficher ou supprimer.")

# 🗑️ Suppression d'une ligne
if st.checkbox("🗑️ Supprimer un enregistrement"):
    records = sheet.get_all_records()
    df = pd.DataFrame(records)

    if not df.empty:
        st.markdown("### 🗑️ Supprimer un enregistrement")

        # Création des libellés lisibles
        df["__label"] = df.apply(
            lambda row: f"{row['Saisie temps']} – {row['Volume urinaire (en mL)']} mL – {row['Méthode utilisée']}",
            axis=1
        )
        selected_label = st.selectbox("Choisissez un enregistrement à supprimer :", df["__label"].tolist())
        selected_index = df[df["__label"] == selected_label].index[0]

        confirm = st.checkbox("✅ Je confirme vouloir supprimer cet enregistrement")

        if st.button("Supprimer cet enregistrement ❌"):
            if confirm:
                sheet.delete_rows(selected_index + 2)  # +2 : 1 pour le header, 1 car index 0-based
                st.success("✅ Enregistrement supprimé avec succès. Rechargez la page pour voir les changements.")
            else:
                st.warning("❗ Veuillez cocher la case de confirmation avant de supprimer.")
    else:
        st.info("Aucun enregistrement à supprimer.")
