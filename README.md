***ViveBien – Plataforma Multimodal de Bienestar***
Este repositorio contiene la implementación del proyecto ViveBien, desarrollado para la asignatura Sistemas Interactivos Inteligentes.
El sistema combina análisis emocional, simulación de métricas de bienestar, chat interactivo y rutinas guiadas mediante contenido multimedia, todo integrado en una interfaz web construida con Streamlit.

**Estructura del proyecto**:
  vivebien_main.py – Aplicación principal y sistema de navegación.
  data_simulation.py – Generación y simulación de métricas (pasos, sueño, energía, frecuencia cardíaca, desafío semanal).
  modelos_locales.py – Integración del modelo emocional basado en pysentimiento.
  database.py – Gestión ligera de datos y estados.
  /assets – Imágenes, iconos y recursos visuales.
  /models – Pesos o archivos relacionados con modelos utilizados.
  requirements.txt – Dependencias necesarias para ejecutar el sistema.

**Funcionalidades principales**:
  - Análisis emocional en español mediante pysentimiento/robertuito-emotion-analysis.
  - Chat interactivo que adapta las respuestas al estado emocional detectado.
  - Simulación de biometrías (pasos, sueño, energía, frecuencia cardíaca, progreso semanal).
  - Rutinas guiadas con vídeos integrados desde YouTube (respiración, estiramientos, yoga).
  - Visualizaciones personalizadas: gráfico donut, barras de progreso, calendario interactivo y tendencias de dos semanas.
  - Exportación de reportes con métricas y comparativas.
  - Arquitectura modular y uso de st.session_state para persistencia de estado.

**Cómo ejecutar el proyecto (local)**:
1. **Clonar el repositorio**:
git clone https://github.com/carlotadelriego/ViveBien.git
cd ViveBien
2. **Crear un entorno virtual (opcional pero recomendado)**:
python -m venv venv
source venv/bin/activate   # Mac/Linux  
venv\Scripts\activate      # Windows
3. **Instalar dependencias**:
pip install -r requirements.txt
4. **Ejecutar la aplicación**:
streamlit run vivebien_main.py
**Nota**: la primera carga del modelo emocional puede tardar unos segundos por inicialización.

**Notas técnicas**:
  - Las rutinas utilizan vídeos de YouTube, por lo que se requiere conexión a internet.
  - El modelo emocional se ejecuta en CPU sin necesidad de GPU.
  - La aplicación utiliza Streamlit, por lo que puede regenerar la interfaz al cambiar de página; st.session_state se utiliza para evitar pérdida de estado.
  - Todos los recursos visuales están optimizados para funcionar dentro del flujo de Streamlit.
