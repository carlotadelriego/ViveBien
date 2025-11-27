# -----------------------------------------------
#  VIVEBIEN — Plataforma de Bienestar Multimodal
#  Archivo completo corregido: navegación 1-clic, accesibilidad segura,
#  fondo sólo en Inicio (sin overlays), y caritas clicables en Resumen.
# python -m streamlit run vivebien_main.py
# -----------------------------------------------

import streamlit as st
import tempfile, os, subprocess, shutil, time
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import base64

ASSETS_DIR = os.path.join(os.getcwd(), "assets")

# módulos del proyecto (asegúrate de tenerlos en la misma carpeta)
from data_simulation import generate_history, simulate_biometrics
from feedback_engine import analyze_text_sentiment, generate_recommendation
import database

st.set_page_config(page_title="ViveBien", page_icon="🌿", layout="centered")
AURA_NAME = "Aura"

# ---------- TTS (pyttsx3 o 'say') ----------
try:
    import pyttsx3
    _has_pyttsx3 = True
except Exception:
    _has_pyttsx3 = False

def shutil_which(cmd):
    from shutil import which
    return which(cmd)

def tts_say(text: str, filename: str):
    """
    Intenta generar audio con pyttsx3 o con 'say' en macOS.
    Devuelve la ruta al archivo si se generó, o None.
    """
    try:
        if _has_pyttsx3:
            engine = pyttsx3.init()
            engine.setProperty('rate', 160)
            engine.setProperty('volume', 0.9)
            engine.save_to_file(text, filename)
            engine.runAndWait()
            return filename
        else:
            if os.name == "posix" and shutil_which("say"):
                aiff = filename if filename.lower().endswith(".aiff") else filename + ".aiff"
                subprocess.run(["say", "-o", aiff, text], check=True)
                return aiff
    except Exception:
        return None
    return None

# -----------------------------
# DB init
# -----------------------------
database.init_db()

# -----------------------------
# session_state inicial (IMPORTANTE: inicializar antes de usar current_user)
# -----------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "last_recommendation" not in st.session_state:
    st.session_state.last_recommendation = ""
if "menu" not in st.session_state:
    st.session_state.menu = "Inicio"
if "show_register" not in st.session_state:
    st.session_state.show_register = False
# accesibilidad: valores por defecto (se pueden cargar desde DB al iniciar sesión)
if "accesibilidad" not in st.session_state:
    st.session_state.accesibilidad = {
        "font_size": "Normal",
        "dark_mode": False,
        "tts_enabled": True,
        "high_contrast": False
    }

# helper para gráficos y datos
def plot_biometrics_df(df: pd.DataFrame):
    fig, ax = plt.subplots(3,1, figsize=(6,8), constrained_layout=True)
    if not df.empty:
        if 'steps' in df: df['steps'].plot(ax=ax[0], title='Pasos (histórico)', marker='o')
        if 'sleep_hours' in df: df['sleep_hours'].plot(ax=ax[1], title='Sueño (horas)', marker='o')
        if 'heart_rate' in df: df['heart_rate'].plot(ax=ax[2], title='Frecuencia cardiaca (bpm)', marker='o')
    else:
        ax[0].text(0.5,0.5,"No hay datos", ha='center')
    for a in ax: a.grid(alpha=0.4)
    return fig

def biometrics_rows_to_df(rows):
    if not rows:
        return pd.DataFrame(columns=['steps','sleep_hours','heart_rate'])
    df = pd.DataFrame(rows, columns=['date','steps','sleep_hours','heart_rate'])
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    return df

# -----------------------------
# APLICACIÓN GLOBAL DE ACCESIBILIDAD (después de inicializar session_state)
# -----------------------------
# fijar un tamaño base y mantener jerarquía de títulos
size_map = {"Pequeño": "14px", "Normal": "18px", "Grande": "22px"}
base_font = size_map.get(st.session_state.accesibilidad.get("font_size", "Normal"), "18px")

st.markdown(f"""
    <style>
        /* Solo texto normal y controles (no tocamos directamente h1/h2/h3) */
        body, p, li, .stTextInput, .stTextArea, .stSlider, .stButton>button, .stSelectbox, .stMarkdown {{
            font-size: {base_font} !important;
        }}

        /* Mantener jerarquía de títulos en proporción al base_font */
        h1, .stMarkdown h1 {{ font-size: calc({base_font} * 2.0) !important; }}
        h2, .stMarkdown h2 {{ font-size: calc({base_font} * 1.6) !important; }}
        h3, .stMarkdown h3 {{ font-size: calc({base_font} * 1.3) !important; }}
    </style>
""", unsafe_allow_html=True)

