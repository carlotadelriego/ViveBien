# -----------------------------------------------
#  VIVEBIEN — Plataforma de Bienestar Multimodal
#  Mockup exacto (Login centrado, sin JS)
# python -m streamlit run vivebien_main.py
# -----------------------------------------------

import streamlit as st
import tempfile, os, subprocess, shutil, time
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
ASSETS_DIR = os.path.join(os.getcwd(), "assets")
from audio_recorder_streamlit import audio_recorder
import hashlib


# módulos del proyecto (asegúrate de tenerlos en la misma carpeta)
from data_simulation import generate_history, simulate_biometrics
from feedback_engine import analyze_text_sentiment, generate_recommendation
from aura_ai import chat_with_aura, tts_edge, stt_groq, check_configuration
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
# helpers
# -----------------------------
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
# session state inicial
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
if "chat_initialized" not in st.session_state:
    st.session_state.chat_initialized = False
if "last_audio_hash" not in st.session_state:
    st.session_state.last_audio_hash = None
if "input_key" not in st.session_state:
    st.session_state.input_key = 0
if "pending_audio" not in st.session_state:
    st.session_state.pending_audio = None
if "auto_tts" not in st.session_state:
    st.session_state.auto_tts = False

# -----------------------------
# GLOBAL STYLE (centrado robusto)
# -----------------------------
GLOBAL_STYLE = """
<style>

/* Logo circular (just spacing) */
.login-logo {
    width: 140px;
    margin-bottom: 6px;
}

/* Título */
.login-title {
    font-size: 26px;
    font-weight: 600;
    margin-bottom: 18px;
}

/* Labels e inputs */
.login-label {
    font-weight: 600;
    text-align: left;
    margin: 0;
    margin-top: 10px;
    font-size: 15px;
}
.login-input {
    width: 100%;
    padding: 12px;
    border-radius: 10px;
    border: 1px solid #ccc;
    margin-top: 6px;
    font-size: 15px;
}

/* Botón principal */
.btn-login {
    background: #dff3e6;
    border: none;
    width: 100%;
    padding: 12px;
    border-radius: 10px;
    margin-top: 18px;
    font-size: 17px;
    font-weight: 600;
    cursor: pointer;
}

/* Divider text */
.divider {
    margin-top: 14px;
    color: #666;
    font-weight: 600;
}

/* Social buttons */
.social-row {
    display:flex;
    gap: 10px;
    margin-top: 12px;
}
.social-btn {
    flex: 1;
    padding: 12px;
    border-radius: 10px;
    border: none;
    font-weight: 600;
    font-size: 15px;
    cursor: pointer;
}

/* Google = azul real */
.google { 
    background: #4285F4 !important; 
    color: white !important;
}

/* Apple = rojo suave */
.apple  { 
    background: #FF6B6B !important; 
    color: white !important;
}

/* bottom links */
.bottom-links {
    display:flex;
    justify-content:space-between;
    margin-top: 12px;
    font-size: 14px;
    font-weight: 600;
}
.link {
    cursor: pointer;
    color: #222;
}


/* Chat and rutina small helpers */
.chat-card {
    max-width: 650px;
    margin: 20px auto;
    padding: 18px;
    border-radius: 22px;
    border: 8px solid #e6e6e6;
    background: white;
}
.msg-user { background:#fff; padding:10px 14px; border-radius:12px; border:2px solid #ddd; width:fit-content; margin:8px 0; }
.msg-aura { background:#e0f6d9; padding:10px 14px; border-radius:12px; border:2px solid #c4e8c1; width:fit-content; margin:8px 0; margin-left:auto; }

.rutina-card { background:white; padding:14px; border-radius:14px; margin-bottom:12px; display:flex; border:1px solid #f0f0f0; box-shadow:0 2px 6px rgba(0,0,0,0.04); align-items:center; }
.rutina-img { width:84px; height:84px; border-radius:12px; object-fit:cover; margin-right:12px; }

</style>
"""
st.markdown(GLOBAL_STYLE, unsafe_allow_html=True)

