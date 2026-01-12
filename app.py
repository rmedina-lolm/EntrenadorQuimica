import streamlit as st
import pandas as pd
import random
import unicodedata
import time
import smtplib
import os
import streamlit.components.v1 as components # IMPORTANTE: Para el auto-foco
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

# Función JavaScript para poner el foco en el input
def enfocar_input():
    components.html("""
        <script>
            var input = window.parent.document.querySelector("input[type=text]");
            if (input) {
                input.focus();
            }
        </script>
    """, height=0)

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
        st.error(f"Error crítico al cargar CSV: {e}")
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
if 'examen_seleccion_unica' not in st.session_state: st.session_state.examen_seleccion_unica = None
if 'skips_used' not in st.session_state: st.session_state.skips_used = 0

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

def set_seleccion_unica(item_seleccionado):
    st.session_state.examen_seleccion_unica = item_seleccionado
    # Forzar desmarcado visual
    for item in todos_items:
        key = f"chk_{item}"
        if item != item_seleccionado:
            if key in st.session_state: st.session_state[key] = False
        else:
             st.session_state[key] = True

# --- INTERFAZ - CABECERA ---
if os.path.exists("image_0.png"):
    col_l, col_c, col_r = st.columns([2, 4, 2])
    with col_c:
        st.image("image_0.png", width=220) 

st.markdown("<h1 style='text-align: center; margin-top: -25px;'>🧪 Entrenador de Formulación</h1>", unsafe_allow_html=True)

# Mapeo de contenidos
cat_csv = df['COMPUESTO'].unique()
mapa = {}
col_1_items = ["Óxidos", "Hidruros", "Hidróxidos"]
col_2_items = ["Compuestos Binarios", "Sales Dobles", "Oxoácidos"]
col_3_items = ["Oxosales", "Sales Ácidas", "Oxosales Ácidas"]
todos_items = col_1_items + col_2_items + col_3_items

for deseada in todos_items:
    encontrado = False
    for real in cat_csv:
        if deseada.lower()[:4] in real.lower()[:4]: 
            mapa[deseada] = real
            encontrado = True
            break
    if not encontrado:
        mapa[deseada] = deseada

# ==========================================
#  CONFIGURACIÓN
# ==========================================
if st.session_state.estado_fase == 'configuracion':
    with st.container(border=True):
        st.markdown("<h3 style='text-align: center;'>⚙️ Configuración</h3>", unsafe_allow_html=True)
        
        # 1. TIPO DE PRUEBA
        c_izq, c_cen, c_der = st.columns([0.1, 9.8, 0.1])
        with c_cen:
            tipo_previo = st.session_state.get("tipo_previo", "Práctica")
            tipo_prueba = st.radio(
                "Tipo de prueba",
                ["Práctica", "Examen", "Examen (mezcla)"], 
                horizontal=True,
                label_visibility="collapsed"
            )
            if tipo_prueba != tipo_previo:
                st.session_state.examen_seleccion_unica = None
                st.session_state.tipo_previo = tipo_prueba
                for item in todos_items:
                    if f"chk_{item}" in st.session_state: del st.session_state[f"chk_{item}"]
                    if f"multi_{item}" in st.session_state: del st.session_state[f"multi_{item}"]
                st.rerun()

        # --- LOGICA CORREO (SOLO SI NO ES PRÁCTICA) ---
        es_examen = (tipo_prueba != "Práctica")
        email_ingresado = ""
        
        if es_examen:
            st.info("🔒 Acceso restringido: Se requiere correo institucional.")
            email_ingresado = st.text_input("Tu Correo (@fomento.edu):", placeholder="nombre@alumno.fomento.edu")
        else:
            st.success("🔓 Modo Práctica Libre (No requiere correo)")

        st.markdown("---")
        
        # 2. CONTENIDOS
        st.write("**Selecciona los contenidos:**")
        col_A, col_B, col_C = st.columns(3)
        seleccion_contenidos = []

        def render_smart_checkboxes(items, col):
            with col:
                for item in items:
                    if tipo_prueba == "Examen":
                        is_checked = st.session_state.get(f"chk_{item}", False)
                        st.checkbox(item, value=is_checked, key=f"chk_{item}", on_change=set_seleccion_unica, args=(item,))
                    else:
                        if st.checkbox(item, value=False, key=f"multi_{item}"):
                            seleccion_contenidos.append(item)

        render_smart_checkboxes(col_1_items, col_A)
        render_smart_checkboxes(col_2_items, col_B)
        render_smart_checkboxes(col_3_items, col_C)
        
        if tipo_prueba == "Examen" and st.session_state.examen_seleccion_unica:
             seleccion_contenidos = [st.session_state.examen_seleccion_unica]
        
        st.markdown("---")
        
        # 3. AJUSTES
        c_modo, c_nom, c_cant = st.columns(3)
        with c_modo:
            st.write("**Modo:**")
            modos = ["Nombrar", "Formular"]
            modos_activos = st.pills("Modo", options=modos, selection_mode="multi", default=modos, label_visibility="collapsed")
        with c_nom:
            st.write("**Nomenclaturas:**")
            sis_trad = st.checkbox("Tradicional", value=True)
            sis_stoc = st.checkbox("Stock", value=True)
            sis_sist = st.checkbox("Pref. Multiplicadores", value=True)
            
            sistemas_activos = []
            if sis_trad: sistemas_activos.append("Tradicional")
            if sis_stoc: sistemas_activos.append("Stock")
            if sis_sist: sistemas_activos.append("Pref. Multiplicadores")
            
        with c_cant:
            st.write("**Cantidad:**")
            if tipo_prueba in ["Examen", "Examen (mezcla)"]:
                limite_preguntas = 20
                st.text_input("Fijo", value="20 Preguntas", disabled=True, label_visibility="collapsed")
            else:
                opciones_cantidad = [5, 10, 15, 20, "∞"]
                limite_preguntas = st.selectbox("Cant.", options=opciones_cantidad, index=1, label_visibility="collapsed")

        st.markdown("<br>", unsafe_allow_html=True)
        
        # BOTÓN DE INICIO
        if st.button("🚀 COMENZAR", type="primary", use_container_width=True):
            errores = []
            
            # --- VALIDACIÓN DE CORREO CONDICIONAL ---
            if es_examen:
                if not email_ingresado:
                    errores.append("⚠️ Introduce tu correo electrónico para el Examen.")
                else:
                    dominio_valido = email_ingresado.strip().endswith("@alumno.fomento.edu") or \
                                     email_ingresado.strip().endswith("@fomento.edu")
                    if not dominio_valido:
                        errores.append("⛔ Acceso denegado: El correo debe ser de @fomento.edu o @alumno.fomento.edu")
            # ----------------------------------------

            if not seleccion_contenidos:
                errores.append("⚠️ Selecciona al menos un contenido.")
            if not modos_activos:
                errores.append("⚠️ Selecciona un modo (Nombrar/Formular).")
            if not sistemas_activos:
                errores.append("⚠️ Selecciona una nomenclatura.")
            
            if errores:
                for e in errores: st.error(e)
            else:
                st.session_state.config_actual = {
                    "tipo": tipo_prueba,
                    "contenidos": seleccion_contenidos,
                    "modos": modos_activos,
                    "sistemas": sistemas_activos,
                    "limite": limite_preguntas,
                    "email_alumno": email_ingresado if es_examen else "Practica_Libre"
                }
                st.session_state.aciertos = 0
                st.session_state.fallos = 0
                st.session_state.skips_used = 0
                st.session_state.stats_familia = {}
                st.session_state.contador_preguntas = 0
                st.session_state.estado_fase = 'respondiendo'
                st.rerun()