# Modo oscuro y contraste alto: aplicar cambios seguros
if st.session_state.accesibilidad.get("dark_mode", False):
    st.markdown("""
        <style>
            [data-testid="stAppViewContainer"] { background-color: #0f0f0f !important; color: #eaeaea !important; }
            [data-testid="stSidebar"] > div:first-child { background-color: rgba(20,20,20,0.95) !important; color: #eaeaea !important; }
            .stButton>button { color: inherit; }
        </style>
    """, unsafe_allow_html=True)

if st.session_state.accesibilidad.get("high_contrast", False):
    st.markdown("""
        <style>
            [data-testid="stAppViewContainer"] { background-color: #000 !important; color: #FFD700 !important; }
            a, .stButton>button { color: #FFD700 !important; font-weight:700; }
        </style>
    """, unsafe_allow_html=True)

# -----------------------------
# GLOBAL STYLE (limpio y seguro)
# -----------------------------
GLOBAL_STYLE = """
<style>
/* Estilos visuales seguros (evitamos .main y position:absolute) */

.login-logo { width: 140px; margin-bottom: 6px; }
.login-title { font-size: 26px; font-weight: 600; margin-bottom: 18px; }
.login-label { font-weight: 600; text-align: left; margin: 0; margin-top: 10px; font-size: 15px; }
.login-input { width: 100%; padding: 12px; border-radius: 10px; border: 1px solid #ccc; margin-top: 6px; font-size: 15px; }
.btn-login { background: #dff3e6; border: none; width: 100%; padding: 12px; border-radius: 10px; margin-top: 18px; font-size: 17px; font-weight: 600; cursor: pointer; }
.divider { margin-top: 14px; color: #666; font-weight: 600; }
.social-row { display:flex; gap: 10px; margin-top: 12px; }
.social-btn { flex: 1; padding: 12px; border-radius: 10px; border: none; font-weight: 600; font-size: 15px; cursor: pointer; }
.google { background: #4285F4 !important; color: white !important; }
.apple  { background: #FF6B6B !important; color: white !important; }
.bottom-links { display:flex; justify-content:space-between; margin-top: 12px; font-size: 14px; font-weight: 600; }
.link { cursor: pointer; color: #222; }

.chat-card { max-width: 650px; margin: 20px auto; padding: 18px; border-radius: 22px; border: 8px solid #e6e6e6; background: white; }
.msg-user { background:#fff; padding:10px 14px; border-radius:12px; border:2px solid #ddd; width:fit-content; margin:8px 0; }
.msg-aura { background:#e0f6d9; padding:10px 14px; border-radius:12px; border:2px solid #c4e8c1; width:fit-content; margin:8px 0; margin-left:auto; }

.rutina-card { background:white; padding:14px; border-radius:14px; margin-bottom:12px; display:flex; border:1px solid #f0f0f0; box-shadow:0 2px 6px rgba(0,0,0,0.04); align-items:center; }
.rutina-img { width:84px; height:84px; border-radius:12px; object-fit:cover; margin-right:12px; }

.inicio-container { max-width: 900px; margin: 0 auto; padding: 24px; background: rgba(255,255,255,0.95); border-radius: 18px; box-shadow: 0 6px 18px rgba(0,0,0,0.04); }
.mood-face { cursor: pointer; opacity: 0.6; transition: all 0.12s ease-in-out; }
.mood-face.selected { opacity: 1; transform: scale(1.05); box-shadow: 0 6px 14px rgba(0,0,0,0.08); border-radius:12px; }

</style>
"""
st.markdown(GLOBAL_STYLE, unsafe_allow_html=True)