# ------------ ESTILO DEL MOCKUP PARA EL RESUMEN -------------
st.markdown("""
<style>

h2 {
    font-size: 32px;
    font-weight: 700;
}

.card {
    background: #ffffff;
    border: 2px solid #CBD5CE;
    padding: 18px;
    border-radius: 18px;
    margin-bottom: 18px;
}

.recommend-box {
    background: #FFF7C7;
    padding: 18px;
    border-radius: 18px;
    border: 2px solid #E6DFA4;
    font-size: 20px;
    text-align: center;
    margin-top: 10px;
}

.big-btn {
    background: #E9E9E9;
    padding: 16px;
    border-radius: 18px;
    font-size: 20px;
    text-align: center;
    border: 2px solid #B6B6B6;
    margin-top: 12px;
}

.mood-container {
    display: flex;
    justify-content: space-between;
    margin-top: 10px;
}

.mood-container img {
    width: 45px;
    cursor: pointer;
    opacity: 0.4;
}

.mood-selected {
    opacity: 1 !important;
}

</style>
""", unsafe_allow_html=True)


# -----------------------------
# RENDER LOGIN (Mockup exacto)
# -----------------------------
def render_login_screen():
    st.markdown("<div class='fullscreen-center'>", unsafe_allow_html=True)
    st.markdown("<div class='login-card'>", unsafe_allow_html=True)

    # logo (assets/logo.png)
    if os.path.exists("assets/logo.png"):
        st.image("assets/logo.png", width=140)
    else:
        st.markdown("<div style='width:140px;height:140px;border-radius:50%;background:#eaf6ec;margin:0 auto 6px;display:flex;align-items:center;justify-content:center;font-size:40px;'>🧘</div>", unsafe_allow_html=True)

    st.markdown("<div class='login-title'>ViveBien</div>", unsafe_allow_html=True)

    # Email
    st.markdown("<div class='login-label'>Email</div>", unsafe_allow_html=True)
    email = st.text_input("email_input", placeholder="nombre@ejemplo.com", label_visibility="collapsed")

    # Password
    st.markdown("<div class='login-label'>Contraseña</div>", unsafe_allow_html=True)
    password = st.text_input("pass_input", placeholder="••••••••••", type="password", label_visibility="collapsed")

    # Botón acceder
    if st.button("Acceder", use_container_width=True):
        if not email or not password:
            st.warning("Completa los campos.")
        else:
            ok, msg, user_info = database.login_user(email.strip(), password)
            if ok:
                st.session_state.logged_in = True
                st.session_state.user = user_info
                st.session_state.menu = "Inicio"
                st.session_state.chat_history = []
                st.rerun()
            else:
                st.error(msg)

    # Bottom links: Olvidaste / Unete
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<div class='link'>¿Olvidaste tu contraseña?</div>", unsafe_allow_html=True)
    with col2:
        if st.button("¡Únete a nosotros!"):
            st.session_state.show_register = True
            st.rerun()


    # Divider
    st.markdown("<div class='divider'>o continúa con</div>", unsafe_allow_html=True)

    # Social buttons (visual)
    colg, cola = st.columns(2)
    with colg:
        st.button("Google", use_container_width=True)
    with cola:
        st.button("Apple ID", use_container_width=True)


    st.markdown("</div></div>", unsafe_allow_html=True)

# -----------------------------
# RENDER REGISTER (centrado, mockup-style)
# -----------------------------
def render_register_screen():
    st.markdown("<div class='fullscreen-center'>", unsafe_allow_html=True)
    st.markdown("<div class='login-card' style='width:520px;'>", unsafe_allow_html=True)

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
# Sidebar (aparece solo después de login)
# -----------------------------
with st.sidebar:
    st.title("ViveBien 🌿")
    st.write(f"Hola, {st.session_state.user['name']}")
    st.markdown("---")
    st.session_state.menu = st.radio("Navegación", ["Inicio","Resumen","Registro de Estado","Chat con Aura","Rutinas","Perfil"])
    if st.button("Cerrar sesión"):
        st.session_state.logged_in = False
        st.session_state.user = None
        st.session_state.chat_history = []
        st.session_state.menu = "Resumen"
        st.rerun()

