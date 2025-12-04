import random
import pandas as pd
import tkinter as tk
from tkinter import ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

# --- 1. CONFIGURACIÓN DE DATOS EMPÍRICOS ---

# Datos iniciales de jugadores
JUGADORES_DATOS = {
    "Messi": {"prob_gol_base": 0.88, "zonas_preferidas": [9, 7]}, # Tira arriba a las esquinas
    "Cristiano": {"prob_gol_base": 0.85, "zonas_preferidas": [3, 1]}, # Tira abajo a las esquinas
    "Neymar": {"prob_gol_base": 0.75, "zonas_preferidas": [5]}, # Tira más al centro o despacio
    "Jugador_Promedio": {"prob_gol_base": 0.78, "zonas_preferidas": [1, 3, 7, 9]}
}

# Probabilidades de gol por zona (Portería dividida en 9 zonas)
PROB_ZONA_BASE = {
    1: 0.80, 2: 0.65, 3: 0.80,  # Abajo
    4: 0.75, 5: 0.55, 6: 0.75,  # Medio
    7: 0.90, 8: 0.70, 9: 0.90   # Arriba
}

N_TIROS_SIMULACION = 5000 # Base de simulación para probabilidad empírica

# --- 2. FUNCIONES DE SIMULACIÓN ---

def ajustar_prob_por_estrategia(jugador, prob_base):
    """Ajusta las probabilidades de zona según la especialidad del jugador (Toma de Decisiones)."""
    prob_jugador = prob_base.copy()
    
    # Aumenta la probabilidad de gol en sus zonas preferidas por ser más preciso ahí
    for zona in jugador["zonas_preferidas"]:
        prob_jugador[zona] = min(1.0, prob_jugador[zona] + 0.05) 
        
    return prob_jugador

def simular_tiro_con_zona(jugador_datos):
    """
    Simula un único penal, considerando la zona a la que apunta el jugador
    y la efectividad en esa zona.
    """
    prob_ajustada = ajustar_prob_por_estrategia(jugador_datos, PROB_ZONA_BASE)
    
    # El jugador elige la zona a la que apunta
    if jugador_datos["zonas_preferidas"]:
        zona_apuntada = random.choice(jugador_datos["zonas_preferidas"])
    else:
        zona_apuntada = random.choice(list(PROB_ZONA_BASE.keys()))
    
    # Determinar si es gol (Simulación Discreta)
    prob_gol_en_zona = prob_ajustada[zona_apuntada]
    es_gol = random.random() < prob_gol_en_zona
    
    return zona_apuntada, es_gol

def ejecutar_simulacion():
    """Ejecuta toda la simulación y prepara los DataFrames."""
    
    global N_TIROS_SIMULACION
    
    # Manejo de la entrada de tiros
    try:
        if 'tiros_entry' in globals():
            N_TIROS_SIMULACION = int(tiros_entry.get())
            if N_TIROS_SIMULACION <= 0:
                 N_TIROS_SIMULACION = 5000
    except ValueError:
        N_TIROS_SIMULACION = 5000 

    resultados_simulacion = {}
    
    # Inicializar mapa_global con TODAS las 9 zonas
    mapa_global = {z: {"tiros": 0, "goles": 0} for z in range(1, 10)} 

    # Ejecución de la simulación
    for nombre, datos in JUGADORES_DATOS.items():
        goles = 0
        
        for _ in range(N_TIROS_SIMULACION):
            zona, gol = simular_tiro_con_zona(datos)
            
            mapa_global[zona]["tiros"] += 1
            if gol:
                goles += 1
                mapa_global[zona]["goles"] += 1
                
        resultados_simulacion[nombre] = {
            "Goles": goles,
            "Tiros": N_TIROS_SIMULACION,
            "Efectividad": goles / N_TIROS_SIMULACION
        }

    # 4. Procesamiento de Resultados (Ranking)
    df_ranking = pd.DataFrame.from_dict(resultados_simulacion, orient='index')
    df_ranking = df_ranking.sort_values(by='Efectividad', ascending=False)
    df_ranking['Efectividad (%)'] = (df_ranking['Efectividad'] * 100)
    
    # 4. Procesamiento de Resultados (Mapa)
    
    # CORRECCIÓN CLAVE: Garantizar 9 filas
    df_mapa = pd.DataFrame.from_dict(mapa_global, orient='index') 
    df_mapa = df_mapa.reindex(range(1, 10), fill_value=0)
    
    # Calcular Efectividad, manejando la división por cero si 'tiros'=0
    df_mapa['Efectividad'] = df_mapa.apply(
        lambda row: row['goles'] / row['tiros'] if row['tiros'] > 0 else 0, 
        axis=1
    )
    
    df_mapa['Efectividad (%)'] = (df_mapa['Efectividad'] * 100)
    df_mapa = df_mapa.rename(columns={"tiros": "Tiros Totales", "goles": "Goles Anotados"})
    
    # Mostrar resultados en la GUI
    mostrar_resultados_gui(df_ranking, df_mapa)
    crear_grafico_ranking(df_ranking) # Nueva gráfica de barras
    crear_grafico_mapa(df_mapa) # Gráfica de calor simplificada

