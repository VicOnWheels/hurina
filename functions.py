import streamlit as st
import pandas as pd
import plotly.express as px
import pandas as pd

@st.cache_data(ttl=30)
def load_df_from_sheet(_sheet) -> pd.DataFrame:
    """Charge les données et gère la conversion datetime de 'Saisie temps'."""
    records = _sheet.get_all_records()
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
    records = sheet.get_all_records()
    df = pd.DataFrame(records)

    if df.empty:
        st.info("Aucun enregistrement à supprimer.")
        return

    st.markdown("### 🗑️ Supprimer un enregistrement")

    # Création des libellés lisibles
    df["__label"] = df.apply(
        lambda row: f"{row['Saisie temps']} – {row['Volume (mL)']} mL – {row['Méthode utilisée']}",
        axis=1
    )
    selected_label = st.selectbox("Choisissez un enregistrement à supprimer :", df["__label"].tolist())
    selected_index = df.index[df["__label"] == selected_label][0]

    confirm = st.checkbox("✅ Je confirme vouloir supprimer cet enregistrement")

    if st.button("Supprimer cet enregistrement ❌"):
        if not confirm:
            st.warning("❗ Veuillez cocher la case de confirmation avant de supprimer.")
            return
        sheet.delete_rows(int(selected_index) + 2)  # +1 pour l'index -> 1-based, +1 pour l'entête
        st.success("✅ Enregistrement supprimé avec succès. Rechargez la page pour voir les changements.")


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
