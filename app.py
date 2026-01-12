import streamlit as st
import pandas as pd
import random
import unicodedata
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ==========================================
# 📧 CONFIGURACIÓN DEL CORREO (EDITAR AQUÍ)
# ==========================================
EMAIL_ORIGEN = "tu_correo@gmail.com"  
PASSWORD_ORIGEN = "xxxx xxxx xxxx xxxx" 
EMAIL_DESTINO_PROFE = "tu_correo@gmail.com"
# ==========================================

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Evaluador de Formulación",
    page_icon="⚗️",
    layout="centered"
)

# --- ESTILOS CSS ---
st.markdown("""
    <style>
    .stApp header {visibility: hidden;} 
    div[data-testid="stPills"] {margin-bottom: 10px;}
    
    /* Ajuste para centrar elementos */
    .centered-radio {
        display: flex;
        justify_content: center;
        margin-bottom: 20px;
    }

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
    
    .sub-info { color: #555; font-size: 16px; margin-top: 5px; }
    
    /* Resultados */
    .resultado-box {
        padding: 30px;
        border-radius: 15px;
        background-color: #f0fdf4;
        border: 2px solid #bbf7d0;
        text-align: center;
        margin-bottom: 20px;
    }
    .nota-final { font-size: 50px; font-weight: bold; color: #15803d; }
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

# --- FUNCIONES AUXILIARES ---
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

def enviar_correo_resultados(alumno_email, nota_final, aciertos, total, desglose):
    asunto = f"Notas Formulación - {alumno_email}"
    cuerpo = f"""
    Hola,
    El alumno {alumno_email} ha finalizado.
    NOTA: {int(nota_final)} / 100
    Aciertos: {aciertos}/{total}
    
    Desglose:
    {desglose}
    """
    msg = MIMEMultipart()
    msg['From'] = EMAIL_ORIGEN
    msg['To'] = EMAIL_DESTINO_PROFE
    msg['Subject'] = asunto
    msg.attach(MIMEText(cuerpo, 'plain'))
    
    try:
        if "xxxx" in PASSWORD_ORIGEN: return False
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_ORIGEN, PASSWORD_ORIGEN)
        server.sendmail(EMAIL_ORIGEN, EMAIL_DESTINO_PROFE, msg.as_string())
        server.quit()
        return True
    except: return False

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

# --- GESTIÓN DE ESTADO ---
if 'aciertos' not in st.session_state: st.session_state.aciertos = 0
if 'fallos' not in st.session_state: st.session_state.fallos = 0
if 'stats_familia' not in st.session_state: st.session_state.stats_familia = {} 
if 'contador_preguntas' not in st.session_state: st.session_state.contador_preguntas = 0
if 'estado_fase' not in st.session_state: st.session_state.estado_fase = 'configuracion' 
if 'datos_fallo' not in st.session_state: st.session_state.datos_fallo = {}
if 'config_prev' not in st.session_state: st.session_state.config_prev = ""

def actualizar_stats(familia, es_acierto):
    if familia not in st.session_state.stats_familia:
        st.session_state.stats_familia[familia] = {'aciertos': 0, 'total': 0}
    st.session_state.stats_familia[familia]['total'] += 1
    if es_acierto:
        st.session_state.stats_familia[familia]['aciertos'] += 1

def mostrar_tabla_progreso(return_string=False):
    if st.session_state.stats_familia:
        datos_tabla = []
        texto_email = ""
        for fam, datos in st.session_state.stats_familia.items():
            fallos_fam = datos['total'] - datos['aciertos']
            datos_tabla.append({"Compuesto": fam, "✅ Aciertos": datos['aciertos'], "❌ Fallos": fallos_fam})
            texto_email += f"- {fam}: {datos['aciertos']} aciertos, {fallos_fam} fallos.\n"
        
        if return_string: return texto_email
        st.markdown("---")
        st.caption("📊 Estadísticas en tiempo real:")
        st.dataframe(pd.DataFrame(datos_tabla), hide_index=True, use_container_width=True)
    return ""

# --- INTERFAZ PRINCIPAL ---
st.title("🧪 Entrenador de Formulación")

# INSERTAR ESCUDO DEBAJO DEL TÍTULO
try:
    st.image("image_0.png", width=100)
except FileNotFoundError:
    st.error("El archivo de imagen 'image_0.png' no se encontró. Asegúrate de que esté en el mismo directorio.")

# Mapeo de contenidos CSV vs Visualización
cat_csv = df['COMPUESTO'].unique()
mapa = {}
# Definimos las columnas visuales solicitadas
col_1_items = ["Óxidos", "Hidruros", "Hidróxidos"]
col_2_items = ["Compuestos Binarios", "Sales Dobles", "Oxoácidos"]
col_3_items = ["Oxosales", "Sales Ácidas", "Oxosales Ácidas"]
todos_items = col_1_items + col_2_items + col_3_items

# Lógica de mapeo (busca coincidencias en el CSV)
for deseada in todos_items:
    encontrado = False
    for real in cat_csv:
        if deseada.lower()[:4] in real.lower()[:4]: 
            mapa[deseada] = real
            encontrado = True
            break
    if not encontrado:
        mapa[deseada] = deseada # Fallback por si no encuentra

# ==========================================
#  CONFIGURACIÓN Y SELECCIÓN
# ==========================================
if st.session_state.estado_fase == 'configuracion':
    with st.container(border=True):
        st.markdown("<h3 style='text-align: center;'>⚙️ Configuración</h3>", unsafe_allow_html=True)
        
        # 1. TIPO DE PRUEBA (CENTRADO)
        c_izq, c_cen, c_der = st.columns([1, 2, 1])
        with c_cen:
            tipo_prueba = st.radio(
                "Tipo de prueba",
                ["Práctica", "Examen Mezclado", "Examen"],
                horizontal=True,
                label_visibility="collapsed"
            )

        # Email si es examen
        pedir_email = (tipo_prueba in ["Examen", "Examen Mezclado"])
        email_ingresado = ""
        if pedir_email:
            st.info("🔒 Modo Examen: Se requiere correo.")
            email_ingresado = st.text_input("Tu Correo:", placeholder="alumno@ejemplo.com")

        st.markdown("---")
        
        # 2. CONTENIDOS (3 COLUMNAS ESPECÍFICAS)
        st.write("**Selecciona los contenidos:**")
        
        col_A, col_B, col_C = st.columns(3)
        seleccion_contenidos = []

        # Función para pintar checkboxes y guardar selección
        def render_checkboxes(items, col):
            with col:
                for item in items:
                    # value=False asegura que no haya nada marcado por defecto
                    if st.checkbox(item, value=False):
                        seleccion_contenidos.append(item)

        render_checkboxes(col_1_items, col_A)
        render_checkboxes(col_2_items, col_B)
        render_checkboxes(col_3_items, col_C)
        
        st.markdown("---")
        
        # 3. AJUSTES TÉCNICOS
        c_modo, c_nom, c_cant = st.columns(3)
        
        with c_modo:
            st.write("**Modo:**")
            modos = ["Nombrar", "Formular"]
            modos_activos = st.pills("Modo", options=modos, selection_mode="multi", default=modos, label_visibility="collapsed")
            
        with c_nom:
            st.write("**Nomenclaturas:**")
            # Tres botones (checkboxes) uno encima del otro
            sis_trad = st.checkbox("Tradicional", value=True)
            sis_stoc = st.checkbox("Stock", value=True)
            sis_sist = st.checkbox("Sistemática", value=True)
            
            sistemas_activos = []
            if sis_trad: sistemas_activos.append("Tradicional")
            if sis_stoc: sistemas_activos.append("Stock")
            if sis_sist: sistemas_activos.append("Sistemática")
            
        with c_cant:
            st.write("**Cantidad:**")
            if tipo_prueba in ["Examen", "Examen Mezclado"]:
                limite_preguntas = 20
                st.text_input("Fijo", value="20 Preguntas", disabled=True, label_visibility="collapsed")
            else:
                opciones_cantidad = [5, 10, 15, 20, "∞"]
                limite_preguntas = st.selectbox("Cant.", options=opciones_cantidad, index=1, label_visibility="collapsed")

        st.markdown("<br>", unsafe_allow_html=True)
        
        # BOTÓN DE INICIO
        if st.button("🚀 COMENZAR", type="primary", use_container_width=True):
            # VALIDACIONES
            errores = []
            if pedir_email and not email_ingresado:
                errores.append("⚠️ Introduce tu correo electrónico.")
            if not seleccion_contenidos:
                errores.append("⚠️ Selecciona al menos un contenido.")
            if not modos_activos:
                errores.append("⚠️ Selecciona un modo (Nombrar/Formular).")
            if not sistemas_activos:
                errores.append("⚠️ Selecciona una nomenclatura.")
            if tipo_prueba == "Examen" and len(seleccion_contenidos) > 1:
                errores.append("⚠️ En 'Examen' solo puedes elegir 1 tema. Usa 'Examen Mezclado' para más.")
            
            if errores:
                for e in errores: st.error(e)
            else:
                # Guardar configuración y arrancar
                st.session_state.config_actual = {
                    "tipo": tipo_prueba,
                    "contenidos": seleccion_contenidos,
                    "modos": modos_activos,
                    "sistemas": sistemas_activos,
                    "limite": limite_preguntas,
                    "email_alumno": email_ingresado
                }
                reiniciar_todo()
                st.session_state.estado_fase = 'respondiendo'
                st.rerun()

# ==========================================
#  JUEGO
# ==========================================
else:
    config = st.session_state.config_actual
    filtros_csv = [mapa.get(x, x) for x in config["contenidos"]] # .get seguro
    df_juego = df[df['COMPUESTO'].isin(filtros_csv)]
    
    # Si por algún motivo el filtrado deja vacío el DF (ej. nombres no coinciden)
    if df_juego.empty:
        st.error("No se encontraron preguntas para los temas seleccionados. Revisa el archivo CSV.")
        if st.button("Volver"):
            st.session_state.estado_fase = 'configuracion'
            st.rerun()
        st.stop()

    mapa_sistemas = {
        "Tradicional": "Nomenclatura Tradicional",
        "Stock": "Nomenclatura de Stock",
        "Sistemática": "Nomenclatura Sistemática"
    }
    
    modos_logica = []
    if "Nombrar" in config["modos"]: modos_logica.append("Nombrar (Fórmula ➡️ Nombre)")
    if "Formular" in config["modos"]: modos_logica.append("Formular (Nombre ➡️ Fórmula)")

    # --- BARRA SUPERIOR ---
    aciertos = st.session_state.aciertos
    fallos = st.session_state.fallos
    total_actual = aciertos + fallos
    limit_val = 999999 if config["limite"] == "∞" else config["limite"]
    
    c_p, c_b = st.columns([4, 1])
    with c_p:
        if config["limite"] != "∞":
            st.progress(min(total_actual / limit_val, 1.0))
            st.caption(f"{config['tipo']} | {total_actual + 1}/{limit_val}")
        else:
            st.caption(f"{config['tipo']} ∞ | Llevas {total_actual}")
    with c_b:
        if st.button("❌ Salir", use_container_width=True):
            st.session_state.estado_fase = 'configuracion'
            st.rerun()

    # --- FINAL DEL JUEGO ---
    if total_actual >= limit_val and st.session_state.estado_fase == 'respondiendo':
        st.balloons()
        porcentaje = (aciertos / total_actual * 100) if total_actual > 0 else 0
        
        st.markdown(f"""
        <div class='resultado-box'>
            <h2>🏁 Finalizado</h2>
            <div class='nota-final'>{int(porcentaje)}%</div>
            <p>Aciertos: <b>{aciertos}</b> / {total_actual}</p>
        </div>
        """, unsafe_allow_html=True)
        
        mostrar_tabla_progreso()
        
        if config["tipo"] in ["Examen", "Examen Mezclado"]:
            desglose = mostrar_tabla_progreso(return_string=True)
            with st.spinner("Enviando notas..."):
                ok = enviar_correo_resultados(config["email_alumno"], porcentaje, aciertos, total_actual, desglose)
                if ok: st.success("✅ Correo enviado al profesor.")
                else: st.error("❌ No se pudo enviar el correo (Revisa configuración).")

        if st.button("🔄 Nuevo", type="primary"):
            st.session_state.estado_fase = 'configuracion'
            st.rerun()
        st.stop()

    # --- LÓGICA PREGUNTA ---
    def nueva_pregunta():
        try:
            familias = df_juego['COMPUESTO'].unique()
            fam = random.choice(familias)
            row = df_juego[df_juego['COMPUESTO'] == fam].sample(1).iloc[0]
            
            cols_deseadas = [mapa_sistemas[s] for s in config["sistemas"]]
            posibles = []
            for col, disp in [('Nomenclatura Tradicional','Tradicional'), ('Nomenclatura de Stock','Stock'), ('Nomenclatura Sistemática','Sistemática')]:
                if col in cols_deseadas and pd.notna(row[col]) and len(str(row[col]).strip()) > 1:
                    posibles.append((col, disp))
            
            if not posibles:
                nueva_pregunta()
                return

            st.session_state.pregunta = row
            st.session_state.modo = random.choice(modos_logica)
            st.session_state.sis_elegido = random.choice(posibles)
            st.session_state.contador_preguntas += 1
            st.session_state.estado_fase = 'respondiendo'
        except:
            nueva_pregunta()

    if 'pregunta' not in st.session_state: nueva_pregunta(); st.rerun()

    # --- PANTALLA JUEGO ---
    if st.session_state.estado_fase == 'mostrar_fallo':
        d = st.session_state.datos_fallo
        st.subheader("❌ Incorrecto")
        st.markdown(f"<div class='question-box'><div class='big-text'>{d['pregunta']}</div></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='fail-box'><p>Tu respuesta: {d['usuario']}</p><hr><p>Correcta: <b>{d['solucion']}</b></p></div>", unsafe_allow_html=True)
        if st.button("➡️ Siguiente", type="primary"):
            nueva_pregunta()
            st.rerun()
    else:
        row = st.session_state.pregunta
        fam = row['COMPUESTO']
        modo = st.session_state.modo
        col_s, nom_s = st.session_state.sis_elegido
        k = f"r_{st.session_state.contador_preguntas}"

        c1, c2 = st.columns([4, 1])
        with c2: 
            if st.button("⏭️"): nueva_pregunta(); st.rerun()
            
        with c1:
            q_text = row[col_s] if "Formular" in modo else row['Fórmula']
            sub = f"Escribe la fórmula ({nom_s})" if "Formular" in modo else f"Nombra ({nom_s})"
            st.markdown(f"<div class='question-box'><div class='sub-info'>{sub}</div><div class='big-text'>{q_text}</div></div>", unsafe_allow_html=True)

        with st.form("f"):
            user = st.text_input("Respuesta:", key=k, autocomplete="off")
            if st.form_submit_button("Comprobar"):
                raw = user.strip()
                target = str(row['Fórmula'] if "Formular" in modo else row[col_s]).strip()
                
                # Normalización simple
                ok = False
                if "Formular" in modo:
                    # Comparar fórmulas (limpiar subíndices visuales por si acaso)
                    ok = (limpiar_subindices(raw) == limpiar_subindices(target)) or (raw == target)
                else:
                    # Comparar nombres (normalizar tildes)
                    ok = normalizar_texto(raw) == normalizar_texto(target)

                if ok:
                    st.toast("✅ Correcto")
                    st.session_state.aciertos += 1
                    actualizar_stats(fam, True)
                    time.sleep(0.5)
                    nueva_pregunta()
                    st.rerun()
                else:
                    st.session_state.fallos += 1
                    actualizar_stats(fam, False)
                    st.session_state.datos_fallo = {"pregunta": q_text, "usuario": user, "solucion": target}
                    st.session_state.estado_fase = 'mostrar_fallo'
                    st.rerun()

    mostrar_tabla_progreso()