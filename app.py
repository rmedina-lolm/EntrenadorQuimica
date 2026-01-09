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

# --- ESTILOS CSS ---
st.markdown("""
    <style>
    .stApp header {visibility: hidden;} 
    .stMultiSelect {margin-top: -10px;}
    div[data-testid="stPills"] {margin-bottom: 20px;}
    
    /* Caja de Pregunta */
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
        color: #1E88E5 !important;
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
        background-color: #f0fdf4;
        border: 2px solid #bbf7d0;
        text-align: center;
        margin-bottom: 20px;
    }
    .nota-final { font-size: 50px; font-weight: bold; color: #15803d; }
    .mensaje-final { font-size: 24px; font-weight: bold; color: #166534; margin-top: 10px; }
    
    /* Caja de Fallo */
    .fail-box {
        padding: 20px;
        border-radius: 10px;
        background-color: #FEF2F2;
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
if 'aciertos' not in st.session_state: st.session_state.aciertos = 0
if 'fallos' not in st.session_state: st.session_state.fallos = 0
if 'stats_familia' not in st.session_state: st.session_state.stats_familia = {} 
if 'contador_preguntas' not in st.session_state: st.session_state.contador_preguntas = 0
if 'estado_fase' not in st.session_state: st.session_state.estado_fase = 'respondiendo' 
if 'datos_fallo' not in st.session_state: st.session_state.datos_fallo = {}
if 'config_prev' not in st.session_state: st.session_state.config_prev = ""

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

# --- FUNCIÓN AUXILIAR: TABLA EN TIEMPO REAL ---
def mostrar_tabla_progreso():
    if st.session_state.stats_familia:
        st.markdown("---")
        st.caption("📊 Estadísticas en tiempo real:")
        
        datos_tabla = []
        for fam, datos in st.session_state.stats_familia.items():
            fallos_fam = datos['total'] - datos['aciertos']
            datos_tabla.append({
                "Compuesto": fam,
                "✅ Aciertos": datos['aciertos'],
                "❌ Fallos": fallos_fam
            })
        
        df_prog = pd.DataFrame(datos_tabla)
        st.dataframe(df_prog, hide_index=True, use_container_width=True)

# --- INTERFAZ PRINCIPAL ---
st.title("🧪 Entrenador de Formulación")

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("Progreso Global")
    aciertos = st.session_state.aciertos
    fallos = st.session_state.fallos
    total_intentos = aciertos + fallos
    
    if total_intentos > 0:
        porcentaje = (aciertos / total_intentos)
        st.progress(porcentaje)
        st.write(f"**Nota:** {aciertos}/{total_intentos} ({int(porcentaje*100)}%)")
    else:
        st.info("Sin datos aún.")
    
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
    opciones_cantidad = [5, 10, 15, 20, 25, "Sin fin"]
    limite_preguntas = st.selectbox("¿Cuántos ejercicios?", options=opciones_cantidad, index=1) 

if not modos_activos: 
    st.info("👆 Selecciona el modo de juego.")
    st.stop()

st.markdown("---")

# --- CONTROL DE CAMBIOS ---
clave_config_actual = f"{clave_cat}_{limite_preguntas}"
if st.session_state.config_prev != clave_config_actual:
    st.session_state.aciertos = 0
    st.session_state.fallos = 0
    st.session_state.stats_familia = {}
    st.session_state.config_prev = clave_config_actual
    if 'pregunta' in st.session_state: del st.session_state['pregunta']
    st.session_state.estado_fase = 'respondiendo'


# --- GAME OVER LOGIC (PANTALLA FINAL) ---
aciertos = st.session_state.aciertos
fallos = st.session_state.fallos
total_actual = aciertos + fallos
juego_terminado = False

if isinstance(limite_preguntas, int):
    st.caption(f"📝 Pregunta {total_actual + 1} de {limite_preguntas}")
    st.progress(min(total_actual / limite_preguntas, 1.0))
    if total_actual >= limite_preguntas and st.session_state.estado_fase == 'respondiendo':
        juego_terminado = True
else:
    st.caption(f"♾️ Modo Sin Fin | Llevas {total_actual} ejercicios")

if juego_terminado:
    st.balloons()
    
    # CÁLCULO DE FEEDBACK PERSONALIZADO
    porcentaje_final = (aciertos / total_actual * 100) if total_actual > 0 else 0
    
    if porcentaje_final >= 90:
        mensaje = "🌟 ¡Muy Bien!"
    elif porcentaje_final >= 80:
        mensaje = "👍 Bien"
    elif porcentaje_final >= 70:
        mensaje = "🎯 ¡Cerca del logro!"
    elif porcentaje_final >= 50:
        mensaje = "🛠️ Aún en proceso"
    else:
        mensaje = "📚 Necesitas practicar más"

    st.markdown(f"""
    <div class='resultado-box'>
        <h2>🏁 ¡Prueba Finalizada!</h2>
        <div class='nota-final'>{int(porcentaje_final)}%</div>
        <div class='mensaje-final'>{mensaje}</div>
        <p style='margin-top:10px;'>Total Aciertos: <b>{aciertos}</b> / {total_actual}</p>
    </div>
    """, unsafe_allow_html=True)
    
    mostrar_tabla_progreso()

    if st.button("🔄 Jugar de nuevo", type="primary"):
        reiniciar_todo()
    st.stop() 

# --- FUNCIONES DE LÓGICA (CON EQUILIBRADO) ---
def nueva_pregunta():
    try:
        # Equilibrado de familias
        familias_disponibles = df_juego['COMPUESTO'].unique()
        familia_azar = random.choice(familias_disponibles)
        row = df_juego[df_juego['COMPUESTO'] == familia_azar].sample(1).iloc[0]
        
        sistemas = [('Nomenclatura Tradicional', 'Tradicional'), ('Nomenclatura de Stock', 'Stock'), ('Nomenclatura Sistemática', 'Sistemática')]
        validos = []
        for col_name, display_name in sistemas:
            if col_name in row and pd.notna(row[col_name]) and len(str(row[col_name]).strip()) > 1:
                validos.append((col_name, display_name))
        
        if not validos:
            nueva_pregunta()
            return

        st.session_state.pregunta = row
        st.session_state.modo = random.choice(modos_activos)
        st.session_state.sis_elegido = random.choice(validos)
        st.session_state.contador_preguntas += 1
        st.session_state.estado_fase = 'respondiendo'
        
    except Exception as e:
        st.error(f"Error generando pregunta: {e}")

# --- INICIALIZACIÓN SEGURA ---
if 'pregunta' not in st.session_state or 'sis_elegido' not in st.session_state:
    nueva_pregunta()

# --- LÓGICA DE PANTALLA ---

# A) MOSTRAR FALLO ANTERIOR
if st.session_state.estado_fase == 'mostrar_fallo':
    datos = st.session_state.datos_fallo
    
    st.subheader("❌ Respuesta Incorrecta")
    
    st.markdown(f"""
    <div class='question-box'>
        <p style='color:#555; margin-bottom:5px;'>La pregunta era:</p>
        <div class='big-text'>{datos['pregunta']}</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class='fail-box'>
        <p><b>Tu respuesta:</b> {datos['usuario']}</p>
        <hr style='margin:10px 0; opacity:0.3;'>
        <p><b>✅ Solución Correcta:</b> <span style='font-size:1.2em;'>{datos['solucion']}</span></p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("➡️ Siguiente Pregunta", type="primary"):
        nueva_pregunta()
        st.rerun()

    mostrar_tabla_progreso()

# B) MOSTRAR PREGUNTA (Juego)
else:
    if 'pregunta' not in st.session_state: nueva_pregunta(); st.rerun()

    row = st.session_state.pregunta
    familia_actual = row['COMPUESTO']
    modo = st.session_state.modo
    
    if 'sis_elegido' in st.session_state:
        col_sis, nom_sis = st.session_state.sis_elegido
    else:
        nueva_pregunta()
        st.rerun()

    input_key = f"resp_{st.session_state.contador_preguntas}"

    c1, c2 = st.columns([4, 1])
    with c2:
        if st.button("⏭️"): nueva_pregunta(); st.rerun()

    # === FORMULAR ===
    if modo == "Formular (Nombre ➡️ Fórmula)":
        nombre_preg = row[col_sis]
        
        with c1:
            st.markdown(f"""
            <div class='question-box'>
                <div class='sub-info'>Escribe la fórmula de:</div>
                <div class='big-text'>{nombre_preg}</div>
                <div class='sub-info' style='margin-top:10px; font-weight:bold; color:#666;'>({nom_sis})</div>
            </div>
            """, unsafe_allow_html=True)

        with st.form("f1"):
            user_input = st.text_input("Tu respuesta:", autocomplete="off", key=input_key, placeholder="Ej: H2O")
            check = st.form_submit_button("Comprobar")
            
            if check:
                raw = user_input.strip()
                visual_user = embellecer_formula(raw)
                correcta_orig = str(row['Fórmula']).strip()
                correcta_clean = limpiar_subindices(correcta_orig)
                
                if raw == correcta_clean or raw == correcta_orig:
                    st.balloons()
                    st.success(f"¡CORRECTO! 🎉")
                    st.session_state.aciertos += 1
                    actualizar_stats(familia_actual, True)
                    msg = st.toast("Siguiente...", icon="⏭️")
                    time.sleep(1.2)
                    nueva_pregunta()
                    st.rerun()
                else:
                    st.session_state.fallos += 1
                    actualizar_stats(familia_actual, False)
                    st.session_state.datos_fallo = {
                        "pregunta": nombre_preg,
                        "usuario": visual_user if visual_user else "(Vacío)",
                        "solucion": correcta_orig
                    }
                    st.session_state.estado_fase = 'mostrar_fallo'
                    st.rerun()

    # === NOMBRAR ===
    else: 
        form_preg = row['Fórmula']
        with c1:
            st.markdown(f"""
            <div class='question-box'>
                <div class='sub-info'>Nombra el compuesto:</div>
                <div class='big-text'>{form_preg}</div>
                <div class='sub-info' style='margin-top:10px; font-weight:bold; color:#d97706;'>⚠️ Usar {nom_sis}</div>
            </div>
            """, unsafe_allow_html=True)

        with st.form("f2"):
            user_input = st.text_input("Tu respuesta:", autocomplete="off", key=input_key)
            col_b1, col_b2 = st.columns([1,1])
            with col_b1: check = st.form_submit_button("Comprobar")
            with col_b2: panico = st.checkbox("Me rindo (Ver solución)")

            if check:
                if panico:
                    st.session_state.fallos += 1
                    actualizar_stats(familia_actual, False)
                    st.session_state.datos_fallo = {
                        "pregunta": form_preg,
                        "usuario": "Me he rendido 🏳️",
                        "solucion": row[col_sis]
                    }
                    st.session_state.estado_fase = 'mostrar_fallo'
                    st.rerun()
                else:
                    u_norm = normalizar_texto(user_input)
                    c_norm = normalizar_texto(str(row[col_sis]))
                    
                    if u_norm == c_norm:
                        st.balloons()
                        st.success(f"¡CORRECTO! 🎉")
                        st.session_state.aciertos += 1
                        actualizar_stats(familia_actual, True)
                        msg = st.toast("Siguiente...", icon="✅")
                        time.sleep(1.2)
                        nueva_pregunta()
                        st.rerun()
                    else:
                        st.session_state.fallos += 1
                        actualizar_stats(familia_actual, False)
                        st.session_state.datos_fallo = {
                            "pregunta": form_preg,
                            "usuario": user_input if user_input else "(Vacío)",
                            "solucion": row[col_sis]
                        }
                        st.session_state.estado_fase = 'mostrar_fallo'
                        st.rerun()

    mostrar_tabla_progreso()