st.markdown("""
<style>

.mood-wrapper { 
    text-align: center;
    height: 120px; /* área fija para alinear imagen y botón */
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
}

.mood-face {
    cursor: pointer;
    opacity: 0.55;
    transition: all 0.20s ease-in-out;
    border-radius: 8px;
    width: 75px;
    height: 75px;
    object-fit: contain;
    display: block;
}

.mood-face:hover {
    opacity: 0.9;
    transform: scale(1.07);
}

.mood-face.selected {
    opacity: 1 !important;
    transform: scale(1.12);
    box-shadow: 0 8px 18px rgba(0,0,0,0.18);
    border-radius: 16px;
}

.mood-btn {
    margin-top: 8px;
}

</style>
""", unsafe_allow_html=True)



# -----------------------------
# RENDER LOGIN (centrado, seguro)
# -----------------------------
def render_login_screen():
    if os.path.exists(os.path.join(ASSETS_DIR, "logo.png")):
        st.image(os.path.join(ASSETS_DIR, "logo.png"), width=140)
    else:
        st.markdown("<div style='width:140px;height:140px;border-radius:50%;background:#eaf6ec;margin:0 auto 6px;display:flex;align-items:center;justify-content:center;font-size:40px;'>🧘</div>", unsafe_allow_html=True)

    st.markdown("<div class='login-title'>ViveBien</div>", unsafe_allow_html=True)

    st.markdown("<div class='login-label'>Email</div>", unsafe_allow_html=True)
    email = st.text_input("email_input", placeholder="nombre@ejemplo.com", label_visibility="collapsed")

    st.markdown("<div class='login-label'>Contraseña</div>", unsafe_allow_html=True)
    password = st.text_input("pass_input", placeholder="••••••••••", type="password", label_visibility="collapsed")

    if st.button("Acceder", use_container_width=True):
        if not email or not password:
            st.warning("Completa los campos.")
        else:
            ok, msg, user_info = database.login_user(email.strip(), password)
            if ok:
                # cargar preferencias desde DB si existen
                st.session_state.logged_in = True
                st.session_state.user = user_info
                # si la BD contiene preferencias de accesibilidad, las cargamos
                if user_info:
                    # merge de accesibilidad sin perder claves
                    prefs = {
                        "font_size": user_info.get("font_size", st.session_state.accesibilidad["font_size"]),
                        "dark_mode": user_info.get("dark_mode", st.session_state.accesibilidad["dark_mode"]),
                        "tts_enabled": user_info.get("tts_enabled", st.session_state.accesibilidad["tts_enabled"]),
                        "high_contrast": user_info.get("high_contrast", st.session_state.accesibilidad["high_contrast"])
                    }
                    st.session_state.accesibilidad.update(prefs)
                st.session_state.menu = "Inicio"
                st.session_state.chat_history = []
                st.rerun()
            else:
                st.error(msg)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<div class='link'>¿Olvidaste tu contraseña?</div>", unsafe_allow_html=True)
    with col2:
        if st.button("¡Únete a nosotros!"):
            st.session_state.show_register = True
            st.rerun()

    st.markdown("<div class='divider'>o continúa con</div>", unsafe_allow_html=True)

    colg, cola = st.columns(2)
    with colg:
        st.button("Google", use_container_width=True)
    with cola:
        st.button("Apple ID", use_container_width=True)

    st.markdown("</div></div>", unsafe_allow_html=True)

# -----------------------------
# RENDER REGISTER
# -----------------------------
def render_register_screen():
    st.header("Crear cuenta")

    name_reg = st.text_input("Nombre", key="reg_name_ui")
    email_reg = st.text_input("Email", key="reg_email_ui")
    pass_reg = st.text_input("Contraseña", type="password", key="reg_pass_ui")
    pass_reg_confirm = st.text_input("Repite contraseña", type="password", key="reg_pass2_ui")

    if st.button("Crear cuenta", key="btn_create_account"):
        if not (name_reg and email_reg and pass_reg):
            st.error("Completa todos los campos.")
        elif pass_reg != pass_reg_confirm:
            st.error("Las contraseñas no coinciden.")
        else:
            ok, msg = database.register_user(name_reg.strip(), email_reg.strip(), pass_reg)
            if ok:
                ok2, msg2, user_info = database.login_user(email_reg.strip(), pass_reg)
                if ok2:
                    st.session_state.user = user_info
                    st.session_state.logged_in = True
                    st.session_state.menu = "Inicio"
                    # generar datos iniciales de ejemplo
                    hist = generate_history(days=14)
                    for idx, row in hist.iterrows():
                        database.save_biometrics(
                            user_info["user_id"],
                            {"steps": int(row.steps),
                             "sleep_hours": float(row.sleep_hours),
                             "heart_rate": int(row.heart_rate)},
                            date_iso=idx.date().isoformat()
                        )
                    st.success("Cuenta creada. ¡Bienvenid@!")
                    st.rerun()
                else:
                    st.warning("Cuenta creada pero no se pudo iniciar sesión.")
            else:
                st.error(msg)

    if st.button("Volver al login", key="btn_back"):
        st.session_state.show_register = False
        st.rerun()

    st.markdown("</div></div>", unsafe_allow_html=True)

