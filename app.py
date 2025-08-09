import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, time, timedelta
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

from datetime import time

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



# 📊 Historique + Graphique (avec cache & toggle)

@st.cache_data(ttl=30)
def load_df_from_sheet(_sheet):
    """Charge les données et gère la conversion datetime de 'Saisie temps'."""
    records = _sheet.get_all_records()  # ⚠️ 1 seul appel grâce au cache
    df = pd.DataFrame(records)
    if df.empty:
        return df

    COL_TIME = "Saisie temps"
    COL_VOL = "Volume urinaire (en mL)"
    COL_METH = "Méthode utilisée"

    # Vérifs colonnes minimales
    for c in [COL_TIME, COL_VOL, COL_METH]:
        if c not in df.columns:
            st.error(f"Colonne manquante dans Google Sheet : '{c}'")
            return pd.DataFrame()

    # Conversion robuste -> datetime
    s = df[COL_TIME].astype(str).str.strip()

    # a) format ISO (celui que tu écris dans append_row)
    dt = pd.to_datetime(s, format="%Y-%m-%d %H:%M:%S", errors="coerce")

    # b) fallback FR
    mask = dt.isna()
    if mask.any():
        dt.loc[mask] = pd.to_datetime(s[mask], format="%d/%m/%Y %H:%M:%S", errors="coerce")

    # c) dernier filet (mixte)
    mask = dt.isna()
    if mask.any():
        dt.loc[mask] = pd.to_datetime(s[mask], errors="coerce", dayfirst=True)

    df[COL_TIME] = dt
    df = df.dropna(subset=[COL_TIME]).copy()

    # Tri et colonnes utiles
    df = df.sort_values(COL_TIME)
    return df

# ---------- UI ----------
if st.checkbox("📈 Afficher l'historique des enregistrements"):
    df = load_df_from_sheet(sheet)

    if df.empty:
        st.info("Aucune donnée exploitable pour l’historique.")
    else:
        st.dataframe(df, use_container_width=True)

        weekly = st.toggle("Regrouper par semaine", value=False)

        COL_TIME = "Saisie temps"
        COL_VOL = "Volume urinaire (en mL)"
        COL_METH = "Méthode utilisée"

        if weekly:
            # début de semaine (lundi)
            df2 = df.assign(
                Semaine=df[COL_TIME].dt.to_period("W-MON").apply(lambda p: p.start_time)
            )
            chart_data = (
                df2.groupby(["Semaine", COL_METH], as_index=False)[COL_VOL]
                   .sum()
                   .sort_values("Semaine")
            )
            x_field = alt.X(
                "Semaine:T",
                title="Semaine (début)",
                axis=alt.Axis(format="%d/%m"),
                sort="ascending",
            )
            tooltip = [
                alt.Tooltip("Semaine:T", title="Semaine du", format="%d/%m/%Y"),
                alt.Tooltip(f"{COL_METH}:N", title="Méthode"),
                alt.Tooltip(f"{COL_VOL}:Q", title="Volume (mL)"),
            ]
            chart_title = "📊 Volume urinaire hebdomadaire par méthode"
        else:
            # journalier (date à minuit pour agréger sur le jour)
            df2 = df.assign(JourDate=df[COL_TIME].dt.normalize())
            chart_data = (
                df2.groupby(["JourDate", COL_METH], as_index=False)[COL_VOL]
                   .sum()
                   .sort_values("JourDate")
            )
            x_field = alt.X(
                "JourDate:T",
                title="Jour",
                axis=alt.Axis(format="%d/%m"),
                sort="ascending",
            )
            tooltip = [
                alt.Tooltip("JourDate:T", title="Jour", format="%d/%m/%Y"),
                alt.Tooltip(f"{COL_METH}:N", title="Méthode"),
                alt.Tooltip(f"{COL_VOL}:Q", title="Volume (mL)"),
            ]
            chart_title = "📊 Volume urinaire journalier par méthode"

        chart = (
            alt.Chart(chart_data)
            .mark_bar(size=20)
            .encode(
                x=x_field,
                y=alt.Y(f"{COL_VOL}:Q", title="Volume total (mL)"),
                color=alt.Color(f"{COL_METH}:N", title="Méthode"),
                tooltip=tooltip,
            )
            .properties(title=chart_title, width="container")
        )

        st.altair_chart(chart, use_container_width=True)

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
            sheet.delete_rows(int(selected_index) + 2)  # 👈 conversion sécurisée en int natif
            st.success("✅ Enregistrement supprimé avec succès. Rechargez la page pour voir les changements.")
        else:
            st.warning("❗ Veuillez cocher la case de confirmation avant de supprimer.")
