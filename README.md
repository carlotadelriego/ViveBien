# ViveBien - Plataforma Multimodal de Bienestar (Prototipo)

Este repositorio contiene un prototipo en **Streamlit** para la asignatura *Sistemas Interactivos Inteligentes*.

## Estructura
- `vivebien_main.py` - App principal (Streamlit).
- `data_simulation.py` - Simulación de datos biométricos (pasos, sueño, frecuencia cardiaca).
- `feedback_engine.py` - Motor ligero de análisis de texto y recomendaciones.
- `requirements.txt` - Paquetes sugeridos.

## Cómo ejecutar (local)
1. Crea un entorno virtual (recomendado).
2. `pip3 install -r requirements.txt`
3. Ejecutar: `streamlit run vivebien_main.py`

Notas:
- La transcripción de audio utiliza `speech_recognition` con el servicio Google (requiere conexión a internet para la transcripción).
- La síntesis de voz usa `pyttsx3` (funciona offline en la mayoría de entornos; en algunos sistemas puede requerir dependencias del sistema).