# -----------------------------
# MAIN: mostrar login o registro si no logueado
# -----------------------------
if not st.session_state.logged_in:
    if st.session_state.show_register:
        render_register_screen()
        st.stop()
    else:
        render_login_screen()
        st.stop()

# -----------------------------
# Sidebar (aparece solo después de login) — navegación 1-clic con on_change
# -----------------------------
def _update_menu():
    st.session_state.menu = st.session_state._menu_radio

with st.sidebar:
    st.title("ViveBien 🌿")
    if st.session_state.user:
        st.write(f"Hola, {st.session_state.user.get('name','')}")

    st.markdown("---")
    # radio con key y on_change para evitar rebotes y requerir 2 clics
    options = ["Inicio","Resumen","Registro de Estado","Chat con Aura","Rutinas","Perfil"]
    default_index = options.index(st.session_state.menu) if st.session_state.menu in options else 0
    st.radio("Navegación", options, index=default_index, key="_menu_radio", on_change=_update_menu)

    if st.button("Cerrar sesión"):
        st.session_state.logged_in = False
        st.session_state.user = None
        st.session_state.chat_history = []
        st.session_state.menu = "Inicio"
        st.rerun()

# actualizar variables locales después del sidebar
current_user = st.session_state.user
user_id = current_user["user_id"] if current_user else None
menu = st.session_state.menu

# -----------------------------
# Fondo seguro (solo en Inicio) -> carga segura sin overlays ni z-index negativos
# -----------------------------
def load_background_safe(image_path):
    if not os.path.exists(image_path):
        return
    with open(image_path, "rb") as image_file:
        encoded = base64.b64encode(image_file.read()).decode()
    page_bg_img = f"""
    <style>
    /* background-image aplicado sin fixed ni overlays */
    [data-testid="stAppViewContainer"] {{
        background-image: url("data:image/png;base64,{encoded}");
        background-repeat: no-repeat;
        background-position: center top;
        background-size: cover;
        background-attachment: scroll;
    }}
    [data-testid="stSidebar"] > div:first-child {{
        background-color: rgba(255,255,255,0.92);
    }}
    .inicio-container {{
        position: relative;
        z-index: 1;
    }}
    </style>
    """
    st.markdown(page_bg_img, unsafe_allow_html=True)

# -----------------------------
# PÁGINAS
# -----------------------------