# ==========================================
#  JUEGO
# ==========================================
else:
    config = st.session_state.config_actual
    filtros_csv = [mapa.get(x, x) for x in config["contenidos"]]
    df_juego = df[df['COMPUESTO'].isin(filtros_csv)]
    
    if df_juego.empty:
        st.error("No se encontraron preguntas. Revisa CSV.")
        if st.button("Volver"):
            st.session_state.estado_fase = 'configuracion'
            st.rerun()
        st.stop()

    mapa_sistemas = {
        "Tradicional": "Nomenclatura Tradicional",
        "Stock": "Nomenclatura de Stock",
        "Pref. Multiplicadores": "Nomenclatura Sistemática"
    }
    
    modos_logica = []
    if "Nombrar" in config["modos"]: modos_logica.append("Nombrar (Fórmula ➡️ Nombre)")
    if "Formular" in config["modos"]: modos_logica.append("Formular (Nombre ➡️ Fórmula)")

    # BARRA SUPERIOR
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

    # FINAL JUEGO
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
        
        if config["tipo"] in ["Examen", "Examen (mezcla)"]:
            desglose = mostrar_tabla_progreso(return_string=True)
            with st.spinner("Enviando notas..."):
                ok = enviar_correo_resultados(config["email_alumno"], porcentaje, aciertos, total_actual, desglose)
                if ok: st.success("✅ Correo enviado al profesor.")
                else: st.error("❌ Error al enviar correo.")

        if st.button("🔄 Nuevo", type="primary"):
            st.session_state.estado_fase = 'configuracion'
            st.rerun()
        st.stop()

    # PREGUNTA
    def nueva_pregunta():
        try:
            familias = df_juego['COMPUESTO'].unique()
            fam = random.choice(familias)
            row = df_juego[df_juego['COMPUESTO'] == fam].sample(1).iloc[0]
            
            cols_deseadas = [mapa_sistemas[s] for s in config["sistemas"]]
            posibles = []
            
            check_list = []
            if "Nomenclatura Tradicional" in cols_deseadas: check_list.append(('Nomenclatura Tradicional', 'Tradicional'))
            if "Nomenclatura de Stock" in cols_deseadas: check_list.append(('Nomenclatura de Stock', 'Stock'))
            if "Nomenclatura Sistemática" in cols_deseadas: check_list.append(('Nomenclatura Sistemática', 'Pref. Multiplicadores'))

            for col, disp in check_list:
                if pd.notna(row[col]) and len(str(row[col]).strip()) > 1:
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
            skips_left = 3 - st.session_state.skips_used
            if st.button(f"⏭️ ({skips_left})", disabled=(skips_left <= 0), use_container_width=True, help="Saltar pregunta (Máx 3)"): 
                st.session_state.skips_used += 1
                nueva_pregunta()
                st.rerun()
            
        with c1:
            q_text = row[col_s] if "Formular" in modo else row['Fórmula']
            sub = f"Escribe la fórmula ({nom_s})" if "Formular" in modo else f"Nombra ({nom_s})"
            st.markdown(f"<div class='question-box'><div class='sub-info'>{sub}</div><div class='big-text'>{q_text}</div></div>", unsafe_allow_html=True)

        with st.form("f"):
            user = st.text_input("Respuesta:", key=k, autocomplete="off")
            # --- AUTOFOCO INYECTADO AQUÍ ---
            enfocar_input()
            # -------------------------------
            
            if st.form_submit_button("Comprobar"):
                raw = user.strip()
                target = str(row['Fórmula'] if "Formular" in modo else row[col_s]).strip()
                
                ok = False
                if "Formular" in modo:
                    ok = (limpiar_subindices(raw) == limpiar_subindices(target)) or (raw == target)
                else:
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