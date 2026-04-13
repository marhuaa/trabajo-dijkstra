import streamlit as st
import folium
import heapq
from streamlit_folium import st_folium

# ==========================================
# 1. BASE DE DATOS GEOGRÁFICA
# ==========================================
capitales = {
    "Chachapoyas": [-6.2294, -77.8728], "Huaraz": [-9.5278, -77.5278],
    "Abancay": [-13.6339, -72.8814], "Arequipa": [-16.4090, -71.5375],
    "Ayacucho": [-13.1588, -74.2239], "Cajamarca": [-7.1638, -78.5003],
    "Callao": [-12.0560, -77.1181], "Cusco": [-13.5319, -71.9675],
    "Huancavelica": [-12.7826, -74.9727], "Huánuco": [-9.9306, -76.2422],
    "Ica": [-14.0678, -75.7286], "Huancayo": [-12.0651, -75.2045],
    "Trujillo": [-8.1160, -79.0300], "Chiclayo": [-6.7711, -79.8442],
    "Lima": [-12.0464, -77.0428], "Iquitos": [-3.7437, -73.2516],
    "Puerto Maldonado": [-12.5933, -69.1833], "Moquegua": [-17.1983, -70.9357],
    "Cerro de Pasco": [-10.6675, -76.2567], "Piura": [-5.1945, -80.6328],
    "Puno": [-15.8402, -70.0212], "Moyobamba": [-6.0342, -76.9717],
    "Tacna": [-18.0117, -70.2536], "Tumbes": [-3.5669, -80.4515],
    "Pucallpa": [-8.3791, -74.5539]
}

# Red de carreteras principales (Distancias referenciales en KM)
grafo_peru = {
    # Costa Norte a Sur (Panamericana)
    "Tumbes": {"Piura": 280},
    "Piura": {"Tumbes": 280, "Chiclayo": 210},
    "Chiclayo": {"Piura": 210, "Trujillo": 200, "Cajamarca": 260, "Chachapoyas": 430},
    "Trujillo": {"Chiclayo": 200, "Huaraz": 310, "Lima": 560},
    "Lima": {"Trujillo": 560, "Huaraz": 400, "Callao": 15, "Huancayo": 310, "Ica": 300},
    "Callao": {"Lima": 15},
    "Ica": {"Lima": 300, "Ayacucho": 330, "Arequipa": 700},
    "Arequipa": {"Ica": 700, "Moquegua": 220, "Puno": 290, "Cusco": 510},
    "Moquegua": {"Arequipa": 220, "Tacna": 160, "Puno": 260},
    "Tacna": {"Moquegua": 160},
    
    # Sierra Sur y Centro
    "Puno": {"Arequipa": 290, "Moquegua": 260, "Cusco": 390},
    "Cusco": {"Puno": 390, "Arequipa": 510, "Abancay": 190, "Puerto Maldonado": 480},
    "Puerto Maldonado": {"Cusco": 480},
    "Abancay": {"Cusco": 190, "Ayacucho": 390},
    "Ayacucho": {"Abancay": 390, "Ica": 330, "Huancavelica": 245},
    "Huancavelica": {"Ayacucho": 245, "Huancayo": 150},
    "Huancayo": {"Huancavelica": 150, "Lima": 310, "Cerro de Pasco": 230},
    "Cerro de Pasco": {"Huancayo": 230, "Huánuco": 100},
    "Huánuco": {"Cerro de Pasco": 100, "Huaraz": 300, "Pucallpa": 380},
    "Huaraz": {"Huánuco": 300, "Trujillo": 310, "Lima": 400},
    
    # Selva y Norte Oriente
    "Pucallpa": {"Huánuco": 380},
    "Cajamarca": {"Chiclayo": 260},
    "Chachapoyas": {"Chiclayo": 430, "Moyobamba": 230},
    "Moyobamba": {"Chachapoyas": 230},
    "Iquitos": {} # Sin conexión terrestre principal
}

