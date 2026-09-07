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
    @import url('https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible:ital,wght@0,400;0,700;1,400&family=Playfair+Display:wght@700&display=swap');

    :root {
        --font-ui: 'Atkinson Hyperlegible', Verdana, Tahoma, sans-serif;
        --font-titre: 'Playfair Display', Georgia, serif;
        --fond: #FEF5EF;
        --encre: #1B1B1B;
        --bordure: #8A7A70;
        --focus: #0B4F9E;
    }

    /* --- Base : tout le texte grossit d'un cran --- */
    html, body, .stApp, [class*="css"] {
        font-family: var(--font-ui);
        background-color: var(--fond);
        color: var(--encre);
    }
    .stApp { font-size: 19px; }
    .stApp p, .stApp li, .stMarkdown { font-size: 1.15rem; line-height: 1.65; }

    /* Le titre garde Playfair pour l'identité visuelle */
    .stApp h1, .stApp h2 { font-family: var(--font-titre); font-size: 2.4rem; }
    .stApp h3 { font-family: var(--font-titre); font-size: 1.8rem; }

    /* --- Libellés des champs --- */
    .stApp label,
    [data-testid="stWidgetLabel"] p {
        font-family: var(--font-ui) !important;
        font-size: 1.2rem !important;
        font-weight: 700 !important;
        color: var(--encre) !important;
    }

    /* --- Menus déroulants : champ fermé --- */
    div[data-baseweb="select"] > div {
        font-family: var(--font-ui) !important;
        font-size: 1.25rem !important;
        min-height: 58px;
        border: 2px solid var(--bordure) !important;
        background-color: #FFFFFF !important;
    }
    div[data-baseweb="select"] svg { height: 28px; width: 28px; }

    /* --- Menus déroulants : liste ouverte (rendue hors de .stApp) --- */
    div[data-baseweb="popover"],
    div[data-baseweb="popover"] *,
    ul[data-baseweb="menu"],
    ul[data-baseweb="menu"] * {
        font-family: var(--font-ui) !important;
    }
    ul[data-baseweb="menu"] li,
    div[data-baseweb="popover"] [role="option"] {
        font-size: 1.2rem !important;
        line-height: 1.5 !important;
        padding: 14px 18px !important;
        min-height: 52px;
    }
    ul[data-baseweb="menu"] li[aria-selected="true"],
    ul[data-baseweb="menu"] li:hover {
        background-color: #E8D9CD !important;
        color: var(--encre) !important;
    }

    /* --- Champs texte, nombre, date --- */
    .stApp input,
    .stApp textarea,
    div[data-baseweb="input"] input,
    div[data-baseweb="base-input"] input {
        font-family: var(--font-ui) !important;
        font-size: 1.25rem !important;
        color: var(--encre) !important;
    }
    div[data-baseweb="input"],
    .stTextArea textarea,
    div[data-testid="stNumberInput"] > div {
        border: 2px solid var(--bordure) !important;
        min-height: 58px;
    }
    .stTextArea textarea { min-height: 130px; line-height: 1.6; }

    /* Boutons +/- du champ Volume */
    div[data-testid="stNumberInput"] button { min-height: 52px; min-width: 52px; }
    div[data-testid="stNumberInput"] button svg { height: 24px; width: 24px; }

    /* --- Calendrier --- */
    div[data-baseweb="calendar"] { font-family: var(--font-ui) !important; }
    div[data-baseweb="calendar"] div[role="gridcell"],
    div[data-baseweb="calendar"] [aria-label] { font-size: 1.1rem !important; }

    /* --- Boutons --- */
    .stButton > button {
        font-family: var(--font-ui) !important;
        font-size: 1.25rem !important;
        font-weight: 700;
        padding: 0.9rem 2rem;
        min-height: 60px;
        border: 2px solid var(--encre);
    }

    /* --- Cases à cocher et interrupteur --- */
    .stCheckbox p, [data-testid="stCheckbox"] p,
    [data-testid="stToggle"] p, .stToggle p {
        font-size: 1.2rem !important;
        font-weight: 700;
    }
    .stCheckbox [data-baseweb="checkbox"] span:first-child { height: 28px; width: 28px; }

    /* --- Tableau d'historique --- */
    [data-testid="stDataFrame"] { font-size: 1.1rem; }

    /* --- Messages --- */
    [data-testid="stAlert"] p { font-size: 1.15rem !important; }

    /* --- Navigation au clavier bien visible --- */
    .stApp *:focus-visible,
    div[data-baseweb="popover"] *:focus-visible {
        outline: 4px solid var(--focus) !important;
        outline-offset: 2px !important;
    }

    @media (prefers-reduced-motion: reduce) {
        * { animation: none !important; transition: none !important; }
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
    date_collected = st.date_input(
        "📅 Date de la collecte",
        value=now_local.date(),
        format="DD/MM/YYYY"   # ← format FR dans le widget
    )
    time_collected = st.selectbox(
        "🕒 Heure de la collecte",
        time_options,
        index=default_index,
        format_func=lambda t: t.strftime("%H:%M")   # 08:30 au lieu de 08:30:00
    )
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
    if df.empty:
        st.info("Aucune donnée exploitable pour l’historique.")
    else:
        st.dataframe(df.drop(columns=["__dt__"], errors="ignore"), use_container_width=True)
        weekly = st.toggle("Regrouper par semaine", value=False)
        fig = build_chart(df, weekly)
        st.plotly_chart(fig, use_container_width=True, config=dict(displayModeBar=False, scrollZoom=True))

# 🗑️ Suppression d'une ligne
if st.checkbox("🗑️ Supprimer un enregistrement"):
    delete_record(sheet)
