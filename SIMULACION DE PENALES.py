import random
import pandas as pd


JUGADORES_DATOS = {
    "Lionel": {"prob_gol_base": 0.88, "zonas_preferidas": [9, 7]}, # Tira arriba a las esquinas
    "Cristiano": {"prob_gol_base": 0.85, "zonas_preferidas": [3, 1]}, # Tira abajo a las esquinas
    "Neymar": {"prob_gol_base": 0.75, "zonas_preferidas": [5]}, # Tira más al centro o despacio
    "Jugador_Promedio": {"prob_gol_base": 0.78, "zonas_preferidas": [1, 3, 7, 9]}
}

PROB_ZONA_BASE = {
    1: 0.80, 2: 0.65, 3: 0.80,  # Abajo
    4: 0.75, 5: 0.55, 6: 0.75,  # Medio
    7: 0.90, 8: 0.70, 9: 0.90   # Arriba
}

N_TIROS_SIMULACION = 5000 #probabilidad empírica


def ajustar_prob_por_estrategia(jugador, prob_base):
    """Ajusta las probabilidades de zona según la especialidad del jugador."""
    prob_jugador = prob_base.copy()
   
    for zona in jugador["zonas_preferidas"]:
        
        prob_jugador[zona] = min(1.0, prob_jugador[zona] + 0.05) 
        
    return prob_jugador

def simular_tiro_con_zona(jugador_datos):
    """
    Simula un único penal, considerando la zona a la que apunta el jugador
    y la efectividad en esa zona.
    """
    
    prob_ajustada = ajustar_prob_por_estrategia(jugador_datos, PROB_ZONA_BASE)
    
    # 2. El jugador elige la zona a la que apunta (puede ser un sesgo estratégico)
    # Aquí elegimos una de sus zonas preferidas para simular la TOMA DE DECISIONES
    if jugador_datos["zonas_preferidas"]:
        zona_apuntada = random.choice(jugador_datos["zonas_preferidas"])
    else:
        # Si no hay preferecnias, elige aleatoriamente
        zona_apuntada = random.choice(list(PROB_ZONA_BASE.keys()))
    
    # 3. Determinar si es gol usando la probabilidad de la zona
    prob_gol_en_zona = prob_ajustada[zona_apuntada]
    es_gol = random.random() < prob_gol_en_zona
    
    return zona_apuntada, es_gol

# --- 3. EJECUCIÓN DE LA SIMULACIÓN ---

resultados_simulacion = {}
mapa_global = {z: {"tiros": 0, "goles": 0} for z in range(1, 10)}

for nombre, datos in JUGADORES_DATOS.items():
    goles = 0
    
    for _ in range(N_TIROS_SIMULACION):
        zona, gol = simular_tiro_con_zona(datos)
        
        # Acumular resultados
        mapa_global[zona]["tiros"] += 1
        if gol:
            goles += 1
            mapa_global[zona]["goles"] += 1
            
    # Guardar el resultado global del jugador
    resultados_simulacion[nombre] = {
        "Goles": goles,
        "Tiros": N_TIROS_SIMULACION,
        "Efectividad": goles / N_TIROS_SIMULACION
    }

# --- 4. RESULTADOS ESPERADOS (Ranking y Mapa) ---

## Ranking de Efectividad

# Convertir los resultados de la simulación a un DataFrame para fácil visualización
df_ranking = pd.DataFrame.from_dict(resultados_simulacion, orient='index')
df_ranking = df_ranking.sort_values(by='Efectividad', ascending=False)
df_ranking['Efectividad (%)'] = (df_ranking['Efectividad'] * 100).map('{:.2f}%'.format)

print("##Ranking de Efectividad de Jugadores")
print(f"Base de simulación: {N_TIROS_SIMULACION} tiros por jugador\n")
print(df_ranking[['Tiros', 'Goles', 'Efectividad (%)']].to_markdown(numalign="left", stralign="left"))


## Mapa de Zonas de Gol

# Convertir el mapa global a un DataFrame
mapa_datos = {z: info for z, info in mapa_global.items() if info["tiros"] > 0}
df_mapa = pd.DataFrame.from_dict(mapa_datos, orient='index')
df_mapa['Efectividad'] = df_mapa['goles'] / df_mapa['tiros']
df_mapa['Efectividad (%)'] = (df_mapa['Efectividad'] * 100).map('{:.2f}%'.format)
df_mapa = df_mapa.rename(columns={"tiros": "Tiros Totales", "goles": "Goles Anotados"})

print("\n## Mapa de Zonas de Gol")
print("Análisis de efectividad combinada por zona de la portería:")
print("Zonas (1-3: Abajo | 4-6: Medio | 7-9: Arriba)\n")
print(df_mapa[['Tiros Totales', 'Goles Anotados', 'Efectividad (%)']].to_markdown(numalign="left", stralign="left"))