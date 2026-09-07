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
        --fond:    #EDF2F4;
        --surface: #FFFFFF;
        --encre:   #16232B;
        --doux:    #52697A;
        --ligne:   #D3DFE5;
        --accent:  #14657F;
        --ambre:   #A96208;
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
        letter-spacing: 0.01em;
        color: var(--doux) !important;
    }

    /* ── Le chiffre : l'élément unique de la page ─────────── */
    [data-testid="stNumberInput"] input {
        font-family: var(--font) !important;
        font-size: 3.2rem !important;
        font-weight: 700 !important;
        text-align: center !important;
        color: var(--ambre) !important;
        font-variant-numeric: tabular-nums;
        padding: 0.2rem 0 !important;
        background: transparent !important;
    }
    [data-testid="stNumberInput"] > div {
        border: 2px solid var(--ligne) !important;
        border-radius: var(--r) !important;
        background: var(--surface) !important;
        min-height: 92px;
        align-items: center;
    }
    [data-testid="stNumberInput"] button {
        min-width: 62px; height: 88px;
        border-left: 1px solid var(--ligne) !important;
        border-right: 1px solid var(--ligne) !important;
        color: var(--accent) !important;
    }
    [data-testid="stNumberInput"] button svg { height: 30px; width: 30px; }

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
    .stButton > button[kind="primary"]:hover { background: #0F5069; color: #FFFFFF; }

    /* Raccourcis de volume : plus discrets */
    .st-key-chips .stButton > button {
        min-height: 44px;
        font-size: 0.95rem !important;
        font-weight: 400;
        border-width: 1px;
    }
    /* Méthode : deux cibles larges */
    .st-key-methode .stButton > button { min-height: 62px; font-size: 1.15rem !important; }
    /* Enregistrer */
    .st-key-save .stButton > button { min-height: 66px; font-size: 1.2rem !important; }

    /* ── Champs texte / date / heure ──────────────────────── */
    .stApp input, .stApp textarea,
    div[data-baseweb="input"] input, div[data-baseweb="select"] > div {
        font-family: var(--font) !important;
        font-size: 1.1rem !important;
        color: var(--encre) !important;
    }
    div[data-baseweb="input"], div[data-baseweb="select"] > div, .stTextArea textarea {
        border: 2px solid var(--ligne) !important;
        border-radius: var(--r) !important;
        min-height: 52px;
        background: var(--surface) !important;
    }
    .stTextArea textarea { min-height: 110px; line-height: 1.6; }

    /* ── Menus déroulants ouverts (rendus hors de .stApp) ─── */
    div[data-baseweb="popover"] *, ul[data-baseweb="menu"] * { font-family: var(--font) !important; }
    ul[data-baseweb="menu"] li, div[data-baseweb="popover"] [role="option"] {
        font-size: 1.1rem !important; padding: 13px 18px !important; min-height: 50px;
    }
    ul[data-baseweb="menu"] li:hover, ul[data-baseweb="menu"] li[aria-selected="true"] {
        background: #DDE8ED !important; color: var(--encre) !important;
    }
    div[data-baseweb="calendar"] * { font-family: var(--font) !important; }

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
    </style>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────
# État
# ─────────────────────────────────────────────────────────────
now_local = datetime.now(TZ).replace(tzinfo=None, second=0, microsecond=0)
slot_defaut = now_local.replace(minute=(now_local.minute // 30) * 30).time()

st.session_state.setdefault("volume", 200)
st.session_state.setdefault("methode", "Sonde")

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
    f"<p style='color:#52697A;margin:-0.4rem 0 1.2rem;font-weight:700'>{fr_date(now_local)}</p>",
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────
# Saisie
# ─────────────────────────────────────────────────────────────
with st.container(border=True):

    # Quand — replié : la valeur par défaut est juste presque à chaque fois
    with st.expander(f"🕒  {slot_defaut.strftime('%H:%M')} · aujourd'hui — modifier"):
        c1, c2 = st.columns(2)
        date_collected = c1.date_input("Date", value=now_local.date(), format="DD/MM/YYYY")
        time_collected = c2.time_input("Heure", value=slot_defaut, step=timedelta(minutes=30))
    datetime_collected = datetime.combine(date_collected, time_collected)

    st.markdown(
        "<p style='font-weight:700;color:#52697A;margin-bottom:0.2rem'>Volume recueilli</p>",
        unsafe_allow_html=True,
    )
    st.number_input("Volume en millilitres", min_value=0, max_value=3000, step=10,
                    key="volume", label_visibility="collapsed")
    st.markdown(
        "<p style='text-align:center;color:#52697A;margin:-0.6rem 0 0.6rem'>millilitres</p>",
        unsafe_allow_html=True,
    )

    with st.container(key="chips"):
        for ligne in ([100, 150, 200], [250, 300, 400]):
            for col, v in zip(st.columns(3), ligne):
                if col.button(str(v), key=f"chip_{v}", use_container_width=True):
                    st.session_state.volume = v
                    st.rerun()

    st.markdown(
        "<p style='font-weight:700;color:#52697A;margin:1.2rem 0 0.2rem'>Méthode</p>",
        unsafe_allow_html=True,
    )
    with st.container(key="methode"):
        mc1, mc2 = st.columns(2)
        for col, nom in ((mc1, "Sonde"), (mc2, "Naturel")):
            actif = st.session_state.methode == nom
            if col.button(nom, key=f"m_{nom}", use_container_width=True,
                          type="primary" if actif else "secondary"):
                st.session_state.methode = nom
                st.rerun()

    with st.expander("💬  Ajouter une note"):
        comment = st.text_area("Note", "", label_visibility="collapsed",
                               placeholder="Douleur, boisson, contexte…")

    with st.container(key="save"):
        if st.button("Enregistrer", type="primary", use_container_width=True):
            sheet.append_row([
                datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S"),
                datetime_collected.strftime("%Y-%m-%d %H:%M:%S"),
                st.session_state.volume,
                st.session_state.methode,
                comment,
            ])
            st.cache_data.clear()
            st.success(
                f"Enregistré : {st.session_state.volume} mL à {time_collected.strftime('%H:%M')}"
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
with st.expander("📈  Historique"):
    df = load_df_from_sheet(sheet)
    if df.empty:
        st.info("Rien à afficher pour l'instant. Enregistre une première collecte.")
    else:
        weekly = st.toggle("Regrouper par semaine", value=False)
        st.plotly_chart(build_chart(df, weekly), use_container_width=True,
                        config=dict(displayModeBar=False, scrollZoom=True))
        st.dataframe(df.drop(columns=["__dt__"], errors="ignore"), use_container_width=True)

with st.expander("🗑️  Supprimer un enregistrement"):
    delete_record(sheet)
