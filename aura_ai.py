# -----------------------------------------------
#  AURA AI - Módulo de Inteligencia Artificial
#  LLM: Llama 3.3 70B via Groq (gratis)
#  TTS: Edge TTS (gratis, sin límites)
#  STT: Whisper via Groq API (gratis, en la nube)
# -----------------------------------------------
#
#  TODO EN LA NUBE - NO REQUIERE MODELOS LOCALES
#
# -----------------------------------------------

import os
import tempfile
import asyncio
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# CONFIGURACIÓN
# ============================================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Modelos de Groq
LLAMA_MODEL = "llama-3.3-70b-versatile"
WHISPER_MODEL = "whisper-large-v3"  # STT en Groq

# ============================================================
# VOCES EDGE TTS PARA ESPAÑOL (gratuitas y sin límites)
# ============================================================

EDGE_TTS_VOICE = "es-ES-ElviraNeural"  # Voz femenina española, cálida

# Otras voces disponibles:
# FEMENINAS:
#   es-ES-ElviraNeural  (España, cálida) ← Default
#   es-ES-AbrilNeural   (España, joven)
#   es-MX-DaliaNeural   (México)
#   es-AR-ElenaNeural   (Argentina)
#   es-CO-SalomeNeural  (Colombia)
# MASCULINAS:
#   es-ES-AlvaroNeural  (España)
#   es-MX-JorgeNeural   (México)

# ============================================================
# SYSTEM PROMPT PARA AURA
# ============================================================

AURA_SYSTEM_PROMPT = """Eres Aura, una asistente virtual de bienestar integral de la plataforma ViveBien.

## Tu personalidad:
- Eres cálida, empática y comprensiva
- Hablas siempre en español de forma natural y cercana
- Nunca juzgas, siempre apoyas
- Eres motivadora pero realista
- Usas un tono conversacional, como una amiga de confianza

## Tu rol:
1. **Apoyo emocional**: Escuchas activamente y validas los sentimientos del usuario
2. **Recomendaciones personalizadas**: Basadas en sus datos biométricos y estado de ánimo
3. **Guía de bienestar**: Sugieres rutinas de respiración, meditación, ejercicio y sueño
4. **Motivación**: Celebras los logros y animas ante los retos

## Datos del usuario disponibles:
- Pasos de hoy: {steps}
- Horas de sueño: {sleep_hours}
- Frecuencia cardíaca: {heart_rate} bpm
- Meta diaria de pasos: {target_steps}
- Estado de ánimo actual: {mood}

## Reglas importantes:
- Responde SIEMPRE en español
- Mantén respuestas concisas (2-4 oraciones máximo, salvo que pidan más detalle)
- Incluye siempre una acción o sugerencia concreta cuando sea apropiado
- Si detectas señales de angustia severa, sugiere amablemente buscar ayuda profesional
- No des diagnósticos médicos, solo orientación de bienestar general
- Usa emojis con moderación para dar calidez (1-2 por mensaje máximo)

## Ejemplos de tono:
- "¡Hola! Me alegra verte por aquí 🌿 ¿Cómo te encuentras hoy?"
- "Entiendo cómo te sientes, es completamente normal. ¿Qué te parece si probamos una respiración rápida para relajarnos?"
- "¡Genial que hayas caminado tanto hoy! Estás muy cerca de tu meta 💪"
"""


# ============================================================
# LLM - LLAMA VIA GROQ (GRATUITO)
# ============================================================

def get_groq_client():
    """Inicializa el cliente de Groq"""
    try:
        from groq import Groq
        return Groq(api_key=GROQ_API_KEY)
    except ImportError:
        raise ImportError("Instala groq: pip install groq")


def chat_with_aura(
    user_message: str,
    biometrics: dict,
    target_steps: int = 8000,
    mood: str = "neutral",
    chat_history: list = None
) -> str:
    """
    Genera una respuesta de Aura usando Llama 3 via Groq.
    
    Args:
        user_message: Mensaje del usuario
        biometrics: Dict con steps, sleep_hours, heart_rate
        target_steps: Meta de pasos del usuario
        mood: Estado de ánimo actual
        chat_history: Lista de tuplas (role, content) con historial
    
    Returns:
        Respuesta de Aura como string
    """
    if not GROQ_API_KEY:
        return "⚠️ Error: No se ha configurado GROQ_API_KEY en el archivo .env"
    
    client = get_groq_client()
    
    # Formatear el system prompt con los datos del usuario
    system_prompt = AURA_SYSTEM_PROMPT.format(
        steps=biometrics.get('steps', 'No disponible'),
        sleep_hours=biometrics.get('sleep_hours', 'No disponible'),
        heart_rate=biometrics.get('heart_rate', 'No disponible'),
        target_steps=target_steps,
        mood=mood
    )
    
    # Construir mensajes con historial
    messages = [{"role": "system", "content": system_prompt}]
    
    # Añadir historial (últimos 10 mensajes)
    if chat_history:
        for role, content in chat_history[-10:]:
            messages.append({
                "role": "user" if role == "user" else "assistant",
                "content": content
            })
    
    messages.append({"role": "user", "content": user_message})
    
    try:
        response = client.chat.completions.create(
            model=LLAMA_MODEL,
            messages=messages,
            temperature=0.7,
            max_tokens=500,
            top_p=0.9,
        )
        return response.choices[0].message.content
    
    except Exception as e:
        return f"⚠️ Error al conectar con Aura: {str(e)}"