# -----------------------------
# Recuperar datos de usuario
# -----------------------------
current_user = st.session_state.user
user_id = current_user["user_id"]
menu = st.session_state.menu



# -----------------------------
# INICIO
# -----------------------------
if menu == "Inicio":

    st.markdown("""
    <style>
        .inicio-card {
            background: #ffffff;
            padding: 35px;
            border-radius: 22px;
            border: 2px solid #e6e6e6;
            max-width: 750px;
            margin: 0 auto;
            box-shadow: 0 4px 12px rgba(0,0,0,0.04);
        }
        .inicio-title {
            font-size: 34px;
            font-weight: 700;
            text-align: center;
            margin-bottom: 6px;
        }
        .inicio-subtitle {
            font-size: 17px;
            color: #666;
            text-align: center;
            margin-bottom: 30px;
        }
        .reco-box {
            background: #F8F9D7;
            padding: 20px;
            border-radius: 16px;
            border: 2px solid #ECE9A4;
            margin-bottom: 25px;
            font-size: 17px;
        }
        .inicio-buttons {
            display: flex;
            justify-content: center;
            gap: 15px;
            margin-top: 10px;
        }
        .inicio-btn button {
            width: 210px !important;
            padding: 14px !important;
            font-size: 17px !important;
            font-weight: 600 !important;
            border-radius: 14px !important;
        }
    </style>
    """, unsafe_allow_html=True)


    # Título
    st.markdown(
        f"<div class='inicio-title'>Bienvenid@, {current_user['name']} 🌿</div>",
        unsafe_allow_html=True
    )
    st.markdown(
        "<div class='inicio-subtitle'>Una plataforma inteligente que te acompaña a mejorar tu salud, tus hábitos y tu bienestar emocional.</div>",
        unsafe_allow_html=True
    )

    # Recomendación
    st.markdown("<h4>Recomendación reciente</h4>", unsafe_allow_html=True)

    if st.session_state.last_recommendation:
        st.markdown(
            f"<div class='reco-box'>{st.session_state.last_recommendation}</div>",
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            "<div class='reco-box'>Aún no hay recomendaciones. Registra tu estado para que Aura pueda ayudarte.</div>",
            unsafe_allow_html=True
        )

    # Botones
    st.markdown("<div class='inicio-buttons'>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1,1,1], gap="medium")

    with col1:
        if st.button("Registrar estado", key="inicio_registro"):
            st.session_state.menu = "Registro de Estado"
            st.rerun()

    with col2:
        if st.button("Ver resumen", key="inicio_resumen"):
            st.session_state.menu = "Resumen"
            st.rerun()

    with col3:
        if st.button("Chat con Aura", key="inicio_chat"):
            st.session_state.menu = "Chat con Aura"
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)



# -----------------------------
# RESUMEN (Mockup fiel)
# -----------------------------
elif menu == "Resumen":
    rows = database.load_biometrics(user_id)
    df = biometrics_rows_to_df(rows)

    st.image("assets/logo.png", width=70)
    st.markdown(f"<h2>Holaa, {current_user['name']}</h2>", unsafe_allow_html=True)

    if df.empty:
        st.warning("No hay datos registrados todavía.")
    else:
        latest = df.tail(1).iloc[0]

        # TARJETA PASOS
        st.markdown("---")
        col1, col2 = st.columns([4,1])
        with col1:
            st.markdown("## Pasos")
            st.markdown(f"<h2>{int(latest.steps)}</h2>", unsafe_allow_html=True)
        with col2:
            st.image("assets/icon_pasos.png", width=100)


        # TARJETA SUEÑO
        st.markdown("---")
        col1, col2 = st.columns([4,1])
        with col1:
            st.markdown("## Sueño")
            st.markdown(f"<h2>{latest.sleep_hours} hs</h2>", unsafe_allow_html=True)
        with col2:
            st.image("assets/icon_sueno.png", width=100)


        # ESTADO DE ÁNIMO
        st.markdown("---")
        st.markdown("## Estado de Ánimo")

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
                st.image(icon_path, width=70)

                # el botón cambia cuando está seleccionado
                selected = (st.session_state.mood == value)
                btn_label = f"✔ {label}" if selected else label

                if st.button(btn_label, key=f"mood_btn_{value}"):
                    st.session_state.mood = value




        # RECOMENDACIÓN
        st.markdown("<div class='recommend-box'>Tu recomendación de hoy es</div>", unsafe_allow_html=True)

        # BOTÓN CHAT
        st.markdown("<div class='big-btn'>Chatea con Aura</div>", unsafe_allow_html=True)



