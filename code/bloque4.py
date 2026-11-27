"""Bloque 4 - Mundial 2026"""

import os
import pandas as pd
import requests
import plotly.express as px
import streamlit as st
import re

st.set_page_config(page_title="Mundial 2026", layout="wide")
st.title("Mundial 2026: Bloque 4")

# =====================================================================
# PARTE 1 (ELENA)
# =====================================================================

TOKEN = "ae376115d8994dbdb72ff027c1970d86"
URL = "https://api.football-data.org/v4"
HEADERS = {"X-Auth-Token": TOKEN}


def descargar_mundial():
    """
    Jugadores del Mundial 2026 con football-data.org
    """

    if os.path.exists("datos_api_mundial.csv"): # Para no ejecutar llamadas innecesarias si ya tenemos el csv
        return pd.read_csv("datos_api_mundial.csv")

    r = requests.get(f"{URL}/competitions/WC/teams", headers=HEADERS, timeout=10)
    r.raise_for_status()
    datos = r.json()

    tabla = pd.json_normalize(
        datos["teams"],
        record_path="squad",
        meta=["name"],
        meta_prefix="seleccion_",)

    tabla = tabla.rename(columns={"seleccion_name": "seleccion"})
    tabla.to_csv("datos_api_mundial.csv", index=False)

    return tabla


LIGAS = {"PL": "Premier League", "PD": "La Liga", "BL1": "Bundesliga", "SA": "Serie A", "FL1": "Ligue 1"} # Nombres oficiales de las ligas
TEMPORADA = 2025 # anterior al Mundial

def descargar_ligas():
    """Clubes de las 5 Grandes Ligas con football-data.org"""

    if os.path.exists("datos_api_ligas.csv"):
        return pd.read_csv("datos_api_ligas.csv")

    tablas = [] # una tabla por liga
    for codigo, liga in LIGAS.items():
        r = requests.get(f"{URL}/competitions/{codigo}/teams", headers=HEADERS, params={"season": TEMPORADA}, timeout=10)
        r.raise_for_status()
        tabla = pd.json_normalize(r.json()["teams"])
        tabla["liga"] = liga
        tablas.append(tabla)

    tabla = pd.concat(tablas, ignore_index=True)
    tabla = tabla[["name", "shortName", "liga"]]
    tabla = tabla.rename(columns={"name": "club", "shortName": "club_corto"})
    tabla.to_csv("datos_api_ligas.csv", index=False)
    return tabla


def limpiar(nombre):
    """En la API, el nombre de los clubs es diferente al del excel de jugadores.
    Esta función deja el nombre de un club en minúsculas y sin FC, CF, puntos, guiones 
    ni números en ambos casos para que se puedan usar"""

    nombre = nombre.lower()
    nombre = re.sub(r"[.\-]", " ", nombre)
    nombre = re.sub(r"\b(fc|cf|c|f|club|de|ac|sc|ssc|afc|cd|ud|rc)\b", "", nombre)
    nombre = re.sub(r"\d+", "", nombre)
    return " ".join(nombre.split())