# ============================================================
# TTS - EDGE TTS (GRATUITO Y SIN LÍMITES)
# ============================================================

async def _tts_edge_async(text: str, filename: str, voice: str = None) -> str:
    """Función async interna para Edge TTS"""
    import edge_tts
    
    voice = voice or EDGE_TTS_VOICE
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(filename)
    
    return filename


def tts_edge(text: str, filename: str = None, voice: str = None) -> Optional[str]:
    """
    Genera audio con Edge TTS (Microsoft) - GRATUITO Y SIN LÍMITES.
    
    Args:
        text: Texto a convertir en audio
        filename: Ruta donde guardar (opcional)
        voice: Voz a usar (opcional)
    
    Returns:
        Ruta al archivo .mp3 generado
    """
    try:
        import edge_tts
    except ImportError:
        print("⚠️ Instala edge-tts: pip install edge-tts")
        return None
    
    try:
        if filename is None:
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
            filename = tmp.name
            tmp.close()
        
        # Manejar event loop (compatible con Streamlit)
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        
        if loop and loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run, 
                    _tts_edge_async(text, filename, voice)
                )
                future.result(timeout=30)
        else:
            asyncio.run(_tts_edge_async(text, filename, voice))
        
        return filename
    
    except Exception as e:
        print(f"⚠️ Error en Edge TTS: {e}")
        return None


# ============================================================
# STT - WHISPER VIA GROQ API (GRATUITO, EN LA NUBE)
# ============================================================

def stt_groq(audio_file, language: str = "es") -> str:
    """
    Transcribe audio a texto usando Whisper en Groq API.
    
    ✅ GRATUITO
    ✅ EN LA NUBE (no requiere modelos locales)
    ✅ MUY RÁPIDO
    
    Args:
        audio_file: Archivo de audio (file-like object o ruta string)
        language: Código de idioma (es, en, etc.)
    
    Returns:
        Texto transcrito
    """
    if not GROQ_API_KEY:
        return "⚠️ Error: No se ha configurado GROQ_API_KEY"
    
    client = get_groq_client()
    
    # Si es un file-like object, guardarlo temporalmente
    if hasattr(audio_file, 'read'):
        # Determinar extensión del archivo
        filename = getattr(audio_file, 'name', 'audio.wav')
        ext = os.path.splitext(filename)[1] or '.wav'
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tf:
            tf.write(audio_file.read())
            temp_path = tf.name
        cleanup_temp = True
    else:
        temp_path = audio_file
        cleanup_temp = False
    
    try:
        # Abrir el archivo y enviarlo a Groq
        with open(temp_path, "rb") as audio:
            transcription = client.audio.transcriptions.create(
                file=(os.path.basename(temp_path), audio),
                model=WHISPER_MODEL,
                language=language,
                response_format="text"
            )
        
        return transcription.strip()
    
    except Exception as e:
        return f"⚠️ Error transcribiendo: {str(e)}"
    
    finally:
        if cleanup_temp and os.path.exists(temp_path):
            os.unlink(temp_path)


# Alias para compatibilidad
stt_whisper = stt_groq


# ============================================================
# VERIFICAR CONFIGURACIÓN
# ============================================================

def check_configuration() -> dict:
    """
    Verifica qué servicios están configurados.
    
    Returns:
        Dict con el estado de cada servicio
    """
    status = {
        "groq": False,
        "edge_tts": False,
    }
    
    # Verificar Groq (LLM + STT)
    if GROQ_API_KEY:
        try:
            from groq import Groq
            status["groq"] = True
        except ImportError:
            pass
    
    # Verificar Edge TTS
    try:
        import edge_tts
        status["edge_tts"] = True
    except ImportError:
        pass
    
    return status


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 Test de Aura AI")
    print("   100% EN LA NUBE - Sin modelos locales")
    print("=" * 60)
    
    status = check_configuration()
    
    print("\n📋 Estado de servicios:")
    print(f"  • Groq (LLM + STT):  {'✅ OK' if status['groq'] else '❌ Falta GROQ_API_KEY'}")
    print(f"  • Edge TTS (voz):    {'✅ OK' if status['edge_tts'] else '❌ pip install edge-tts'}")
    
    if not status['groq']:
        print("\n⚠️  Configura GROQ_API_KEY en tu archivo .env")
        print("    Obtén tu key gratis en: https://console.groq.com/keys")
    
    # Test de chat
    if status["groq"]:
        print("\n🤖 Test de chat con Aura:")
        test_biometrics = {"steps": 5000, "sleep_hours": 7, "heart_rate": 72}
        response = chat_with_aura(
            "Hola Aura, hoy me siento un poco cansado",
            test_biometrics
        )
        print(f"  Aura: {response}")
    
    # Test de TTS
    if status["edge_tts"]:
        print("\n🔊 Test de Edge TTS:")
        test_file = tts_edge("Hola, soy Aura. Estoy aquí para ayudarte.")
        if test_file:
            print(f"  ✅ Audio generado: {test_file}")
            print(f"  📁 Tamaño: {os.path.getsize(test_file)} bytes")
        else:
            print("  ❌ Error generando audio")
    
    print("\n" + "=" * 60)
    print("✅ Todo listo para usar")
    print("=" * 60)