# --- 3. FUNCIONES DE LA INTERFAZ GRÁFICA (GUI) ---

def mostrar_resultados_gui(df_ranking, df_mapa):
    """Actualiza los widgets de texto con el ranking y el mapa."""
    
    ranking_text.delete(1.0, tk.END)
    mapa_text.delete(1.0, tk.END)

    # 1. Mostrar Ranking de Efectividad
    ranking_text.insert(tk.END, f"Base de simulación: {N_TIROS_SIMULACION} tiros por jugador\n\n")
    # Nota: to_markdown requiere la librería 'tabulate'
    ranking_markdown = df_ranking[['Tiros', 'Goles', 'Efectividad (%)']].to_markdown(
        numalign="left", stralign="left", floatfmt=".2f")
    ranking_text.insert(tk.END, ranking_markdown)
    
    # 2. Mostrar Mapa de Zonas
    mapa_text.insert(tk.END, "Zonas (1-3: Abajo | 4-6: Medio | 7-9: Arriba)\n\n")
    mapa_markdown = df_mapa[['Tiros Totales', 'Goles Anotados', 'Efectividad (%)']].to_markdown(
        numalign="left", stralign="left", floatfmt=".2f")
    mapa_text.insert(tk.END, mapa_markdown)

# --- Gráfica 1: Ranking de Jugadores (Barras) ---
def crear_grafico_ranking(df_ranking):
    """Crea y muestra el gráfico de barras del ranking de jugadores."""
    
    for widget in grafico_ranking_frame.winfo_children():
        widget.destroy()

    jugadores = df_ranking.index
    efectividad_pct = df_ranking['Efectividad (%)'].values
    
    fig = Figure(figsize=(5, 4), dpi=100)
    ax = fig.add_subplot(111)
    
    bars = ax.bar(jugadores, efectividad_pct, color=['#003366', '#0077B6', '#4CAF50', '#FFC300'])
    
    ax.set_title('Ranking de Efectividad (Simulación)', fontsize=12)
    ax.set_ylabel('Efectividad (%)')
    ax.set_ylim(0, 100)
    
    # Etiquetas de valor encima de cada barra
    for bar in bars:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2, yval + 1, f'{yval:.2f}%', ha='center', va='bottom', fontsize=8)

    canvas = FigureCanvasTkAgg(fig, master=grafico_ranking_frame)
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=1)
    canvas.draw()

