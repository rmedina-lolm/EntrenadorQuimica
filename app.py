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
    .big-formula {font-size: 40px; font-weight: bold; color: #4F8BF9; text-align: center; font-family: sans-serif;}
    .user-response {font-size: 24px; font-weight: bold; color: #333;}
    div[data-testid="stForm"] button {width: 100%;}
    
    /* Estilo para la tarjeta de resultados final */
    .resultado-box {
        padding: 20px;
        border-radius: 10px;
        background-color: #f0f2f6;
        text-align: center;
        margin-bottom: 20px;
    }
    .nota-final { font-size: 50px; font-weight: bold; color: #2E86C1; }
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
        df = df.dropna(subset=cols)
        df['COMPUESTO'] = df['COMPUESTO'].str.strip()
        for col in cols:
            df[col] = df[col].astype(str)
        return df
    except Exception as e:
        st.error(f"Error al cargar el archivo: {e}")
        return pd.DataFrame()

df = cargar_datos()
if df.empty: st.stop()

# --- GESTIÓN DE ESTADÍSTICAS ---
if 'stats_familia' not in st.session_state:
    st.session_state.stats_familia = {} 

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
    st.rerun()

# --- INTERFAZ PRINCIPAL ---

st.title("🧪 Entrenador de Formulación")

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("📊 Tu Progreso")
    
    aciertos = st.session_state.get('aciertos', 0)
    fallos = st.session_state.get('fallos', 0)
    total_intentos = aciertos + fallos
    
    # Visualización Global
    if total_intentos > 0:
        porcentaje = (aciertos / total_intentos)
        st.progress(porcentaje)
        st.write(f"**Nota Global:** {aciertos}/{total_intentos} ({int(porcentaje*100)}%)")
    else:
        st.info("Responde para ver tu nota.")

    st.divider()

    # Desglose
    with st.expander("Ver desglose por temas", expanded=False):
        if not st.session_state.stats_familia:
            st.caption("Aún no hay datos.")
        else:
            datos_tabla = []
            for fam, datos in st.session_state.stats_familia.items():
                datos_tabla.append({
                    "Familia": fam,
                    "✅": datos['aciertos'],
                    "Total": datos['total']
                })
            df_stats = pd.DataFrame(datos_tabla)
            st.dataframe(df_stats, hide_index=True, use_container_width=True)

    st.divider()
    if st.button("🗑️ Reiniciar Sesión"):
        reiniciar_todo()

# --- 1. CONFIGURACIÓN DEL JUEGO ---

# A) FAMILIA
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
seleccion = st.pills("Familia", options=opciones_menu, selection_mode="single", default=opciones_menu[0], key="pills_familia")

if seleccion == "🔀 Mezclar Prueba":
    mix = st.multiselect("Familias:", options=cat_display, default=cat_display[:3], label_visibility="collapsed")
    if not mix: st.stop()
    filtros = [mapa[x] for x in mix]
    df_juego = df[df['COMPUESTO'].isin(filtros)]
    clave_cat = f"MIX_{'-'.join(mix)}"
else:
    if not seleccion: st.stop()
    filtro = mapa.get(seleccion, seleccion)
    df_juego = df[df['COMPUESTO'] == filtro]
    clave_cat = f"CAT_{seleccion}"

# B) MODO Y CANTIDAD (NUEVO)
st.write("**2. Configura tu práctica:**")
col_modo, col_cant = st.columns([2, 1])

with col_modo:
    modos = ["Nombrar (Fórmula ➡️ Nombre)", "Formular (Nombre ➡️ Fórmula)"]
    modos_activos = st.pills("Modo", options=modos, selection_mode="multi", default=modos, key="pills_modo")

with col_cant:
    opciones_cantidad = [5, 10, 15, 20, 25, "Sin fin"]
    limite_preguntas = st.selectbox("¿Cuántos ejercicios?", options=opciones_cantidad, index=1) # Default 10

if not modos_activos: st.warning("Selecciona un modo"); st.stop()

st.markdown("---")

# --- CONTROL DE CAMBIOS Y RESET ---
# Si cambia la familia o el límite, reiniciamos el contador interno de esta "partida"
clave_config_actual = f"{clave_cat}_{limite_preguntas}"
if 'config_prev' not in st.session_state: st.session_state.config_prev = clave_config_actual

if st.session_state.config_prev != clave_config_actual:
    st.session_state.aciertos = 0
    st.session_state.fallos = 0
    st.session_state.stats_familia = {}
    st.session_state.config_prev = clave_config_actual
    # Forzar nueva pregunta
    if 'pregunta' in st.session_state: del st.session_state['pregunta']


# --- LÓGICA DE FINALIZACIÓN DE JUEGO (GAME OVER) ---

total_actual = st.session_state.get('aciertos', 0) + st.session_state.get('fallos', 0)
juego_terminado = False

if isinstance(limite_preguntas, int):
    # Si hay límite numérico
    st.caption(f"📝 Pregunta {total_actual + 1} de {limite_preguntas}")
    st.progress(min(total_actual / limite_preguntas, 1.0))
    
    if total_actual >= limite_preguntas:
        juego_terminado = True
else:
    # Modo sin fin
    st.caption(f"♾️ Modo Sin Fin | Llevas {total_actual} ejercicios")


if juego_terminado:
    # === PANTALLA DE RESULTADOS ===
    st.balloons()
    
    nota_final = int((aciertos / total_actual) * 10) if total_actual > 0 else 0
    
    if nota_final >= 9: mensaje = "🏆 ¡EXCELENTE!"
    elif nota_final >= 7: mensaje = "👏 ¡MUY BIEN!"
    elif nota_final >= 5: mensaje = "👍 APROBADO"
    else: mensaje = "💪 ¡A SEGUIR PRACTICANDO!"

    st.markdown(f"""
    <div class='resultado-box'>
        <h2>🏁 ¡Prueba Finalizada!</h2>
        <div class='nota-final'>{nota_final}/10</div>
        <p>{mensaje}</p>
        <p>Has acertado <b>{aciertos}</b> de <b>{total_actual}</b> preguntas.</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🔄 Volver a Jugar (Reiniciar)"):
        reiniciar_todo()
    
    st.stop() # Detiene la ejecución para no mostrar más preguntas

# --- GENERACIÓN DE PREGUNTA ---

def nueva_pregunta():
    row = df_juego.sample(1).iloc[0]
    st.session_state.pregunta = row
    st.session_state.modo = random.choice(modos_activos)
    
    sistemas = [('Nomenclatura Tradicional', 'Tradicional'), ('Nomenclatura de Stock', 'Stock'), ('Nomenclatura Sistemática', 'Sistemática')]
    validos = [s for s in sistemas if pd.notna(row[s[0]]) and len(row[s[0]].strip()) > 1]
    
    if not validos: nueva_pregunta(); return

    st.session_state.sis_elegido = random.choice(validos)

if 'pregunta' not in st.session_state:
    st.session_state.aciertos = 0
    st.session_state.fallos = 0
    nueva_pregunta()

# --- JUEGO ACTIVO ---
row = st.session_state.pregunta
familia_actual = row['COMPUESTO']
modo = st.session_state.modo
col_sis, nom_sis = st.session_state.sis_elegido

c1, c2 = st.columns([4, 1])
with c2:
    if st.button("⏭️ Saltar"): nueva_pregunta(); st.rerun()

# === FORMULAR ===
if modo == "Formular (Nombre ➡️ Fórmula)":
    nombre_preg = row[col_sis]
    
    with c1:
        st.subheader("📝 Escribe la fórmula:")
        if "MIX" in clave_cat: st.caption(f"Familia: {familia_actual}")
        st.markdown(f"<div class='big-formula'>{nombre_preg}</div>", unsafe_allow_html=True)
        st.info(f"Sistema: **{nom_sis}**")
        st.caption("Escribe números normales (ej: H2O)")

    with st.form("f1"):
        user_input = st.text_input("Respuesta:", autocomplete="off")
        check = st.form_submit_button("Comprobar")
        
        if check:
            raw = user_input.strip()
            visual_user = embellecer_formula(raw)
            correcta_orig = str(row['Fórmula']).strip()
            correcta_clean = limpiar_subindices(correcta_orig)
            
            if raw == correcta_clean or raw == correcta_orig:
                st.balloons()
                st.success(f"¡CORRECTO! 🎉")
                st.markdown(f"Interpretado como: **{visual_user}**")
                
                st.session_state.aciertos += 1
                actualizar_stats(familia_actual, True)
                
                msg = st.toast("Siguiente...", icon="⏭️")
                time.sleep(1.5)
                nueva_pregunta()
                st.rerun()
            else:
                st.error("Incorrecto")
                st.markdown(f"Tú: **{visual_user}** | Solución: **{correcta_orig}**")
                
                st.session_state.fallos += 1
                actualizar_stats(familia_actual, False)
                
                if st.form_submit_button("Siguiente"): # Cambiado de "Reintentar" a Siguiente para fluidez en modo examen
                    nueva_pregunta()
                    st.rerun()

# === NOMBRAR ===
else: 
    form_preg = row['Fórmula']
    with c1:
        st.subheader("🗣️ Nombra el compuesto:")
        if "MIX" in clave_cat: st.caption(f"Familia: {familia_actual}")
        st.markdown(f"<div class='big-formula'>{form_preg}</div>", unsafe_allow_html=True)
        st.warning(f"Indica el nombre en **{nom_sis}**")

    with st.form("f2"):
        user_input = st.text_input("Respuesta:", autocomplete="off")
        check = st.form_submit_button("Comprobar")
        panico = st.checkbox("No sé escribirlo / Ver solución")

        if check:
            if panico:
                st.info(f"Solución: **{row[col_sis]}**")
                st.session_state.fallos += 1
                actualizar_stats(familia_actual, False)
                if st.form_submit_button("Siguiente"): nueva_pregunta(); st.rerun()
            else:
                u_norm = normalizar_texto(user_input)
                c_norm = normalizar_texto(str(row[col_sis]))
                
                if u_norm == c_norm:
                    st.balloons()
                    st.success(f"¡CORRECTO! 🎉")
                    st.write(f"Exacto: **{row[col_sis]}**")
                    
                    st.session_state.aciertos += 1
                    actualizar_stats(familia_actual, True)
                    
                    msg = st.toast("Siguiente...", icon="✅")
                    time.sleep(1.5)
                    nueva_pregunta()
                    st.rerun()
                else:
                    st.error("Incorrecto")
                    st.write(f"Tú: {user_input}")
                    st.write(f"Solución: **{row[col_sis]}**")
                    
                    st.session_state.fallos += 1
                    actualizar_stats(familia_actual, False)
                    
                    if st.form_submit_button("Siguiente"):
                        nueva_pregunta()
                        st.rerun()