# -----------------------------
# REGISTRO DEL ESTADO
# -----------------------------
elif menu == "Registro de Estado":
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
            reco = generate_recommendation(user_text, latest, current_user.get("target_steps",8000))
            st.session_state.last_recommendation = reco
            st.info(reco)
            if current_user.get("tts_enabled", True):
                try:
                    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".aiff")
                    tmp.close()
                    ap = tts_say(reco, tmp.name)
                    if ap:
                        st.audio(ap)
                except:
                    pass
    st.markdown("</div>", unsafe_allow_html=True)

# -----------------------------
# CHAT CON AURA
# -----------------------------
elif menu == "Chat con Aura":
    
    # ---- HEADER ----
    col_logo, col_title = st.columns([1, 5])
    with col_logo:
        if os.path.exists("assets/logo.png"):
            st.image("assets/logo.png", width=65)
    with col_title:
        st.markdown("## Chatea con Aura")
    
    # ---- VERIFICAR CONFIGURACIÓN ----
    ai_status = check_configuration()
    if not ai_status["groq"]:
        st.error("⚠️ Configura GROQ_API_KEY en tu archivo .env")
        st.info("Obtén tu key gratis en: https://console.groq.com/keys")
        st.stop()
    
    # ---- MENSAJE DE BIENVENIDA ----
    if not st.session_state.chat_initialized:
        welcome = "¡Hola! 🌿 Soy Aura, tu asistente de bienestar. Estoy aquí para acompañarte y ayudarte a sentirte mejor. ¿Cómo te encuentras hoy?"
        st.session_state.chat_history.append(("aura", welcome))
        st.session_state.chat_initialized = True
    
    # ---- TOGGLE LECTURA AUTOMÁTICA ----
    col_toggle, col_spacer = st.columns([1, 3])
    with col_toggle:
        st.session_state.auto_tts = st.toggle("🔊 Lectura automática", value=st.session_state.auto_tts)
    
    # ---- REPRODUCIR AUDIO PENDIENTE (de botón 🔊) ----
    if st.session_state.pending_audio:
        st.audio(st.session_state.pending_audio, format="audio/mp3", autoplay=True)
        st.session_state.pending_audio = None
    
    # ---- MOSTRAR MENSAJES ----
    for i, (role, text) in enumerate(st.session_state.chat_history):
        if role == "user":
            st.markdown(f"<div class='msg-user'>{text}</div>", unsafe_allow_html=True)
        else:
            col_msg, col_audio = st.columns([10, 1])
            with col_msg:
                st.markdown(f"<div class='msg-aura'>{text}</div>", unsafe_allow_html=True)
            with col_audio:
                if st.button("🔊", key=f"listen_{i}", help="Escuchar este mensaje"):
                    audio_file = tts_edge(text)
                    if audio_file:
                        st.session_state.pending_audio = audio_file
                        st.rerun()
    
    st.markdown("---")
    
    # ---- BARRA DE INPUT ----
    col_text, col_mic, col_send = st.columns([6, 1, 1])
    
    with col_text:
        user_msg = st.text_input(
            "msg",
            placeholder="Escribe tu mensaje...",
            key=f"chat_input_{st.session_state.input_key}",
            label_visibility="collapsed"
        )
    
    with col_mic:
        audio_bytes = audio_recorder(
            text="",
            recording_color="#e74c3c",
            neutral_color="#95a5a6",
            icon_name="microphone",
            icon_size="2x",
            pause_threshold=2.0,
            sample_rate=16000
        )
    
    with col_send:
        send_btn = st.button("📤", use_container_width=True, help="Enviar")
    
    # ---- PROCESAR AUDIO GRABADO (solo si es nuevo) ----
    audio_processed = False
    if audio_bytes:
        audio_hash = hashlib.md5(audio_bytes).hexdigest()
        
        if audio_hash != st.session_state.last_audio_hash:
            st.session_state.last_audio_hash = audio_hash
            
            with st.spinner("🎤 Escuchando..."):
                with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                    tmp.write(audio_bytes)
                    tmp_path = tmp.name
                
                transcribed = stt_groq(tmp_path)
                os.unlink(tmp_path)
                
                if transcribed and not transcribed.startswith("⚠️"):
                    user_msg = transcribed
                    audio_processed = True
                    st.toast(f"🎤 {transcribed}")
                else:
                    st.warning("No pude entenderte. ¿Puedes repetirlo?")
    
    # ---- ENVIAR MENSAJE ----
    if (send_btn or audio_processed) and user_msg and user_msg.strip():
        
        # Obtener biométricos
        rows = database.load_biometrics(user_id)
        df = biometrics_rows_to_df(rows)
        bio = df.tail(1).iloc[0].to_dict() if not df.empty else simulate_biometrics()
        
        # Guardar mensaje usuario
        st.session_state.chat_history.append(("user", user_msg))
        
        # Respuesta de Aura
        with st.spinner("🌿 Aura está pensando..."):
            reply = chat_with_aura(
                user_message=user_msg,
                biometrics=bio,
                target_steps=current_user.get("target_steps", 8000),
                mood=st.session_state.get("mood", "neutral"),
                chat_history=st.session_state.chat_history[:-1]
            )
        
        st.session_state.chat_history.append(("aura", reply))
        
        # Guardar en BD
        sent, score = analyze_text_sentiment(user_msg)
        database.save_mood_log(user_id, user_msg, sent, score)
        
        # Audio SOLO si lectura automática está activada
        if st.session_state.auto_tts:
            audio_file = tts_edge(reply)
            if audio_file:
                st.session_state.pending_audio = audio_file
        
        # Limpiar input
        st.session_state.input_key += 1
        st.rerun()
    
    # ---- LIMPIAR CHAT ----
    st.markdown("<br>", unsafe_allow_html=True)
    _, col_clear, _ = st.columns([2, 1, 2])
    with col_clear:
        if st.button("🗑️ Limpiar", use_container_width=True):
            st.session_state.chat_history = []
            st.session_state.chat_initialized = False
            st.session_state.last_audio_hash = None
            st.session_state.input_key += 1
            st.session_state.pending_audio = None
            st.rerun()
            