def parte1():
    st.header("Parte 1: jugadores y ligas")

    mundial = descargar_mundial()
    mundial = mundial[mundial["position"] != "Coach"].copy() # quitamos los entrenadores (no son jugadores)
    mundial["mes_nacimiento"] = pd.to_datetime(mundial["dateOfBirth"]).dt.month

    st.subheader("Mes de nacimiento")
    meses = {1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun", 7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"}

    por_mes = mundial.groupby("mes_nacimiento").size().reset_index(name="jugadores")   # nº de jugadores por mes
    por_mes["nombre_mes"] = por_mes["mes_nacimiento"].replace(meses)

    por_mes["periodo"] = "Jul-Dic"
    por_mes.loc[por_mes["mes_nacimiento"] <= 6, "periodo"] = "Ene-Jun"

    fig = px.bar(por_mes, x="nombre_mes", y="jugadores", color="periodo", text="jugadores", template="plotly_white",
                color_discrete_map={"Ene-Jun": "#1f77b4", "Jul-Dic": "#aec7e8"},
                labels={"nombre_mes": "Mes de nacimiento", "jugadores": "Número de jugadores", "periodo": "Periodo"},
                title="Jugadores del Mundial 2026 por mes de nacimiento")
    
    fig.update_traces(offsetgroup=None, alignmentgroup=None, textposition="outside")
    fig.update_layout(bargap=0.2, yaxis_range=[0, por_mes["jugadores"].max() * 1.15])
    st.plotly_chart(fig)

    primer_semestre = (mundial["mes_nacimiento"].dropna() <= 6).mean() * 100
    st.write(f"Nacidos entre enero y junio: {primer_semestre:.1f}%")

    st.subheader("Grandes Ligas")
    colores = {"La Liga": "#711010", "Premier League": "#2E7D32", "Ligue 1": "#144473", "Serie A": "#FBC02D", "Bundesliga": "#6A1B9A", "Otra": "#BDBDBD"}
    jugadores = pd.read_excel("jugadoresWC26.xlsx")
    ligas = descargar_ligas()

    club_liga = {}
    for i in range(len(ligas)):
        club_liga[limpiar(ligas.loc[i, "club"])] = ligas.loc[i, "liga"] 

    jugadores["club_limpio"] = jugadores["club_jugador"].apply(limpiar)
    jugadores["liga"] = jugadores["club_limpio"].map(club_liga).fillna("Otra")

    # Jugadores en las 5 Grandes Ligas
    total = len(jugadores)
    en_grandes = (jugadores["liga"] != "Otra").sum()
    st.write(f"Jugadores en las 5 Grandes Ligas: {en_grandes} de {total} ({en_grandes / total * 100:.1f}%)")
    # Ligas más representadas
    por_liga = jugadores.groupby("liga").size().reset_index(name="jugadores")
    por_liga = por_liga.sort_values("jugadores", ascending=False)

    fig = px.bar(por_liga, x="liga", y="jugadores", text="jugadores", color="liga",
                 color_discrete_map=colores, template="plotly_white",
                 labels={"liga": "Liga", "jugadores": "Número de jugadores"},
                 title="Jugadores del Mundial 2026 por liga de su club")
    fig.update_traces(offsetgroup=None, alignmentgroup=None, textposition="outside")
    fig.update_layout(showlegend=False, bargap=0.25, yaxis_range=[0, por_liga["jugadores"].max() * 1.15])
    st.plotly_chart(fig)

    # Distribución de cada selección entre las ligas
    por_seleccion = jugadores.groupby(["seleccion_nacional", "liga"]).size().reset_index(name="jugadores")
    fig = px.bar(por_seleccion, x="jugadores", y="seleccion_nacional", color="liga", orientation="h", height=1100,
                 color_discrete_map=colores, template="plotly_white",
                 category_orders={"liga": ["Premier League", "La Liga", "Bundesliga", "Serie A", "Ligue 1", "Otra"]},
                 labels={"seleccion_nacional": "Selección", "jugadores": "Número de jugadores", "liga": "Liga"},
                 title="Distribución de los jugadores de cada selección por liga")
    fig.update_traces(offsetgroup=None, alignmentgroup=None)
    fig.update_yaxes(autorange="reversed", title_text="")
    fig.update_layout(bargap=0.2, margin=dict(t=110),
                      legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0, title_text=""))
    st.plotly_chart(fig)

    # Comparación con los Mundiales anteriores
    mundiales = pd.DataFrame({"mundial": ["2018", "2022", "2026"],
                              "totales": [736, 831, total],
                              "grandes_ligas": [385, 417, en_grandes]})
    
    mundiales = pd.DataFrame({"mundial": ["Rusia 2018", "Qatar 2022", "Norteamérica 2026"],
                              "totales": [736, 831, total],
                              "grandes_ligas": [385, 417, en_grandes]})

    mundiales["porcentaje"] = (mundiales["grandes_ligas"] / mundiales["totales"] * 100).round(1)
    fig = px.bar(mundiales, x="mundial", y="porcentaje", text="porcentaje", color="mundial",
                 color_discrete_sequence=["#1976D2", "#1976D2", "#9A1414"], template="plotly_white",
                 labels={"mundial": "Mundial", "porcentaje": "% en las 5 Grandes Ligas"},
                 title="% de jugadores en las 5 Grandes Ligas por Mundial")
    fig.update_traces(offsetgroup=None, alignmentgroup=None, texttemplate="%{text}%", textposition="outside")
    fig.update_layout(showlegend=False, bargap=0.45, yaxis_range=[0, 65])
    st.plotly_chart(fig)

parte1()

# ----- FIN PARTE 1 -----






# =====================================================================
# PARTE 2 (MARIA)
# =====================================================================




# ----- FIN PARTE 2 -----