# ----- INICIO -----
if menu == "Inicio":
    load_background_safe(os.path.join(ASSETS_DIR, "inicio.png"))
    name = current_user.get("name") if current_user else ""
    st.markdown(f"<h2 style='text-align:center;margin-bottom:6px;'>Bienvenid@, {name} 🌿</h2>", unsafe_allow_html=True)

    ### MAL ESTILO: contenedor centralizado con fondo blanco semitransparente
    st.markdown("<div style='text-align:center' class='inicio-subtitle'>Una plataforma inteligente que te acompaña a mejorar tu salud, tus hábitos y tu bienestar emocional.</div>", unsafe_allow_html=True)
    # linea separadora
    st.markdown("<hr style='margin-top:18px;margin-bottom:18px;border:none;border-top:1px solid #ccc;'/>", unsafe_allow_html=True)

    ## espacio entre título y contenido transparente
    st.markdown("<h2>Recomendación del día</h2>", unsafe_allow_html=True)
    if st.session_state.last_recommendation:
        st.markdown(f"<div class='reco-box'>{st.session_state.last_recommendation}</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='reco-box'>Aún no hay recomendaciones. Registra tu estado para que Aura pueda ayudarte.</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# ----- RESUMEN -----
elif menu == "Resumen":
    if user_id is None:
        st.error("Usuario no identificado. Vuelve a iniciar sesión.")
        st.stop()

    rows = database.load_biometrics(user_id)
    df = biometrics_rows_to_df(rows)

    st.image(os.path.join(ASSETS_DIR, "logo.png"), width=70)
    st.title("Resumen del día")

    if df.empty:
        st.warning("No hay datos registrados todavía.")
    else:
        latest = df.tail(1).iloc[0]

        st.markdown("---")
        col1, col2 = st.columns([4,1])
        with col1:
            st.subheader("Pasos")
            st.markdown(f"<h2>{int(latest.steps)}</h2>", unsafe_allow_html=True)
        with col2:
            icon_pasos = os.path.join(ASSETS_DIR, "icon_pasos.png")
            if os.path.exists(icon_pasos):
                st.image(icon_pasos, width=100)

        st.markdown("---")
        col1, col2 = st.columns([4,1])
        with col1:
            st.subheader("Sueño")
            st.markdown(f"<h2>{latest.sleep_hours} hs</h2>", unsafe_allow_html=True)
        with col2:
            icon_sueno = os.path.join(ASSETS_DIR, "icon_sueno.png")
            if os.path.exists(icon_sueno):
                st.image(icon_sueno, width=100)

        st.markdown("---")
        st.subheader("Estado de Ánimo")

        # ----- MOOD PICKER -----
        if "mood" not in st.session_state:
            st.session_state.mood = None

        mood_files = [
            ("m_1.png", "Muy mal", 1),
            ("m_2.png", "Mal", 2),
            ("m_3.png", "Normal", 3),
            ("m_4.png", "Bien", 4),
            ("m_5.png", "Muy bien", 5),
        ]

        cols = st.columns(5)

        for i, (file, label, value) in enumerate(mood_files):
            with cols[i]:

                icon_path = os.path.join(ASSETS_DIR, file)

                # Imagen centrada con animación y estilo
                if os.path.exists(icon_path):
                    encoded_img = base64.b64encode(open(icon_path, 'rb').read()).decode()
                    st.markdown(
                        f"""
                        <div class='mood-wrapper'>
                            <img src='data:image/png;base64,{encoded_img}' 
                                width='75' 
                                class='mood-face {"selected" if st.session_state.mood == value else ""}'>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        f"""
                        <div class="mood-wrapper" 
                                style="width:75px;height:75px;background:#eee;border-radius:16px;display:flex;align-items:center;justify-content:center;">
                            {label[0]}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                # BOTÓN centrado debajo — añadir pequeño espaciador para separarlo de la imagen
                # Ajusta `height` para aumentar/disminuir la separación (ej. 6px, 10px, 14px)
                st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
                btn_label = "Seleccionar" if st.session_state.mood != value else "✓ Seleccionado"

                if st.button(btn_label, key=f"mood_btn_{value}"):
                    st.session_state.mood = value

                    # GUARDADO EN BD
                    try:
                        database.save_mood_log(user_id, f"Estado: {label}", label, value)
                    except:
                        pass

                    # POPUP agradable
                    st.success(f"Estado registrado: {label}")

                    # OPCIONAL: sonido TTS del click
                    if current_user.get("tts_enabled", True):
                        try:
                            tts_say("Estado actualizado", tempfile.NamedTemporaryFile(delete=False).name)
                        except:
                            pass

                    st.rerun()



# ----- REGISTRO DE ESTADO -----
elif menu == "Registro de Estado":
    if user_id is None:
        st.error("Usuario no identificado. Vuelve a iniciar sesión.")
        st.stop()

    st.title("Registro de estado")
    mode = st.radio("Modo de entrada", ("Texto", "Subir audio"), key="reg_mode")
    user_text = ""
    if mode == "Texto":
        user_text = st.text_area("¿Cómo te sientes hoy?", key="reg_text")
    else:
        audio_file = st.file_uploader("Sube audio", type=["wav","mp3","m4a"])
        if audio_file:
            st.audio(audio_file)
            st.info("Transcribiendo audio...")
            try:
                import speech_recognition as sr
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tf:
                    tf.write(audio_file.read())
                r = sr.Recognizer()
                with sr.AudioFile(tf.name) as src:
                    audio = r.record(src)
                user_text = r.recognize_google(audio, language="es-ES")
                st.success("Transcripción: " + user_text)
            except Exception as e:
                st.warning(f"No se pudo transcribir: {e}")

    if st.button("Analizar y guardar"):
        if not user_text.strip():
            st.error("Escribe algo primero.")
        else:
            sent, score = analyze_text_sentiment(user_text)
            database.save_mood_log(user_id, user_text, sent, score)
            rows = database.load_biometrics(user_id)
            df = biometrics_rows_to_df(rows)
            if df.empty:
                sim = simulate_biometrics()
                database.save_biometrics(user_id, sim)
                latest = sim
            else:
                latest = df.tail(1).iloc[0].to_dict()
            reco = generate_recommendation(user_text, latest, current_user.get("target_steps",8000) if current_user else 8000)
            st.session_state.last_recommendation = reco
            st.info(reco)
            if current_user and current_user.get("tts_enabled", True):
                try:
                    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".aiff")
                    tmp.close()
                    ap = tts_say(reco, tmp.name)
                    if ap:
                        st.audio(ap)
                except:
                    pass

# ----- CHAT CON AURA -----
elif menu == "Chat con Aura":
    if user_id is None:
        st.error("Usuario no identificado. Vuelve a iniciar sesión.")
        st.stop()

    st.image(os.path.join(ASSETS_DIR, "logo.png"), width=65)
    st.title("Chatea con Aura")
    for role, text in st.session_state.chat_history:
        if role == "user":
            st.markdown(f"<div class='msg-user'>{text}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='msg-aura'>{text}</div>", unsafe_allow_html=True)

    col1, col2 = st.columns([4,1])
    with col1:
        user_msg = st.text_input(" ", placeholder="Escribe aquí…", key="chat_input_box", label_visibility="collapsed")
    with col2:
        st.markdown("<div style='font-size:24px;text-align:center;'>🎤</div>", unsafe_allow_html=True)

    if st.button("Enviar"):
        if user_msg.strip():
            st.session_state.chat_history.append(("user", user_msg))
            rows = database.load_biometrics(user_id)
            df = biometrics_rows_to_df(rows)
            latest = df.tail(1).iloc[0].to_dict() if not df.empty else simulate_biometrics()
            reply = generate_recommendation(user_msg, latest, current_user.get("target_steps",8000) if current_user else 8000)
            st.session_state.chat_history.append(("aura", reply))
            sent, score = analyze_text_sentiment(user_msg)
            database.save_mood_log(user_id, user_msg, sent, score)
            if current_user and current_user.get("tts_enabled", True):
                try:
                    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".aiff")
                    tmp.close()
                    ap = tts_say(reply, tmp.name)
                    if ap:
                        st.audio(ap)
                except:
                    pass
            st.rerun()

