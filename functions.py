import streamlit as st
import pandas as pd
import plotly.express as px
import pandas as pd

@st.cache_data(ttl=60, show_spinner=False)
def load_records(_sheet):
    """Lecture brute du Sheet. Unique point d'accès réseau, mis en cache :
    tout le reste du module passe par ici au lieu d'appeler get_all_records()."""
    return _sheet.get_all_records()


@st.cache_data(ttl=60, show_spinner=False)
def load_df_from_sheet(_sheet) -> pd.DataFrame:
    """Charge les données et gère la conversion datetime de 'Saisie temps'."""
    records = load_records(_sheet)
    df = pd.DataFrame(records)
    if df.empty:
        return df

    COL_TIME = "Saisie temps"
    COL_VOL = "Volume (mL)"
    COL_METH = "Méthode utilisée"

    # Vérifs colonnes minimales
    for c in (COL_TIME, COL_VOL, COL_METH):
        if c not in df.columns:
            st.error(f"Colonne manquante dans Google Sheet : '{c}'")
            return pd.DataFrame()

    # Conversion robuste -> datetime
    s = df[COL_TIME].astype(str).str.strip()

    dt = pd.to_datetime(s, format="%Y-%m-%d %H:%M:%S", errors="coerce")  # ISO
    mask = dt.isna()
    if mask.any():
        dt.loc[mask] = pd.to_datetime(s[mask], format="%d/%m/%Y %H:%M:%S", errors="coerce")  # FR
    mask = dt.isna()
    if mask.any():
        dt.loc[mask] = pd.to_datetime(s[mask], errors="coerce", dayfirst=True)  # filet

    df[COL_TIME] = dt
    df = df.dropna(subset=[COL_TIME]).copy()
    df = df.sort_values(COL_TIME, ascending=False)  # plus récent en haut

    # 👉 Supprimer colonne Horodatage si elle existe
    df = df.drop(columns=["Horodatage"], errors="ignore")

    # 👉 Ajouter colonnes Date & Heure (FR)
    df["Date"] = df[COL_TIME].dt.strftime("%d/%m/%Y")
    df["Heure"] = df[COL_TIME].dt.strftime("%H:%M")

    # 👉 Retirer 'Saisie temps' de l'affichage
    df["__dt__"] = df[COL_TIME]          # <= colonne interne pour les charts
    df = df.drop(columns=[COL_TIME], errors="ignore")  # n’apparaît plus à l’écran

    # 👉 Réordonner : Date, Heure d'abord
    cols = ["Date", "Heure"] + [c for c in df.columns if c not in ["Date", "Heure"]]
    df = df[cols]

    return df


def delete_record(sheet) -> None:
    import pandas as pd
    import streamlit as st

    records = load_records(sheet)
    df = pd.DataFrame(records)

    if df.empty:
        st.info("Aucun enregistrement.")
        return

    COL_TIME = "Saisie temps"
    COL_VOL  = "Volume (mL)"
    COL_METH = "Méthode utilisée"

    # Renomme si besoin
    if COL_VOL not in df.columns and "Volume urinaire (en mL)" in df.columns:
        df.rename(columns={"Volume urinaire (en mL)": COL_VOL}, inplace=True)
    if COL_METH not in df.columns and "Méthode" in df.columns:
        df.rename(columns={"Méthode": COL_METH}, inplace=True)

    # Datetime FR/ISO robuste
    s = df[COL_TIME].astype(str).str.strip()
    dt = pd.to_datetime(s, format="%Y-%m-%d %H:%M:%S", errors="coerce")
    m = dt.isna()
    if m.any():
        dt.loc[m] = pd.to_datetime(s[m], format="%d/%m/%Y %H:%M:%S", errors="coerce")
    m = dt.isna()
    if m.any():
        dt.loc[m] = pd.to_datetime(s[m], errors="coerce", dayfirst=True)

    df["__dt__"] = dt
    df = df.dropna(subset=["__dt__"]).copy()

    # Numéro de ligne réel (get_all_records saute l'entête)
    df["__rownum__"] = df.index + 2

    # 🔽 Tri: plus récent -> plus ancien
    df = df.sort_values("__dt__", ascending=False)

    # Libellé FR propre
    df["__label__"] = (
        df["__dt__"].dt.strftime("%d/%m/%Y %H:%M")
        + " • "
        + df[COL_VOL].fillna(0).astype(int).astype(str) + " mL"
        + " • "
        + df[COL_METH].astype(str)
    )

    st.markdown("### 🗑️ Supprimer un enregistrement")
    selected_label = st.selectbox(
        "Choisissez l’enregistrement (les plus récents en premier) :",
        df["__label__"].tolist()
    )

    sel_rownum = int(df.loc[df["__label__"] == selected_label, "__rownum__"].iloc[0])

    if st.button("Supprimer cet enregistrement ❌"):
        sheet.delete_rows(sel_rownum)
        st.cache_data.clear()
        st.success("Enregistrement supprimé.")
        st.rerun()



def build_chart(df: pd.DataFrame, weekly: bool):
    """Construit un graphique Plotly interactif avec rangeslider, lisible sur mobile."""
    COL_TIME = "Saisie temps"



    COL_VOL = "Volume (mL)"
    COL_METH = "Méthode utilisée"

    if weekly:
        df2 = df.assign(Semaine=df['__dt__'].dt.to_period("W-MON").apply(lambda p: p.start_time))
        chart_data = df2.groupby(["Semaine", COL_METH], as_index=False)[COL_VOL].sum()
        x_col = "Semaine"
        title = "📊 Volume hebdomadaire par méthode"
        window_days = 8 * 7  # ~8 semaines visibles par défaut
    else:
        df2 = df.assign(JourDate=df['__dt__'].dt.normalize())
        chart_data = df2.groupby(["JourDate", COL_METH], as_index=False)[COL_VOL].sum()
        x_col = "JourDate"
        title = "📊 Volume journalier par méthode"
        window_days = 15  # ~15 jours visibles par défaut

    # --- Graphique Plotly ---
    fig = px.bar(
        chart_data,
        x=x_col, y=COL_VOL, color=COL_METH,
        barmode="stack", title=title
    )

    # Rangeslider + fenêtre initiale
    end = pd.to_datetime(chart_data[x_col]).max()
    start = end - pd.Timedelta(days=window_days)
    fig.update_xaxes(
        type="date",
        range=[start, end],
        rangeslider=dict(visible=True),
        tickformat="%d/%m"
    )

    # Lisibilité mobile
    fig.update_layout(
        height=520,
        margin=dict(l=10, r=10, t=60, b=10),
        yaxis_title="Volume total (mL)",
        legend_title="Méthode",
        font=dict(size=18),
        bargap=0.15,
    )

    return fig
