"""Bloque 4 - Mundial 2026"""
import os
import pandas as pd
import requests
import plotly.express as px
import streamlit as st

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


def parte1():

    mundial = descargar_mundial()
    mundial = mundial[mundial["position"] != "Coach"].copy() # quitamos los entrenadores (no son jugadores)
    mundial["mes_nacimiento"] = pd.to_datetime(mundial["dateOfBirth"]).dt.month

    meses = {1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun", 7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic"}

    por_mes = mundial["mes_nacimiento"].value_counts().sort_index().reset_index()
    por_mes.columns = ["mes", "jugadores"]
    por_mes["nombre_mes"] = por_mes["mes"].replace(meses)

    por_mes["periodo"] = "Jul-Dic"
    por_mes.loc[por_mes["mes"] <= 6, "periodo"] = "Ene-Jun"

    fig = px.bar(por_mes, x="nombre_mes", y="jugadores", color="periodo", text="jugadores",
                color_discrete_map={"Ene-Jun": "#1f77b4", "Jul-Dic": "#aec7e8"},
                labels={"nombre_mes": "Mes de nacimiento", "jugadores": "Número de jugadores"},
                title="Jugadores del Mundial 2026 por mes de nacimiento")
    fig.show()

    primer_semestre = (mundial["mes_nacimiento"].dropna() <= 6).mean() * 100
    print(f"Nacidos entre enero y junio: {primer_semestre:.1f}%")


parte1()

# ----- FIN PARTE 1 -----






# =====================================================================
# PARTE 2 (MARIA)
# =====================================================================




# ----- FIN PARTE 2 -----