# --- Gráfica 2: Mapa de Zonas (Calor Simplificado) ---
def crear_grafico_mapa(df_mapa):
    """Crea y muestra el gráfico de calor del mapa de zonas con etiquetas amigables."""
    
    for widget in grafico_mapa_frame.winfo_children():
        widget.destroy()

    # Los valores de 'Efectividad' están garantizados de 1 a 9 (índices 0 a 8)
    efectividades = df_mapa['Efectividad'].values
    
    # Mapeo de índices a la matriz 3x3 de la portería
    mapa_matriz = [
        [efectividades[6], efectividades[7], efectividades[8]], # Zonas 7, 8, 9 (Arriba)
        [efectividades[3], efectividades[4], efectividades[5]], # Zonas 4, 5, 6 (Medio)
        [efectividades[0], efectividades[1], efectividades[2]]  # Zonas 1, 2, 3 (Abajo)
    ]
    
    # Etiquetas descriptivas para la matriz 3x3
    etiquetas_matriz = [
        ["Sup. Izq.", "Sup. Cen.", "Sup. Der."],
        ["Medio Izq.", "Centro", "Medio Der."],
        ["Inf. Izq.", "Inf. Cen.", "Inf. Der."]
    ]
    
    fig = Figure(figsize=(5, 4), dpi=100)
    ax = fig.add_subplot(111)
    
    # Gráfico de calor
    im = ax.imshow(mapa_matriz, cmap='YlGn', vmin=0.0, vmax=1.0) 
    
    # Etiquetas de la portería
    ax.set_xticks([0, 1, 2])
    ax.set_yticks([0, 1, 2])
    ax.set_xticklabels(['Izquierda', 'Centro', 'Derecha'])
    ax.set_yticklabels(['Arriba', 'Medio', 'Abajo'])
    ax.set_title('Mapa de Éxito por Posición de Tiro', fontsize=12)
    
    # Etiquetas de datos y texto descriptivo
    for i in range(3):
        for j in range(3):
            valor = mapa_matriz[i][j] * 100
            etiqueta = etiquetas_matriz[i][j]
            
            # El color del texto ayuda a la legibilidad
            text_color = "black" if valor < 70 else "white"

            text = ax.text(j, i, f"{etiqueta}\n{valor:.1f}%",
                           ha="center", va="center", color=text_color, fontsize=8, weight='bold')
            
    # Añadir barra de color
    fig.colorbar(im, ax=ax, label='Probabilidad de Gol (%)')
    
    canvas = FigureCanvasTkAgg(fig, master=grafico_mapa_frame)
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=1)
    canvas.draw()


# --- 4. CONFIGURACIÓN DE LA VENTANA PRINCIPAL (Tkinter) ---

root = tk.Tk()
root.title("⚽ Simulación de Tiros Libres/Penales")
root.geometry("1200x700")

# 1. Frame de Control
control_frame = ttk.Frame(root, padding="10")
control_frame.pack(fill='x')

ttk.Label(control_frame, text="Número de Tiros por Jugador:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=5)
tiros_entry = ttk.Entry(control_frame, width=10)
tiros_entry.insert(0, str(N_TIROS_SIMULACION))
tiros_entry.pack(side=tk.LEFT, padx=5)

run_button = ttk.Button(control_frame, text="▶️ Ejecutar Simulación", command=ejecutar_simulacion)
run_button.pack(side=tk.LEFT, padx=20)


# 2. Frame de Resultados (Contenedor principal)
results_frame = ttk.Frame(root, padding="10")
results_frame.pack(fill=tk.BOTH, expand=True)

# 2a. Panel de Ranking (Izquierda)
ranking_frame = ttk.LabelFrame(results_frame, text="🏆 Ranking de Efectividad (Tabla)", padding="10")
ranking_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

ranking_text = tk.Text(ranking_frame, wrap=tk.WORD, height=15, font=('Courier', 10))
ranking_text.pack(fill=tk.BOTH, expand=True)


# 2b. Panel de Mapa (Derecha)
mapa_frame = ttk.LabelFrame(results_frame, text="🗺️ Mapa de Zonas de Gol (Tabla)", padding="10")
mapa_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

mapa_text = tk.Text(mapa_frame, wrap=tk.WORD, height=15, font=('Courier', 10))
mapa_text.pack(fill=tk.BOTH, expand=True)


# 3. Frame para las Gráficas (Abajo)
graficas_base_frame = ttk.Frame(root, padding="10")
graficas_base_frame.pack(fill='both', expand=True)

# 3a. Frame para el Gráfico de Ranking (Izquierda)
grafico_ranking_frame = ttk.LabelFrame(graficas_base_frame, text="🏆 Gráfico de Ranking de Jugadores", padding="10")
grafico_ranking_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

# 3b. Frame para el Gráfico de Mapa (Derecha)
grafico_mapa_frame = ttk.LabelFrame(graficas_base_frame, text="🔥 Mapa de Éxito por Posición de Tiro", padding="10")
grafico_mapa_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

# Iniciar la simulación al abrir la GUI
ejecutar_simulacion()

root.mainloop()