# ==========================================
# 2. ALGORITMO DE DIJKSTRA
# ==========================================
def dijkstra(grafo, inicio, fin):
    cola = [(0, inicio)]
    distancias = {nodo: float('inf') for nodo in capitales}
    distancias[inicio] = 0
    padres = {}
    
    while cola:
        d_actual, nodo_actual = heapq.heappop(cola)
        
        if nodo_actual == fin: 
            break
            
        for vecino, peso in grafo.get(nodo_actual, {}).items():
            distancia = d_actual + peso
            if distancia < distancias.get(vecino, float('inf')):
                distancias[vecino] = distancia
                padres[vecino] = nodo_actual
                heapq.heappush(cola, (distancia, vecino))
                
    camino, aux = [], fin
    while aux in padres:
        camino.insert(0, aux)
        aux = padres[aux]
    if camino: 
        camino.insert(0, inicio)
        
    return camino, distancias[fin]

# ==========================================
# 3. CONFIGURACIÓN DE PÁGINA Y ESTADO
# ==========================================
st.set_page_config(page_title="Dijkstra Perú", layout="wide")

# Inicializar variables de sesión para que no se borre el mapa
if 'contador' not in st.session_state:
    st.session_state.contador = 0
if 'ruta' not in st.session_state:
    st.session_state.ruta = []
if 'distancia' not in st.session_state:
    st.session_state.distancia = 0

# ==========================================
# 4. INTERFAZ DE USUARIO (SIDEBAR)
# ==========================================
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/cf/Flag_of_Peru.svg/200px-Flag_of_Peru.svg.png", width=100)
    st.header("📍 Parámetros de Ruta")
    
    lista_ciudades = list(capitales.keys())
    # Índices por defecto: Puno (20) y Lima (14)
    origen = st.selectbox("Ciudad de Origen", lista_ciudades, index=20)
    destino = st.selectbox("Ciudad de Destino", lista_ciudades, index=14)
    
    st.markdown("---")
    
    if st.button("🚀 Encontrar Camino Más Corto", use_container_width=True):
        # Ejecutar algoritmo
        ruta_calc, dist_calc = dijkstra(grafo_peru, origen, destino)
        
        # Guardar en el estado de la sesión
        st.session_state.ruta = ruta_calc
        st.session_state.distancia = dist_calc
        
        # Sumar al contador (Clave para que el mapa se recargue SIEMPRE)
        st.session_state.contador += 1

    # Panel de resultados laterales
    if st.session_state.ruta:
        st.markdown("### 📊 Resumen de Viaje")
        st.success(f"**Distancia Total:**\n{st.session_state.distancia} KM")
        st.info("**Ruta Óptima:**\n\n" + " ➔ \n".join(st.session_state.ruta))

# ==========================================
# 5. RENDERIZADO DEL MAPA
# ==========================================
st.title("🗺️ Optimización de Rutas Nacionales (Dijkstra)")
st.markdown("Modelo de red de carreteras interdepartamentales del Perú.")

# Mapa base centrado en Perú
m = folium.Map(location=[-9.19, -75.01], zoom_start=6, tiles="CartoDB positron")

# Dibujar nodos base (Puntos grises para todas las capitales)
for ciudad, coords in capitales.items():
    folium.CircleMarker(
        location=coords, radius=3, color="gray", fill=True, popup=ciudad
    ).add_to(m)

# Dibujar la ruta si existe
if st.session_state.ruta:
    ruta_nombres = st.session_state.ruta
    puntos = [capitales[n] for n in ruta_nombres]
    
    # Línea de ruta
    folium.PolyLine(puntos, color="#FF0000", weight=5, opacity=0.8).add_to(m)
    
    # Marcadores de la ruta
    for i, nombre in enumerate(ruta_nombres):
        if i == 0:
            color, icono = 'green', 'play' # Origen
        elif i == len(ruta_nombres) - 1:
            color, icono = 'red', 'stop'   # Destino
        else:
            color, icono = 'orange', 'info-sign' # Nodos intermedios
            
        folium.Marker(
            location=capitales[nombre],
            popup=f"{i+1}. {nombre}",
            icon=folium.Icon(color=color, icon=icono)
        ).add_to(m)
elif st.session_state.distancia == float('inf'):
    st.error(f"⚠️ No existe una conexión terrestre configurada entre {origen} y {destino} (Ej: Iquitos solo tiene acceso fluvial/aéreo).")

# Renderizar el mapa con el KEY DINÁMICO
st_folium(m, width=1200, height=650, key=f"mapa_{st.session_state.contador}")