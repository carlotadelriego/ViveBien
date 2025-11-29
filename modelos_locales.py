import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import whisper
from llama_cpp import Llama


# ======================================================
# 1. MODELO GEMMA 2B IT — RECOMENDACIONES (OFFLINE)
# ======================================================
from llama_cpp import Llama

llm = Llama(
    model_path="./models/gemma-2b-it-Q4_K_M.gguf",
    n_ctx=2048,
    n_threads=8,       # depende de tu CPU
    temperature=0.7,
)

def generate_recommendation(user_text, *args, **kwargs):

    prompt = (
        f"Eres un asistente de bienestar cálido y empático. "
        f"La persona dice: \"{user_text}\". "
        "Responde con un mensaje amable, cercano y motivador de 3–4 líneas. "
        "Háblale directamente y sugiere una acción sencilla para sentirse mejor."
    )

    result = llm(prompt, max_tokens=150)
    return result["choices"][0]["text"].strip()


# ======================================================
# 2. MODELO EMOCIONAL (ROBERTUITO)
# ======================================================

emotion_tokenizer = AutoTokenizer.from_pretrained("pysentimiento/robertuito-emotion-analysis")
emotion_model = AutoModelForSequenceClassification.from_pretrained("pysentimiento/robertuito-emotion-analysis")

def analyze_text_sentiment(text):
    inputs = emotion_tokenizer(text, return_tensors="pt", truncation=True)
    outputs = emotion_model(**inputs)
    scores = torch.softmax(outputs.logits, dim=1)[0]

    label_id = scores.argmax().item()
    label = emotion_model.config.id2label[label_id]
    confidence = float(scores[label_id])
    return label, confidence


# ======================================================
# 3. WHISPER (AUDIO → TEXTO)
# ======================================================

whisper_model = whisper.load_model("small")

def transcribe_audio(path):
    result = whisper_model.transcribe(path, language="es")
    return result["text"]
