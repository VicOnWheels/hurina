import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import json
import base64
import pandas as pd

from functions import load_df_from_sheet, delete_record, build_chart

st.set_page_config(page_title="Hurina", page_icon="💧", layout="centered")

TZ = ZoneInfo("Europe/Paris")

# ─────────────────────────────────────────────────────────────
# Connexion à Google Sheet
# ─────────────────────────────────────────────────────────────
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(st.secrets["GOOGLE_CREDENTIALS"])
creds_dict["private_key"] = base64.b64decode(creds_dict["private_key"]).decode()
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open("hurina_db").sheet1

# ─────────────────────────────────────────────────────────────
# Style
# ─────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible:ital,wght@0,400;0,700;1,400&display=swap');

    :root {
      --font: 'Atkinson Hyperlegible', Verdana, sans-serif;
      --fond: #FFF3F0;      /* fond du logo */
      --surface: #FFFFFF;
      --encre: #2B1C19;
      --doux: #7C5A54;
      --ligne: #F2D9D3;
      --saumon: #D89890;    /* saumon du logo */
      --accent: #B85E53;    /* saumon foncé, lisible sur blanc */
      --accent-fonce: #9C4A40;
      --r: 14px;
    }

    /* ── Base ─────────────────────────────────────────────── */
    html, body, .stApp, [class*="css"] { font-family: var(--font); }
    .stApp { background: var(--fond); color: var(--encre); font-size: 17px; }
    #MainMenu, footer, header [data-testid="stStatusWidget"] { visibility: hidden; }
    .block-container { padding: 1.6rem 1rem 4rem; max-width: 640px; }
    .stApp p, .stApp li { font-size: 1.05rem; line-height: 1.6; color: var(--encre); }

    /* ── Cartes ───────────────────────────────────────────── */
    [data-testid="stVerticalBlockBorderWrapper"] {
      background: var(--surface);
      border: 1px solid var(--ligne) !important;
      border-radius: var(--r) !important;
      padding: 0.4rem 0.2rem;
    }

    /* ── Libellés ─────────────────────────────────────────── */
    .stApp label, [data-testid="stWidgetLabel"] p {
      font-family: var(--font) !important;
      font-size: 0.95rem !important;
      font-weight: 700 !important;
      color: var(--doux) !important;
    }

    /* ── Le chiffre : l'élément unique de la page ─────────── */
    [data-testid="stNumberInput"] input {
      font-family: var(--font) !important;
      font-size: 3.2rem !important;
      font-weight: 700 !important;
      text-align: center !important;
      color: var(--accent) !important;
      font-variant-numeric: tabular-nums;
      padding: 0.2rem 0 !important;
      background: transparent !important;
    }
    /* L'encart « Appuyez sur Entrée » se superposait au champ : on le masque */
    [data-testid="InputInstructions"],
    [data-testid="stInputInstructions"] { display: none !important; }

    [data-testid="stNumberInputContainer"] {
      border: 2px solid var(--ligne) !important;
      border-radius: var(--r) !important;
      background: var(--surface) !important;
      min-height: 96px;
      align-items: center;
      overflow: hidden;
    }

    /* Le bouton d'effacement reste petit et discret, pas un pavé saumon */
    [data-testid="stNumberInputClearButton"] {
      background: transparent !important;
      color: var(--doux) !important;
      min-width: 40px !important; width: 40px !important; height: 40px !important;
    }
    [data-testid="stNumberInputClearButton"] svg {
      height: 20px !important; width: 20px !important; fill: var(--doux) !important;
    }

    /* Boutons + / − : toujours visibles, larges, tapables au doigt */
    [data-testid="stNumberInputStepUp"],
    [data-testid="stNumberInputStepDown"] {
      display: flex !important;
      visibility: visible !important;
      opacity: 1 !important;
      min-width: 68px !important;
      width: 68px !important;
      height: 92px !important;
      align-items: center !important;
      justify-content: center !important;
      background: var(--saumon) !important;
      color: #FFFFFF !important;
      border: none !important;
      border-radius: 0 !important;
    }
    [data-testid="stNumberInputStepUp"]:hover,
    [data-testid="stNumberInputStepDown"]:hover {
      background: var(--accent) !important;
      color: #FFFFFF !important;
    }
    [data-testid="stNumberInputStepUp"] svg,
    [data-testid="stNumberInputStepDown"] svg {
      height: 34px !important; width: 34px !important;
      fill: #FFFFFF !important; color: #FFFFFF !important;
    }

    /* ── Méthode : deux pastilles à parts égales ──────────── */
    [data-testid="stButtonGroup"] { width: 100% !important; }
    [data-testid="stButtonGroup"] > div {
      display: flex !important;
      width: 100% !important;
      gap: 0.6rem !important;
    }
    [data-testid="stButtonGroup"] > div > * { flex: 1 1 0 !important; min-width: 0 !important; }
    [data-testid="stButtonGroup"] button {
      flex: 1 1 0 !important;
      width: 100% !important;
      min-width: 0 !important;
      min-height: 64px !important;
      margin: 0 !important;
      padding: 0 0.4rem !important;
      border: 2px solid var(--ligne) !important;
      border-radius: var(--r) !important;
      background: var(--surface) !important;
      overflow: visible !important;
    }
    [data-testid="stButtonGroup"] button p,
    [data-testid="stButtonGroup"] button div {
      font-size: 1.2rem !important;
      font-weight: 700 !important;
      color: var(--doux) !important;
      white-space: nowrap !important;
      overflow: visible !important;
      text-overflow: clip !important;
    }
    [data-testid="stButtonGroup"] button[kind="segmented_controlActive"] {
      background: var(--accent) !important;
      border-color: var(--accent) !important;
    }
    [data-testid="stButtonGroup"] button[kind="segmented_controlActive"] p,
    [data-testid="stButtonGroup"] button[kind="segmented_controlActive"] div {
      color: #FFFFFF !important;
    }

    /* ── Boutons ──────────────────────────────────────────── */
    .stButton > button {
      font-family: var(--font) !important;
      font-size: 1.05rem !important;
      font-weight: 700;
      min-height: 52px;
      border-radius: var(--r);
      border: 2px solid var(--ligne);
      background: var(--surface);
      color: var(--doux);
      transition: none;
    }
    .stButton > button[kind="primary"] {
      background: var(--accent);
      border-color: var(--accent);
      color: #FFFFFF;
    }
    .stButton > button:hover { border-color: var(--accent); color: var(--accent); }
    .stButton > button[kind="primary"]:hover { background: var(--accent-fonce); color: #FFFFFF; }
    .st-key-save .stButton > button { min-height: 66px; font-size: 1.2rem !important; }

    /* ── Champs texte / date / heure ──────────────────────── */
    .stApp input, .stApp textarea,
    div[data-baseweb="input"] input, div[data-baseweb="select"] > div,
    [data-testid="stDateInput"] input, [data-testid="stTimeInput"] input {
      font-family: var(--font) !important;
      font-size: 1.25rem !important;
      font-weight: 700 !important;
      color: var(--encre) !important;
    }
    div[data-baseweb="input"], div[data-baseweb="select"] > div, .stTextArea textarea {
      border: 2px solid var(--ligne) !important;
      border-radius: var(--r) !important;
      min-height: 60px;
      background: var(--surface) !important;
    }
    .stTextArea textarea { font-weight: 400 !important; min-height: 110px; line-height: 1.6; }

    /* ── Menus déroulants ouverts (rendus hors de .stApp) ─── */
    div[data-baseweb="popover"] *, ul[data-baseweb="menu"] * { font-family: var(--font) !important; }
    ul[data-baseweb="menu"] li, div[data-baseweb="popover"] [role="option"],
    div[data-baseweb="popover"] li {
      font-size: 1.25rem !important;
      font-weight: 700 !important;
      padding: 16px 20px !important;
      min-height: 60px !important;
      display: flex !important;
      align-items: center !important;
    }
    ul[data-baseweb="menu"] li:hover, ul[data-baseweb="menu"] li[aria-selected="true"] {
      background: var(--fond) !important; color: var(--encre) !important;
    }
    div[data-baseweb="calendar"] * { font-family: var(--font) !important; }
    div[data-baseweb="calendar"] [role="gridcell"] { font-size: 1.1rem !important; }

    /* ── Résumé du jour ───────────────────────────────────── */
    .resume {
      display: flex; gap: 2.2rem; align-items: baseline;
      padding: 1.1rem 1.3rem; margin: 1.4rem 0 0.6rem;
      background: var(--surface); border: 1px solid var(--ligne); border-radius: var(--r);
    }
    .resume b { font-size: 1.6rem; color: var(--encre); font-variant-numeric: tabular-nums; }
    .resume span { font-size: 0.9rem; color: var(--doux); display: block; font-weight: 700; }

    /* ── Divers ───────────────────────────────────────────── */
    [data-testid="stExpander"] details {
      border: 1px solid var(--ligne); border-radius: var(--r); background: var(--surface);
    }
    [data-testid="stExpander"] summary p { font-size: 1.05rem !important; font-weight: 700; }
    [data-testid="stDataFrame"] { font-size: 1rem; }
    [data-testid="stAlert"] p { font-size: 1.05rem !important; }
    [data-testid="stToggle"] p, .stCheckbox p { font-size: 1.05rem !important; }
    hr { border-color: var(--ligne); margin: 1.6rem 0; }
    .stApp *:focus-visible, div[data-baseweb="popover"] *:focus-visible {
      outline: 3px solid var(--accent) !important; outline-offset: 2px !important;
    }
    @media (prefers-reduced-motion: reduce) { * { animation: none !important; transition: none !important; } }

    /* ── Petits écrans ────────────────────────────────────── */
    @media (max-width: 420px) {
      .block-container { padding: 1.2rem 0.7rem 3rem; }
      [data-testid="stNumberInput"] input { font-size: 2.8rem !important; }
      [data-testid="stNumberInputStepUp"],
      [data-testid="stNumberInputStepDown"] {
        min-width: 58px !important; width: 58px !important; height: 80px !important;
      }
      [data-testid="stNumberInputContainer"] { min-height: 84px; }
      [data-testid="stButtonGroup"] button p { font-size: 1.1rem !important; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────
# Date du jour
# ─────────────────────────────────────────────────────────────
now_local = datetime.now(TZ).replace(tzinfo=None, second=0, microsecond=0)
slot_defaut = now_local.replace(minute=(now_local.minute // 30) * 30).time()

JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
MOIS = ["janvier", "février", "mars", "avril", "mai", "juin",
        "juillet", "août", "septembre", "octobre", "novembre", "décembre"]


def fr_date(d):
    return f"{JOURS[d.weekday()]} {d.day} {MOIS[d.month - 1]}"


# ─────────────────────────────────────────────────────────────
# En-tête
# ─────────────────────────────────────────────────────────────
st.image("hurina_logo.png", width=150)
st.markdown(
    f"<p style='color:#7C5A54;margin:-0.4rem 0 1.2rem;font-weight:700'>{fr_date(now_local)}</p>",
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────
# Saisie
# ─────────────────────────────────────────────────────────────
with st.container(border=True):

    # Quand — replié : l'heure proposée convient presque toujours
    with st.expander(f"Heure du recueil : {slot_defaut.strftime('%H:%M')} — modifier"):
        c1, c2 = st.columns(2)
        date_collected = c1.date_input("Date", value=now_local.date(), format="DD/MM/YYYY")
        time_collected = c2.time_input("Heure", value=slot_defaut, step=timedelta(minutes=30))
    datetime_collected = datetime.combine(date_collected, time_collected)

    st.markdown(
        "<p style='font-weight:700;color:#7C5A54;margin-bottom:0.2rem'>Volume recueilli (mL)</p>",
        unsafe_allow_html=True,
    )
    # value=0 : les boutons +/- sont utilisables dès le départ, sans saisie préalable
    volume = st.number_input(
        "Volume en millilitres",
        min_value=0,
        max_value=3000,
        step=50,
        value=0,
        key="volume",
        label_visibility="collapsed",
    )

    st.markdown(
        "<p style='font-weight:700;color:#7C5A54;margin:1.2rem 0 0.2rem'>Méthode</p>",
        unsafe_allow_html=True,
    )
    methode = st.segmented_control(
        "Méthode",
        ["Sonde", "Naturel"],
        default="Sonde",
        key="methode_choix",
        label_visibility="collapsed",
        width="stretch",
    )

    with st.expander("Ajouter une note"):
        comment = st.text_area("Note", "", label_visibility="collapsed",
                               placeholder="Douleur, boisson, contexte…")

    with st.container(key="save"):
        if st.button("Enregistrer", type="primary", width="stretch"):
            if not volume:
                st.warning("Saisis un volume avant d'enregistrer.")
            elif not methode:
                st.warning("Choisis une méthode avant d'enregistrer.")
            else:
                sheet.append_row([
                    datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S"),
                    datetime_collected.strftime("%Y-%m-%d %H:%M:%S"),
                    int(volume),
                    methode,
                    comment,
                ])
                st.cache_data.clear()
                st.success(
                    f"Enregistré : {int(volume)} mL à {time_collected.strftime('%H:%M')}"
                )


# ─────────────────────────────────────────────────────────────
# Résumé du jour
# ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=60, show_spinner=False)
def resume_du_jour(_sheet, jour):
    """Total et nombre de collectes du jour. None si le format ne s'y prête pas."""
    try:
        df = load_df_from_sheet(_sheet)
        if df.empty or "__dt__" not in df.columns:
            return None
        col_vol = next(c for c in df.columns if "volume" in str(c).lower())
        j = df[pd.to_datetime(df["__dt__"]).dt.date == jour]
        if j.empty:
            return 0, 0
        return int(pd.to_numeric(j[col_vol], errors="coerce").sum()), len(j)
    except Exception:
        return None


r = resume_du_jour(sheet, now_local.date())
if r is not None:
    total, n = r
    st.markdown(
        f"""<div class="resume">
        <div><span>Aujourd'hui</span><b>{total:,} mL</b></div>
        <div><span>Collectes</span><b>{n}</b></div>
        </div>""".replace(",", " "),
        unsafe_allow_html=True,
    )

# ─────────────────────────────────────────────────────────────
# Historique
# ─────────────────────────────────────────────────────────────
with st.expander("Historique"):
    df = load_df_from_sheet(sheet)
    if df.empty:
        st.info("Rien à afficher pour l'instant. Enregistre une première collecte.")
    else:
        weekly = st.toggle("Regrouper par semaine", value=False)
        st.plotly_chart(build_chart(df, weekly), width="stretch",
                        config=dict(displayModeBar=False, scrollZoom=True))
        st.dataframe(df.drop(columns=["__dt__"], errors="ignore"), width="stretch")

with st.expander("Supprimer un enregistrement"):
    delete_record(sheet)
