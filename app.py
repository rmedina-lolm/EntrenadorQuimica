import streamlit as st
import pandas as pd
import random
import unicodedata
import time

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Formulación Inorgánica",
    page_icon="⚗️",
    layout="centered"
)

# --- ESTILOS CSS (MEJORADOS PARA VISIBILIDAD) ---
st.markdown("""
    <style>
    .stApp header {visibility: hidden;} 
    .stMultiSelect {margin-top: -10px;}
    div[data-testid="stPills"] {margin-bottom: 20px;}
    
    /* Caja de Pregunta (Fondo blanco para asegurar contraste) */
    .question-box {
        background-color: #ffffff;
        border: 2px solid #d1d5db;
        border-radius: 15px;
        padding: 25px;
        text-align: center;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .big-text {
        font-size: 38px !important;
        font-weight: bold;
        color: #1E88E5 !important; /* Azul fuerte */
        margin: 0;
        font-family: sans-serif;
        line-height: 1.4;
    }
    
    .sub-info {
        color: #555;
        font-size: 16px;
        margin-top: 5px;
    }

    /* Caja de Resultado Final */
    .resultado-box {
        padding: 30px;
        border-radius: 15px;
        background-color: #f0fdf4; /* Verde muy claro */
        border: 2px solid #bbf7d0;
        text-align: center;
        margin-bottom: 20px;
    }
    .nota-final { font-size: 60px; font-weight: bold; color: #15803d; }
    
    /* Caja de Fallo */
    .fail-box {
        padding: 20px;
        border-radius: 10px;
        background-color: #FEF2F2; /* Rojo muy claro */
        border: 2px solid #FECACA;
        margin-bottom: 15px;
        color: #991B1B;
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCIONES DE TEXTO ---
def embellecer_formula(texto):
    if not isinstance(texto, str): return ""
    tabla = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")
    return texto.translate(tabla)

def limpiar_subindices(texto):
    if not isinstance(texto, str): return ""
    tabla = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")
    return texto.translate(tabla)

def normalizar_texto(texto):
    if not isinstance(texto, str): return ""
    texto = texto.lower().strip()
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    return texto

# --- CARGA DE DATOS ---
@st.cache_data
def cargar_datos():
    try:
        df = pd.read_csv("formulacion.csv", sep=',') 
        cols = ['Fórmula', 'Nomenclatura Tradicional', 'Nomenclatura de Stock', 'Nomenclatura Sistemática', 'COMPUESTO']
        # Limpieza básica
        df = df.dropna(subset=['Fórmula', 'COMPUESTO'])
        df['COMPUESTO'] = df['COMPUESTO'].str.strip()
        for col in cols:
            if col in df.columns:
                df[col] = df[col].astype(str)
        return df
    except Exception as e:
        st.error(f"Error crítico al cargar: {e}")
        return pd.DataFrame()

df = cargar_datos()
if df.empty: st.stop()

# --- GESTIÓN DE VARIABLES DE ESTADO ---
if 'stats_familia' not in st.session_state: st.session_state.stats_familia = {} 
if 'contador_preguntas' not in st.session_state: st.session_state.contador_preguntas = 0
if 'estado_fase' not in st.session_state: st.session_state.estado_fase = 'respondiendo' 
if 'datos_fallo' not in st.session_state: st.session_state.datos_fallo = {}

def actualizar_stats(familia, es_acierto):
    if familia not in st.session_state.stats_familia:
        st.session_state.stats_familia[familia] = {'aciertos': 0, 'total': 0}
    st.session_state.stats_familia[familia]['total'] += 1
    if es_acierto:
        st.session_state.stats_familia[familia]['aciertos'] += 1

def reiniciar_todo():
    st.session_state.aciertos = 0
    st.session_state.fallos = 0
    st.session_state.stats_familia = {}
    st.session_state.contador_preguntas = 0
    st.session_state.estado_fase = 'respondiendo'
    if 'pregunta' in st.session_state: del st.session_state['pregunta']
    st.rerun()

# --- FUNCIONES DE LÓGICA ---
def nueva_pregunta():
    # Selección segura
    try:
        row = df_juego.sample(1).iloc[0]
        
        # Validación de columnas
        sistemas = [('Nomenclatura Tradicional', 'Tradicional'), ('Nomenclatura de Stock', 'Stock'), ('Nomenclatura Sistemática', 'Sistemática')]
        validos = []
        for col_name, display_name in sistemas:
            if col_name in row and pd.notna(row[col_name]) and len(str(row[col_name]).strip()) > 1:
                validos.append((col_name, display_name))
        
        if not validos:
            # Si esta fila está rota, probamos otra recursivamente (con límite para no colgar)
            nueva_pregunta()
            return

        st.session_state.pregunta = row
        st.session_state.modo = random.choice(modos_activos)
        st.session_state.sis_elegido = random.choice(validos)
        st.session_state.contador_preguntas += 1
        st.session_state.estado_fase = 'respondiendo'
        
    except Exception as e:
        st.error(f"Error generando pregunta: {e}")

# --- INTERFAZ PRINCIPAL ---
st.title("🧪 Entrenador de Formulación")

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("📊 Tu Progreso")
    aciertos = st.session_state.get('aciertos', 0)
    fallos = st.session_state.get('fallos', 0)
    total_intentos = aciertos + fallos
    
    if total_intentos > 0:
        porcentaje = (aciertos / total_intentos)
        st.progress(porcentaje)
        st.write(f"**Nota Global:** {aciertos}/{total_intentos} ({int(porcentaje*100)}%)")
    else:
        st.info("Responde para ver tu nota.")
    
    st.divider()
    if st.button("🗑️ Reiniciar Sesión"):
        reiniciar_todo()

# --- 1. CONFIGURACIÓN DEL JUEGO ---
st.write("**1. Elige el contenido:**")
orden = ["Óxidos", "Hidruros", "Hidróxidos", "Compuestos Binarios", "Sales Dobles", "Oxoácidos", "Oxosales", "Sales Ácidas", "Oxosales Ácidas"]
cat_csv = df['COMPUESTO'].unique()
mapa = {}
cat_display = []

for deseada in orden:
    for real in cat_csv:
        if deseada.lower()[:4] in real.lower()[:4]: 
            mapa[deseada] = real
            cat_display.append(deseada)
            break
for real in cat_csv:
    if real not in mapa.values():
        cat_display.append(real)
        mapa[real] = real

opciones_menu = ["🔀 Mezclar Prueba"] + cat_display
seleccion = st.pills("Familia", options=opciones_menu, selection_mode="single", default=None, key="pills_familia")

if not seleccion:
    st.info("👆 Selecciona primero un tipo de compuesto para empezar.")
    st.stop()

if seleccion == "🔀 Mezclar Prueba":
    mix = st.multiselect("Familias:", options=cat_display, default=cat_display[:3], label_visibility="collapsed")
    if not mix: 
        st.warning("Selecciona al menos una familia.")
        st.stop()
    filtros = [mapa[x] for x in mix]
    df_juego = df[df['COMPUESTO'].isin(filtros)]
    clave_cat = f"MIX_{'-'.join(mix)}"
else:
    filtro = mapa.get(seleccion, seleccion)
    df_juego = df[df['COMPUESTO'] == filtro]
    clave_cat = f"CAT_{seleccion}"

st.write("**2. Configura tu práctica:**")
col_modo, col_cant = st.columns([2, 1])
with col_modo:
    modos = ["Nombrar (Fórmula ➡️ Nombre)", "Formular (Nombre ➡️ Fórmula)"]
    modos_activos = st.pills("Modo", options=modos, selection_mode="multi", default=[], key="pills_modo")

with col_cant:
    opciones_cantidad = [5, 10, 15, 20, 25, "