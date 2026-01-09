import streamlit as st
import pandas as pd
import random

# Configuración de la página
st.set_page_config(page_title="Repaso Formulación", page_icon="🧪")

# Título y descripción
st.title("🧪 Entrenador de Formulación Inorgánica")
st.markdown("Pon a prueba tus conocimientos. Elige el tipo de ejercicio en el menú de la izquierda.")

# --- CARGA DE DATOS ---
@st.cache_data
def cargar_datos():
    try:
        # Cargamos el CSV. Asumimos que el separador es coma (,) estándar.
        # Si tu excel usa punto y coma (;), cambia sep=',' por sep=';'
        df = pd.read_csv("formulacion.csv", sep=',') 
        
        # Limpiamos columnas clave para evitar errores
        cols_necesarias = ['Fórmula', 'Nomenclatura Tradicional', 'Nomenclatura de Stock', 'Nomenclatura Sistemática', 'COMPUESTO']
        df = df.dropna(subset=cols_necesarias)
        return df
    except Exception as e:
        st.error(f"Error al cargar el archivo: {e}")
        return pd.DataFrame()

df = cargar_datos()

if df.empty:
    st.stop()

# --- BARRA LATERAL (FILTROS) ---
st.sidebar.header("Configuración")

# 1. Elegir Modo de Juego
modo = st.sidebar.radio(
    "¿Qué quieres practicar?",
    ["Nombrar (Ver Fórmula -> Escribir Nombre)", 
     "Formular (Ver Nombre -> Escribir Fórmula)"]
)

# 2. Filtro por Tipo de Compuesto (Usando tu columna 'COMPUESTO')
tipos_disponibles = list(df['COMPUESTO'].unique())
seleccion_tipos = st.sidebar.multiselect(
    "Filtrar por familia:",
    options=tipos_disponibles,
    default=tipos_disponibles # Por defecto selecciona todos
)

# Filtrar el DataFrame según la selección
df_juego = df[df['COMPUESTO'].isin(seleccion_tipos)]

if df_juego.empty:
    st.warning("No hay compuestos seleccionados. Marca al menos una familia en la barra lateral.")
    st.stop()

# --- LÓGICA DEL EJERCICIO ---

# Inicializar estado de la pregunta si no existe
if 'pregunta' not in st.session_state:
    st.session_state.pregunta = df_juego.sample(1).iloc[0]
    st.session_state.mostrar_solucion = False
    st.session_state.contador_aciertos = 0

# Botón para siguiente pregunta
col1, col2 = st.columns([1, 4])
with col1:
    if st.button("🔄 Siguiente"):
        st.session_state.pregunta = df_juego.sample(1).iloc[0]
        st.session_state.mostrar_solucion = False

# Mostrar contador (Gamificación simple)
st.sidebar.metric("Racha de Aciertos", st.session_state.contador_aciertos)

# --- MODO 1: FORMULAR (Te dan el nombre -> Escribes la fórmula) ---
if modo == "Formular (Ver Nombre -> Escribir Fórmula)":
    row = st.session_state.pregunta
    
    # Elegimos al azar uno de los 3 sistemas de nomenclatura disponibles en tu CSV
    sistemas = [
        ('Nomenclatura Tradicional', 'Tradicional'),
        ('Nomenclatura de Stock', 'Stock'),
        ('Nomenclatura Sistemática', 'Sistemática')
    ]
    # Filtramos sistemas que no tengan datos (por si hay celdas vacías)
    sistemas_validos = [s for s in sistemas if pd.notna(row[s[0]]) and str(row[s[0]]).strip() != '']
    
    if not sistemas_validos:
        st.error("Este compuesto no tiene nomenclaturas válidas.")
    else:
        col_sistema, nombre_sistema = random.choice(sistemas_validos)
        nombre_pregunta = row[col_sistema]

        st.subheader(f"Escribe la fórmula de:")
        st.markdown(f"### {nombre_pregunta}")
        st.caption(f"Sistema: {nombre_sistema} | Familia: {row['COMPUESTO']}")

        # Input del usuario
        respuesta = st.text_input("Tu respuesta (Ej: H2SO4):", key="input_formular")

        if respuesta:
            # Normalización básica (quitar espacios y mayúsculas)
            resp_user = respuesta.strip()
            resp_correcta = str(row['Fórmula']).strip()
            
            # Comparación (Intentamos ser flexibles con mayúsculas/minúsculas si quieres)
            # Aquí comparamos exacto respetando mayúsculas de símbolos químicos (H != h)
            if resp_user == resp_correcta:
                st.success("¡Correcto! ✅")
                if st.button("Sumar punto y Seguir"):
                     st.session_state.contador_aciertos += 1
                     st.session_state.pregunta = df_juego.sample(1).iloc[0]
                     st.session_state.mostrar_solucion = False
                     st.rerun()
            else:
                st.error(f"Incorrecto. La solución es: {resp_correcta}")

# --- MODO 2: NOMBRAR (Te dan la fórmula -> Piensas el nombre) ---
else:
    row = st.session_state.pregunta
    
    st.subheader("Nombra este compuesto:")
    st.markdown(f"## {row['Fórmula']}")
    st.caption(f"Familia: {row['COMPUESTO']}")
    
    st.info("Piensa el nombre en los diferentes sistemas y luego pulsa 'Ver Solución'.")
    
    if st.button("👁️ Ver Solución"):
        st.session_state.mostrar_solucion = True

    if st.session_state.mostrar_solucion:
        st.markdown("---")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("**Tradicional**")
            st.write(row['Nomenclatura Tradicional'])
        with c2:
            st.markdown("**Stock**")
            st.write(row['Nomenclatura de Stock'])
        with c3:
            st.markdown("**Sistemática**")
            st.write(row['Nomenclatura Sistemática'])
        
        st.write("")
        st.markdown("*¿Acertaste?*")
        col_si, col_no = st.columns(2)
        if col_si.button("¡Sí, acerté! 👍"):
            st.session_state.contador_aciertos += 1
            st.session_state.pregunta = df_juego.sample(1).iloc[0]
            st.session_state.mostrar_solucion = False
            st.rerun()
        if col_no.button("No, necesito repasar 👎"):
            st.session_state.pregunta = df_juego.sample(1).iloc[0]
            st.session_state.mostrar_solucion = False
            st.rerun()