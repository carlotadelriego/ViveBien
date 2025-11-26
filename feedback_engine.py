# Motor simple de recomendaciones y análisis de sentimiento (ligero, sin dependencias pesadas)
import re

POS_WORDS = {"bien","contento","contenta","tranquilo","tranquila","feliz","relajado","relajada","descansado","sano","sana","enérgico","enérgica","alegre"}
NEG_WORDS = {"estres","estresado","estresada","cansado","cansada","triste","mal","ansioso","ansiosa","preocupado","preocupada","nervioso","nerviosa","agotado","agotada","insomnio","dificultad"}

def analyze_text_sentiment(text):
    """Análisis simple de sentimiento: cuenta palabras positivas y negativas."""
    t = text.lower()
    # simple tokenization
    tokens = re.findall(r"\\w+", t, flags=re.UNICODE)
    pos = sum(1 for tok in tokens if any(tok.startswith(p) for p in POS_WORDS))
    neg = sum(1 for tok in tokens if any(tok.startswith(n) for n in NEG_WORDS))
    score = (pos - neg) / max(1, len(tokens))
    if score > 0.05:
        sentiment = "Positivo"
    elif score < -0.05:
        sentiment = "Negativo"
    else:
        sentiment = "Neutral"
    return sentiment, score

def generate_recommendation(user_text, latest_bio, target_steps=10000):
    """Genera una recomendación básica combinando texto y biométrica."""
    sentiment, score = analyze_text_sentiment(user_text)
    recs = []
    # Sleep-based suggestions
    if latest_bio.get("sleep_hours",7) < 6.5:
        recs.append("Has dormido menos de lo recomendado. Evita pantallas 1 hora antes de dormir y prueba una rutina de respiración de 10 minutos.")
    elif latest_bio.get("sleep_hours",7) >= 8:
        recs.append("Tu sueño está en buen rango. Mantén la rutina actual y cuida la exposición a luz natural por la mañana.")
    # Steps-based suggestions
    if latest_bio.get("steps",0) < target_steps*0.6:
        recs.append(f"Tu nivel de actividad es bajo. Intenta dar un paseo de 20 minutos o dividir tu objetivo en bloques de 5-10 minutos.")
    else:
        recs.append("Excelente nivel de pasos. Puedes mantenerlo y añadir pequeños estiramientos después de sesiones largas sentado.")
    
    # Heart rate quick check
    if latest_bio.get("heart_rate",70) > 95:
        recs.append("Tu frecuencia cardiaca está alta. Si te sientes mal, descansa y considera hacer respiraciones lentas y profundas. Consulta a un profesional si persiste.")
    # Sentiment-based
    if sentiment == "Negativo":
        recs.append("Veo señales de malestar emocional. Prueba escribir en un diario 5 minutos o hablar con alguien de confianza.")
    elif sentiment == "Positivo":
        recs.append("¡Genial! Mantén las pequeñas rutinas que te funcionan.")
    # Fallback
    if not recs:
        recs.append("Mantén hábitos regulares: hidratación, pausas activas y rutinas de sueño.")
    return " ".join(recs)