# -----------------------------
# RUTINAS
# -----------------------------
elif menu == "Rutinas":
    st.title("Rutinas personalizadas")
    # Rutina 1
    col1, col2 = st.columns([1,3])
    with col1:
        if os.path.exists("assets/rutina_respiracion.png"):
            st.image("assets/rutina_respiracion.png", width=84)
        else:
            st.markdown("<div class='rutina-img'>🧘</div>", unsafe_allow_html=True)
    with col2:
        st.subheader("Respiración guiada")
        st.write("5 min — Nivel bajo")
        if st.button("Iniciar respiración"):
            st.success("Comenzando respiración guiada…")
    st.markdown("---")

    # Rutina 2
    col1, col2 = st.columns([1,3])
    with col1:
        if os.path.exists("assets/rutina_estiramientos.png"):
            st.image("assets/rutina_estiramientos.png", width=84)
        else:
            st.markdown("<div class='rutina-img'>🤸</div>", unsafe_allow_html=True)
    with col2:
        st.subheader("Estiramientos básicos")
        st.write("10 min — Nivel medio")
        if st.button("Iniciar estiramientos"):
            st.success("Iniciando estiramientos…")
    st.markdown("---")

    # Rutina 3
    col1, col2 = st.columns([1,3])
    with col1:
        if os.path.exists("assets/rutina_yoga.png"):
            st.image("assets/rutina_yoga.png", width=84)
        else:
            st.markdown("<div class='rutina-img'>🧘‍♀️</div>", unsafe_allow_html=True)
    with col2:
        st.subheader("Yoga suave")
        st.write("15 min — Nivel bajo")
        if st.button("Iniciar yoga"):
            st.success("Iniciando yoga suave")
    st.markdown("---")