# ----- RUTINAS -----
elif menu == "Rutinas":
    header_col1, header_col2 = st.columns([1,7])
    with header_col1:
        logo_p = os.path.join(ASSETS_DIR, "logo.png")
        if os.path.exists(logo_p):
            st.image(logo_p, width=90)
    with header_col2:
        st.title("Rutinas personalizadas")
        st.markdown("Selecciona una rutina para mejorar tu bienestar físico y mental.")
    st.markdown("---")

    # ---- RUTINA 1: RESPIRACIÓN ----
    col1, col2 = st.columns([1,5])
    with col1:
        img = os.path.join(ASSETS_DIR, "rutina_respiracion.png")
        if os.path.exists(img):
            st.image(img, width=84)
    with col2:
        st.subheader("Respiración guiada")
        st.write("5 min — Nivel bajo")
        if st.button("Iniciar respiración"):
            st.success("Comenzando respiración guiada…")
            st.video("https://www.youtube.com/watch?v=YFSc7Ck0Ao0")  # vídeo respiración
    st.markdown("---")

    # ---- RUTINA 2: ESTIRAMIENTOS ----
    col1, col2 = st.columns([1,5])
    with col1:
        img2 = os.path.join(ASSETS_DIR, "rutina_estiramientos.png")
        if os.path.exists(img2):
            st.image(img2, width=84)
    with col2:
        st.subheader("Estiramientos básicos")
        st.write("5 min — Nivel medio")
        if st.button("Iniciar estiramientos"):
            st.success("Iniciando estiramientos…")
            st.video("https://www.youtube.com/watch?v=2L2lnxIcNmo")  # vídeo de estiramientos
    st.markdown("---")

    # ---- RUTINA 3: YOGA ----
    col1, col2 = st.columns([1,5])
    with col1:
        img3 = os.path.join(ASSETS_DIR, "rutina_yoga.png")
        if os.path.exists(img3):
            st.image(img3, width=84)
    with col2:
        st.subheader("Yoga suave")
        st.write("25 min — Nivel bajo")
        if st.button("Iniciar yoga"):
            st.success("Iniciando yoga suave…")
            st.video("https://www.youtube.com/watch?v=Eml2xnoLpYE")  # vídeo yoga suave
    st.markdown("---")

