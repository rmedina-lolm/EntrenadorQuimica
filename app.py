import streamlit as st
import pandas as pd
import random
import unicodedata

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Formulación Inorgánica",
    page_icon="⚗️",
    layout="centered"
)

# --- ESTILOS CSS ---
st.markdown("""
    <style>
    .stApp header {visibility: hidden;} 
    .stMultiSelect {margin-top: -10px;}
    div[data-testid="stPills"] {margin-bottom: 20px;}
    /* Hacemos que la fórmula se vea grande */
    .big-formula {font-size: 40px; font-weight: bold; color: #4F8BF9; text-align: center;}
    </style>
    """, unsafe_allow_html=True)

# --- FUNCIONES AUXILIARES ---

# Función para normalizar texto (quitar tildes y minúsculas) para comparar respuestas
def normalizar(texto):
    if not isinstance(texto, str): return ""
    texto = texto.lower().strip()
    # Descomposición unicode para separar tildes de letras
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    return texto

@st.cache_data
def cargar_datos():
    try:
        df = pd.read_csv("formulacion.csv", sep=',') 
        # Limpieza básica
        cols_necesarias = ['Fórmula', 'Nomenclatura Tradicional', 'Nomenclatura de Stock', 'Nomenclatura Sistemática', 'COMPUESTO']
        df = df.dropna(subset=cols_necesarias)
        df['COMPUESTO'] = df['COMPUESTO'].str.strip()
        # Convertimos todo a string para evitar errores
        for col in cols_necesarias:
            df[col] = df[col].astype(str)
        return df
    except Exception as e:
        st.error(f"Error al cargar el archivo: {e}")
        return pd.DataFrame()

df = cargar_datos()
if df.empty: st.stop()

# --- 2. LÓGICA DE SELECCIÓN DE CONTENIDO ---

st.title("🧪 Entrenador de Formulación")

# --- A) SELECCIÓN DE FAMILIA ---
st.write("**1. Elige el contenido:**")

orden_preferido = [
    "Óxidos", "Hidruros", "Hidróxidos", "Compuestos Binarios", 
    "Sales Dobles", "Oxoácidos", "Oxosales", "Sales Ácidas", "Oxosales Ácidas"
]
categorias_en_csv = df['COMPUESTO'].unique()
mapa_categorias = {}
categorias_display = []

for cat_deseada in orden_preferido:
    for cat_real in categorias_en_csv:
        if cat_deseada.lower()[:4] in cat_real.lower()[:4]: 
            mapa_categorias[cat_deseada] = cat_real
            categorias_display.append(cat_deseada)
            break
            
for cat_real in categorias_en_csv:
    if cat_real not in mapa_categorias.values():
        categorias_display.append(cat_real)
        mapa_categorias[cat_real] = cat_real

opciones_menu = ["🔀 Mezclar Prueba"] + categorias_display

seleccion_pill = st.pills("Familia", options=opciones_menu, selection_mode="single", default=opciones_menu[0], key="pills_familia")

# Lógica de filtrado
if seleccion_pill == "🔀 Mezclar Prueba":
    seleccion_mix = st.multiselect("Familias a mezclar:", options=categorias_display, default=categorias_display[:3], label_visibility="collapsed")
    if not seleccion_mix:
        st.warning("Selecciona al menos una familia.")
        st.stop()
    filtros_reales = [mapa_categorias[x] for x in seleccion_mix]
    df_juego = df[df['COMPUESTO'].isin(filtros_reales)]
    clave_categoria_actual = f"MIX_{'-'.join(seleccion_mix)}"
else:
    if not seleccion_pill: st.stop()
    filtro_real = mapa_categorias.get(seleccion_pill, seleccion_pill)
    df_juego = df[df['COMPUESTO'] == filtro_real]
    clave_categoria_actual = f"CAT_{seleccion_pill}"

# --- B) SELECCIÓN DE MODO ---
st.write("**2. ¿Qué quieres practicar?**")
opciones_modo = ["Nombrar (Fórmula ➡️ Nombre)", "Formular (Nombre ➡️ Fórmula)"]
modos_activos = st.pills("Modo", options=opciones_modo, selection_mode="multi", default=opciones_modo, key="pills_modo")

if not modos_activos:
    st.warning("⚠️ Selecciona al menos un modo.")
    st.stop()

st.markdown("---")

# --- 3. GESTIÓN DEL ESTADO ---

if 'config_anterior' not in st.session_state:
    st.session_state.config_anterior = clave_categoria_actual

# Función para generar NUEVA pregunta
def nueva_pregunta():
    # 1. Elegir fila
    row = df_juego.sample(1).iloc[0]
    st.session_state.pregunta = row
    
    # 2. Elegir Modo (Formular o Nombrar)
    st.session_state.modo_actual = random.choice(modos_activos)
    
    # 3. Elegir Sistema de Nomenclatura VÁLIDO para esa fila
    sistemas = [
        ('Nomenclatura Tradicional', 'Tradicional'),
        ('Nomenclatura de Stock', 'Stock'),
        ('Nomenclatura Sistemática', 'Sistemática')
    ]
    # Solo nos quedamos con sistemas que tengan texto en esa celda
    sistemas_validos = [s for s in sistemas if pd.notna(row[s[0]]) and len(row[s[0]].strip()) > 1]
    
    if not sistemas_validos:
        # Si la fila está rota, intentamos otra vez (recursivo)
        nueva_pregunta()
        return

    st.session_state.sistema_elegido = random.choice(sistemas_validos)
    st.session_state.mostrar_solucion = False