# -----------------------------
# PERFIL
# -----------------------------
elif menu == "Perfil":

    # ---- HEADER ------------------------------------------------------------------
    header_col1, header_col2 = st.columns([1,4])
    with header_col1:
        if os.path.exists("assets/logo.png"):
            st.image("assets/logo.png", width=60)
        else:
            st.markdown("<div style='width:60px;height:60px;border-radius:50%;background:#eaf6ec;display:flex;align-items:center;justify-content:center;font-size:30px;'>🧘‍♀️</div>", unsafe_allow_html=True)

    with header_col2:
        st.markdown("<h2 style='margin-top:8px;'>Perfil</h2>", unsafe_allow_html=True)

    st.markdown("---")

    # ============================================================================
    # METAS
    # ============================================================================
    st.markdown("### <b>Metas</b>", unsafe_allow_html=True)

    dormir_mejor = st.slider("Dormir mejor", 0, 10, 8)
    reducir_estres = st.slider("Reducir estrés", 0, 10, 3)
    moverme = st.slider("Moverme más (pasos)", 2000, 20000, current_user.get("target_steps", 8000), step=500)

    st.markdown("---")

    # ============================================================================
    # ACCESIBILIDAD
    # ============================================================================
    st.markdown("### <b>Ajustes de Accesibilidad</b>", unsafe_allow_html=True)

    # Tamaño de letra
    colA, colB = st.columns([1,1])
    with colA:
        st.write("Tamaño de letra")
    with colB:
        font_size = st.radio(
            "tamaño_letra_radio",
            ["Pequeño", "Normal", "Grande"],
            horizontal=True,
            label_visibility="collapsed"
        )

    modo_oscuro = st.checkbox("Modo oscuro")
    lectura_voz = st.checkbox("Lectura de voz", value=current_user.get("tts_enabled", True))
    contraste_alto = st.checkbox("Contraste alto")

    st.markdown("---")

    # ============================================================================
    # INTEGRACIONES
    # ============================================================================
    st.markdown("### <b>Integraciones</b>", unsafe_allow_html=True)

    # ---- Apple Health ----
    col1, col2 = st.columns([1,1])
    with col1:
        st.markdown("Apple Health")
    with col2:
        st.markdown("<div style='text-align:right;color:green;font-weight:600;'>Conectado</div>", unsafe_allow_html=True)

    # ---- Wearables ----
    col1, col2 = st.columns([1,1])
    with col1:
        st.markdown("Wearables")
    with col2:
        st.markdown("<div style='text-align:right;color:green;font-weight:600;'>Conectado</div>", unsafe_allow_html=True)

    st.write("")
    if st.button("Sincronizar ahora"):
        st.success("Datos sincronizados.")

    st.markdown("---")

    # ============================================================================
    # GUARDAR
    # ============================================================================
    if st.button("Guardar cambios", use_container_width=True):
        database.update_user(
            user_id,
            name=current_user["name"],
            target_steps=moverme,
            tts_enabled=lectura_voz
        )
        st.session_state.user["target_steps"] = moverme
        st.session_state.user["tts_enabled"] = lectura_voz
        st.success("Cambios guardados correctamente.")

    st.markdown("</div>", unsafe_allow_html=True)