# ----- PERFIL -----
elif menu == "Perfil":
    header_col1, header_col2 = st.columns([1,7])
    with header_col1:
        logo_p = os.path.join(ASSETS_DIR, "logo.png")
        if os.path.exists(logo_p):
            st.image(logo_p, width=90)
    with header_col2:
        st.title("Perfil y Configuración")
        st.markdown("Gestiona tu información personal, preferencias y ajustes de la aplicación.")
    st.markdown("---")

    st.markdown("### <b>Metas</b>", unsafe_allow_html=True)
    dormir_mejor = st.slider("Dormir mejor", 0, 10, 8)
    reducir_estres = st.slider("Reducir estrés", 0, 10, 3)
    moverme = st.slider("Moverme más (pasos)", 2000, 20000, (current_user.get("target_steps", 8000) if current_user else 8000), step=500)
    st.markdown("---")

    st.markdown("### <b>Ajustes de Accesibilidad</b>", unsafe_allow_html=True)
    colA, colB = st.columns([1,1])
    with colA:
        st.write("Tamaño de letra")
    with colB:
        options = ["Pequeño", "Normal", "Grande"]
        current_font = st.session_state.accesibilidad.get("font_size", "Normal")
        try:
            idx = options.index(current_font)
        except ValueError:
            idx = 1
        font_size = st.radio("tamaño_letra_radio", options, index=idx, horizontal=True, label_visibility="collapsed")

    modo_oscuro = st.checkbox("Modo oscuro", value=st.session_state.accesibilidad.get("dark_mode", False))
    lectura_voz = st.checkbox("Lectura de voz", value=st.session_state.accesibilidad.get("tts_enabled", True))
    contraste_alto = st.checkbox("Contraste alto", value=st.session_state.accesibilidad.get("high_contrast", False))

    # Guardar en session_state para que se aplique al recargar la página
    st.session_state.accesibilidad.update({
        "font_size": font_size,
        "dark_mode": modo_oscuro,
        "tts_enabled": lectura_voz,
        "high_contrast": contraste_alto
    })

    st.markdown("---")
    st.markdown("### <b>Integraciones</b>", unsafe_allow_html=True)
    col1, col2 = st.columns([1,1])
    with col1:
        st.markdown("Apple Health")
    with col2:
        st.markdown("<div style='text-align:right;color:green;font-weight:600;'>Conectado</div>", unsafe_allow_html=True)
    col1, col2 = st.columns([1,1])
    with col1:
        st.markdown("Wearables")
    with col2:
        st.markdown("<div style='text-align:right;color:green;font-weight:600;'>Conectado</div>", unsafe_allow_html=True)

    st.write("")
    if st.button("Sincronizar ahora"):
        st.success("Datos sincronizados.")

    st.markdown("---")

    if st.button("Guardar cambios", use_container_width=True):
        if current_user:
            # Guardar en DB (si tu función soporta estos campos)
            try:
                database.update_user(
                    current_user["user_id"],
                    name=current_user["name"],
                    target_steps=moverme,
                    tts_enabled=lectura_voz,
                    font_size=st.session_state.accesibilidad["font_size"],
                    dark_mode=st.session_state.accesibilidad["dark_mode"],
                    high_contrast=st.session_state.accesibilidad["high_contrast"]
                )
            except Exception:
                pass

            # Refrescar session_state.user
            st.session_state.user.update({
                "target_steps": moverme,
                "tts_enabled": lectura_voz,
                "font_size": st.session_state.accesibilidad["font_size"],
                "dark_mode": st.session_state.accesibilidad["dark_mode"],
                "high_contrast": st.session_state.accesibilidad["high_contrast"]
            })
            st.success("Cambios guardados correctamente.")
        else:
            st.error("No hay usuario activo.")

# fin del archivo