# Si cambia la categoría, reseteamos
if st.session_state.config_anterior != clave_categoria_actual:
    nueva_pregunta()
    st.session_state.config_anterior = clave_categoria_actual

if 'pregunta' not in st.session_state:
    st.session_state.contador_aciertos = 0
    st.session_state.contador_fallos = 0
    nueva_pregunta()

# BARRA LATERAL (Puntuación)
if st.sidebar.button("🗑️ Reiniciar Puntuación"):
    st.session_state.contador_aciertos = 0
    st.session_state.contador_fallos = 0
    st.rerun()
st.sidebar.metric("✅ Aciertos", st.session_state.contador_aciertos)
st.sidebar.metric("❌ Fallos", st.session_state.contador_fallos)


# --- 4. RENDERIZADO DEL JUEGO ---

row = st.session_state.pregunta
modo_juego = st.session_state.modo_actual 
col_sistema, nombre_sistema = st.session_state.sistema_elegido

# Cabecera común con botón saltar
c1, c2 = st.columns([4, 1])
with c2:
    if st.button("⏭️ Saltar"):
        nueva_pregunta()
        st.rerun()

# === CASO A: FORMULAR (Te dan nombre -> Escribes fórmula) ===
if modo_juego == "Formular (Nombre ➡️ Fórmula)":
    
    nombre_pregunta = row[col_sistema]

    with c1:
        st.subheader("📝 Escribe la fórmula:")
        if "MIX" in clave_categoria_actual:
            st.caption(f"Familia: {row['COMPUESTO']}")
        
        # Mostramos el nombre centrado y grande
        st.markdown(f"<div class='big-formula'>{nombre_pregunta}</div>", unsafe_allow_html=True)
        st.info(f"Sistema pedido: **{nombre_sistema}**")

    with st.form("form_formular"):
        respuesta = st.text_input("Tu respuesta (ej: H2SO4):", autocomplete="off")
        submitted = st.form_submit_button("Comprobar")
        
        if submitted:
            # Normalización (ignoramos mayúsculas en la respuesta del usuario para ser amables, 
            # aunque en química importa, para una app móvil es mejor ser flexible).
            # Si quieres ser estricto, quita el .lower()
            resp_user = respuesta.strip()
            resp_correcta = str(row['Fórmula']).strip()
            
            if resp_user == resp_correcta: # Comparación exacta (case-sensitive)
                st.success("¡CORRECTO! 🎉")
                st.session_state.contador_aciertos += 1
                if st.form_submit_button("Siguiente ➡️"): pass
                nueva_pregunta()
                st.rerun()
            elif resp_user.lower() == resp_correcta.lower(): # Comparación flexible
                st.warning(f"¡Bien! Pero cuidado con las mayúsculas: **{resp_correcta}**")
                st.session_state.contador_aciertos += 1
                if st.form_submit_button("Siguiente ➡️"): pass
                nueva_pregunta()
                st.rerun()
            else:
                st.error("Incorrecto.")
                st.session_state.contador_fallos += 1
                st.markdown(f"Solución: **{resp_correcta}**")
                if st.form_submit_button("Intentar otro"):
                    nueva_pregunta()
                    st.rerun()

# === CASO B: NOMBRAR (Te dan fórmula -> ESCRIBES nombre específico) ===
else: 
    formula_pregunta = row['Fórmula']
    
    with c1:
        st.subheader("🗣️ Nombra el compuesto:")
        if "MIX" in clave_categoria_actual:
            st.caption(f"Familia: {row['COMPUESTO']}")
            
        st.markdown(f"<div class='big-formula'>{formula_pregunta}</div>", unsafe_allow_html=True)
        # AQUÍ ESTÁ EL CAMBIO: Pedimos un sistema concreto
        st.warning(f"Indica el nombre en **{nombre_sistema}**")

    with st.form("form_nombrar"):
        respuesta = st.text_input("Tu respuesta:", autocomplete="off")
        submitted = st.form_submit_button("Comprobar")
        
        # Botón de pánico por si no saben escribirlo
        ver_solucion = st.checkbox("No sé escribirlo, prefiero ver la solución")

        if submitted:
            if ver_solucion:
                st.info(f"La respuesta era: **{row[col_sistema]}**")
                if st.form_submit_button("Siguiente"): 
                    nueva_pregunta()
                    st.rerun()
            else:
                # Usamos la función normalizar para ignorar tildes y mayúsculas
                resp_user_norm = normalizar(respuesta)
                resp_correcta_norm = normalizar(str(row[col_sistema]))
                
                if resp_user_norm == resp_correcta_norm:
                    st.success(f"¡CORRECTO! 🎉 ({row[col_sistema]})")
                    st.session_state.contador_aciertos += 1
                    if st.form_submit_button("Siguiente ➡️"): pass
                    nueva_pregunta()
                    st.rerun()
                else:
                    st.error("Incorrecto o mal escrito.")
                    st.markdown(f"Tú escribiste: {respuesta}")
                    st.markdown(f"La solución exacta es: **{row[col_sistema]}**")
                    st.session_state.contador_fallos += 1
                    if st.form_submit_button("Intentar otro"):
                        nueva_pregunta()
                        st.rerun()