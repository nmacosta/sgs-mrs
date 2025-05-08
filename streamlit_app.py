import streamlit as st
import requests
import os
from urllib.parse import urljoin, urlencode
import json # Para el pretty print del JSON y para el LLM
import time # Para spinners y posibles timeouts
from bs4 import BeautifulSoup # Para limpiar HTML si el LLM tiene problemas

# --- IMPORTACIONES PARA GEMINI ---
import google.generativeai as genai
# ----------------------------------

# --- Configuración API ---
# (Sin cambios respecto al original)

# --- Funciones de Ayuda ---

def get_api_token(api_username, api_password, config):
    """Autentica contra la API y devuelve un token."""
    api_base_url = config.get('api_base_url')
    if not api_base_url:
        st.error("Error: 'api_base_url' no definida en la configuración del entorno.")
        return None

    login_url = urljoin(api_base_url, "custom/apps/api.php?login")
    payload = {"username": api_username, "password": api_password}
    headers = {'Content-Type': 'application/json'}

    try:
        response = requests.post(login_url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        token = data.get("token") or data.get("access_token") or data.get("data", {}).get("token")

        if not token:
            st.error(f"Login fallido: No se pudo encontrar token en la respuesta. Respuesta: {data}")
            return None
        return token
    except requests.exceptions.HTTPError as e:
        st.error(f"Error HTTP {e.response.status_code} durante la autenticación en {login_url}.")
        if e.response.status_code == 401:
            st.error("Credenciales inválidas o no autorizadas.")
        else:
            try:
                st.error(f"Respuesta del servidor: {e.response.text}")
            except Exception:
                st.error("No se pudo obtener el detalle de la respuesta del servidor.")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error de conexión durante la autenticación a {login_url}: {e}")
        return None
    except Exception as e:
        st.error(f"Error inesperado procesando el login: {e}")
        return None

def get_kpi_data(token, country_id, config):
    """Obtiene datos del endpoint de KPI para historias médicas."""
    api_base_url = config.get('api_base_url')
    if not api_base_url:
        st.error("Error: 'api_base_url' no definida en la configuración del entorno.")
        return None

    kpi_action_params = {"afn": "admin", "cfn": "kpis"}
    kpi_endpoint_path = "custom/apps/api.php"
    kpi_url = f"{urljoin(api_base_url, kpi_endpoint_path)}?{urlencode(kpi_action_params)}"

    payload = {
        "page-id": "kpis",
        "section-id": "kpis",
        "kpi-name": "medicalrecords",
        "country-ids": country_id
    }
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    try:
        response = requests.get(kpi_url, headers=headers, json=payload, timeout=60) # GET con payload en JSON
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.HTTPError as e:
        st.error(f"Error HTTP {e.response.status_code} al obtener datos de Historias Médicas desde {kpi_url}.")
        try:
            st.error(f"Respuesta del servidor (HM): {e.response.text}")
        except Exception:
            st.error("No se pudo obtener el detalle de la respuesta del servidor (HM).")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error de conexión al obtener datos de Historias Médicas desde {kpi_url}: {e}")
        return None
    except json.JSONDecodeError:
        st.error(f"Error decodificando JSON de la respuesta de Historias Médicas ({kpi_url}). Respuesta recibida:")
        st.code(response.text, language='text')
        return None
    except Exception as e:
        st.error(f"Error inesperado al obtener datos de Historias Médicas: {e}")
        return None

def get_exam_data(token, country_id, config):
    """Obtiene datos del endpoint de KPI para resultados de exámenes."""
    api_base_url = config.get('api_base_url')
    if not api_base_url:
        st.error("Error: 'api_base_url' no definida en la configuración del entorno.")
        return None

    kpi_action_params = {"afn": "admin", "cfn": "kpis"}
    kpi_endpoint_path = "custom/apps/api.php"
    kpi_url = f"{urljoin(api_base_url, kpi_endpoint_path)}?{urlencode(kpi_action_params)}"

    payload = {
        "page-id": "kpis",
        "section-id": "kpis",
        "kpi-name": "exams", # Modificado para exámenes
        "country-ids": country_id
    }
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    try:
        response = requests.get(kpi_url, headers=headers, json=payload, timeout=60) # GET con payload en JSON
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.HTTPError as e:
        st.error(f"Error HTTP {e.response.status_code} al obtener datos de Exámenes desde {kpi_url}.")
        try:
            st.error(f"Respuesta del servidor (Exámenes): {e.response.text}")
        except Exception:
            st.error("No se pudo obtener el detalle de la respuesta del servidor (Exámenes).")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error de conexión al obtener datos de Exámenes desde {kpi_url}: {e}")
        return None
    except json.JSONDecodeError:
        st.error(f"Error decodificando JSON de la respuesta de Exámenes ({kpi_url}). Respuesta recibida:")
        st.code(response.text, language='text')
        return None
    except Exception as e:
        st.error(f"Error inesperado al obtener datos de Exámenes: {e}")
        return None

def get_lab_data(token, country_id, config):
    """Obtiene datos del endpoint de KPI para resultados de exámenes."""
    api_base_url = config.get('api_base_url')
    if not api_base_url:
        st.error("Error: 'api_base_url' no definida en la configuración del entorno.")
        return None

    kpi_action_params = {"afn": "admin", "cfn": "kpis"}
    kpi_endpoint_path = "custom/apps/api.php"
    kpi_url = f"{urljoin(api_base_url, kpi_endpoint_path)}?{urlencode(kpi_action_params)}"

    payload = {
        "page-id": "kpis",
        "section-id": "kpis",
        "kpi-name": "labresults", # Modificado para exámenes
        "country-ids": country_id
    }
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    try:
        response = requests.get(kpi_url, headers=headers, json=payload, timeout=60) # GET con payload en JSON
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.HTTPError as e:
        st.error(f"Error HTTP {e.response.status_code} al obtener datos de Exámenes desde {kpi_url}.")
        try:
            st.error(f"Respuesta del servidor (Exámenes): {e.response.text}")
        except Exception:
            st.error("No se pudo obtener el detalle de la respuesta del servidor (Exámenes).")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error de conexión al obtener datos de Exámenes desde {kpi_url}: {e}")
        return None
    except json.JSONDecodeError:
        st.error(f"Error decodificando JSON de la respuesta de Exámenes ({kpi_url}). Respuesta recibida:")
        st.code(response.text, language='text')
        return None
    except Exception as e:
        st.error(f"Error inesperado al obtener datos de Exámenes: {e}")
        return None



# --- FUNCIÓN PARA GEMINI ---
def generate_clinical_analysis_with_llm(combined_json_data_for_llm, model_name, prompt_instructions_template, gemini_api_key):
    """Genera análisis clínico usando Gemini."""
    try:
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel(model_name)

        json_string_for_prompt = json.dumps(combined_json_data_for_llm, indent=2, ensure_ascii=False)
        full_prompt = prompt_instructions_template.replace("{json_data_placeholder}", json_string_for_prompt)

        # st.subheader("Prompt enviado al LLM (para depuración):")
        # st.text_area("Prompt:", full_prompt, height=300)

        generation_config = genai.GenerationConfig(
            temperature=0.2,
            max_output_tokens=131072 # Aumentado para permitir respuestas más largas si es necesario. Verifica límites de modelo.
                                   # Gemini 1.5 Pro tiene 1M tokens, Flash 1M, pero la respuesta puede ser menor.
                                   # `max_output_tokens` en `GenerationConfig` suele referirse a la *respuesta*.
                                   # La longitud total (prompt + respuesta) es manejada por `model.count_tokens`.
        )

        response = model.generate_content(
            full_prompt,
            generation_config=generation_config,
            request_options={'timeout': 600} # 10 minutos de timeout
        )
        # Simple HTML cleaner for ExamResults (optional, LLM might handle it)
        #soup = BeautifulSoup(response.text, "html.parser")
        #return soup.get_text() # This would strip ALL html, might be too aggressive.
        # It's better to let the LLM do the smart extraction as instructed in the prompt.
        return response.text

    except genai.types.generation_types.BlockedPromptException as blocked_error:
        st.error("Error: La solicitud al LLM fue bloqueada por políticas de seguridad.")
        try:
            feedback = getattr(blocked_error, 'response', {}).get('prompt_feedback', None)
            if feedback: st.warning(f"Razón del bloqueo: {feedback}")
            # Check if response object exists and has prompt_feedback attribute
            # This part might be tricky as 'response' might not be fully formed in a BlockedPromptException
            # For now, rely on the feedback from the exception itself if available.
        except Exception: pass
        return None
    except Exception as e:
        st.error(f"Ocurrió un error durante la generación con el LLM: {e}")
        if hasattr(e, 'message'): st.error(f"Detalle: {e.message}")
        # If the error is about token limits, it might be in the response or exception details
        if "token limit" in str(e).lower():
            st.warning("El prompt o la respuesta podrían haber excedido el límite de tokens del modelo.")
        return None

# --- Prompt para Gemini (Instrucciones para el Análisis Clínico) ---
PROMPT_INSTRUCTIONS_TEMPLATE = """
Instrucciones Detalladas para la Generación del Análisis Clínico:

Interpretación del JSON:
Aquí está el JSON con los datos del paciente:
{json_data_placeholder}

Este JSON contiene dos claves principales: "medical_history" y "exam_results".
- Para "medical_history": Analiza el JSON para extraer todos los registros médicos del paciente de `medical_history.Records`. Procesa todos los objetos dentro de ese array.
- Para "exam_results": Analiza el JSON para extraer los resultados de los exámenes del paciente de `exam_results.Records`.
- Para "lab_results": Analiza el JSON para extraer los resultados de los laboratorios del paciente de `lab_results.Records`.

Analiza el JSON proporcionado para extraer toda la información relevante.
Consolidación del Historial Médico y Exámenes:

Reúne toda la información relevante de cada registro para construir un informe completo y cronológico.
Generación del Análisis Clínico (siguiendo un esquema de referencia tipo PDF):
El informe final debe estructurarse de la siguiente manera. Si alguna información no está disponible en el JSON para un campo específico del esquema de referencia, indícalo claramente (ej. "No disponible en JSON" o "Dato no suministrado").

A. IDENTIFICACIÓN DEL PACIENTE (Extraer de la sección "medical_history")

Nombre: (Extraer de `medical_history.Records[0].Patient.Name` si `medical_history.Records` existe y no está vacío, o el primer `Patient.Name` que encuentres en `medical_history`. Si no hay datos en `medical_history` pero sí en `exam_results`, usa `exam_results.Records[0].Patient.Name`.)
Cédula (referencial): (Extraer de `medical_history.Records[0].Patient.CountryID` de forma similar. Si no, de `exam_results`.)
Número de Atenciones (Consultas Médicas): (Contar el número de registros en `medical_history.Records`. Si `medical_history` o `medical_history.Records` es nulo o vacío, indicar 0 o "No disponible".)
Fechas de Atenciones (Consultas Médicas): (Listar todas las `Date` de los registros en `medical_history.Records`, formateadas dd/mm/aaaa HH:MM AM/PM. Si es nulo o vacío, indicar "No disponible".)
Número de Exámenes Registrados: (Contar el número de registros en `exam_results.Records`. Si `exam_results` o `exam_results.Records` es nulo o vacío, indicar 0 o "No disponible".)

B. ANTECEDENTES (Consolidar de todos los registros en `medical_history.Records`, principalmente de `History.Description`. Buscar patrones o información recurrente.)

Personales: (Condiciones médicas preexistentes, alergias, hábitos, etc., de `History.Description` y `Sickness` si es relevante para el historial general).
Familiares: (Condiciones médicas en la familia del paciente, si se menciona en `History.Description`).
Quirúrgicos: (Intervenciones quirúrgicas previas, si se mencionan en `History.Description`).
Ginecológicos: (Si se mencionan en `History.Description`).
Epidemiológicos/Otros: (Inmunizaciones, exposición a enfermedades, viajes, hábitos específicos como tabaquismo (Tabáquicos), alcohol (OH), ocupación, etc., desde `History.Description`).
(Si no hay datos en `medical_history.Records` para antecedentes, indicar "No hay información de antecedentes disponible en las historias médicas".)

C. ORGANIZACIÓN CRONOLÓGICA DE DATOS POR EVENTO DE ATENCIÓN (CONSULTA MÉDICA)
(Para cada registro en `medical_history.Records` dentro del JSON proporcionado):

Consulta [ID del Registro] (Usar el `ID` principal del registro, ej. "Consulta 2750")
Fecha de consulta: (Usar `Date`)
Motivo de Consulta: (Usar `Reason`)
Enfermedad Actual / Padecimiento: (Usar `Sickness`. Describir la condición que llevó a la consulta).
Signos Vitales: (TAS: `VitalSigns.TAS` mmHg, TAD: `VitalSigns.TAD` mmHg, FC: `VitalSigns.FC` x', Peso: `VitalSigns.Weight` Kg, Talla: `VitalSigns.Size` Mts. Indicar "0", "No registrado" o "No aplica" si el valor es 0, null o no es pertinente para la consulta).
Examen Físico: (Usar `PhysicalExam.Description`. Indicar si está vacío o no aplica. Notar `PhysicalExam.Type`).
Diagnósticos: (Listar cada diagnóstico de `Diagnostics`: [ID] - [Name]. Si `Diagnostics` es null, vacío, o no aplica, indicar "Sin diagnósticos registrados para este evento" o similar).
Exámenes Indicados/Realizados (durante la consulta): (Listar cada examen de `Exams`: [ID] - [Name]. Si `Exams` es null, vacío, o no aplica, indicar "Sin exámenes indicados/realizados para este evento").
Tratamiento(s), Plan de Acción y Comentarios:
Medicamentos: (Listar cada medicamento de `Medicines`: [Name] ([Generic], [Code]) - Dosis/Presentación: [Presentation] - Indicaciones: [Indications] - Laboratorio: [Laboratory]. Si `Medicines` es null o no aplica, indicar "Sin medicamentos recetados para este evento").
Indicaciones Generales/Comentarios: (Usar `Comments`. Ejemplo: "Reposo por RestDays días", "Uso de epicondilera 15 días").
Días de Reposo: (Usar `RestDays` si es > 0).
(Si no hay datos en `medical_history.Records`, esta sección debe indicar "No hay eventos de atención médica registrados".)

D. GENERACIÓN DE RESUMEN Y ANÁLISIS LONGITUDINAL (Basado en `medical_history.Records`)

Resumen Conciso de la Atención por Evento: (Para cada fecha de atención en `medical_history.Records`, resumir brevemente: ej. "dd/mm/aaaa: Consulta por [Motivo principal]. Diagnóstico(s) principal(es): [Diagnósticos]. Tratamiento principal: [Medicamento/Indicación].")
Análisis Longitudinal de Hallazgos Positivos y Negativos:
Condiciones Clínicas Persistentes/Recurrentes: (Identificar condiciones que aparecen en múltiples registros o que se mencionan como crónicas en los antecedentes).
Evolución de Diagnósticos: (Cómo han cambiado, se han resuelto o se han añadido diagnósticos con el tiempo).
Tendencias en Signos Vitales: (Si hay suficientes datos, comentar tendencias en peso, TAS/TAD, etc.).
Respuesta a Tratamientos (si se puede inferir): (Mencionar si se observa mejoría, recurrencia a pesar del tratamiento, o efectos secundarios, basado en `Comments` o consultas subsecuentes).
Patrones Notables: (Cualquier otro patrón observado: tipos de medicamentos frecuentemente recetados, necesidad de múltiples consultas para un mismo problema, adherencia (si se infiere), etc.).
Alertas y Recomendaciones (basadas en el análisis de `medical_history`): (Conclusión general sobre el estado de salud del paciente según las consultas, posibles riesgos identificados, y si se desprenden recomendaciones generales del análisis consolidado de las consultas).
(Si no hay datos en `medical_history.Records`, esta sección debe indicar "No es posible realizar análisis longitudinal sin historial de consultas médicas".)

E. RESULTADOS DE EXÁMENES COMPLEMENTARIOS (Estudios y Laboratorios)
(Basado en `exam_results.Records`. Si `exam_results` o `exam_results.Records` es nulo o vacío, indicar "No hay resultados de exámenes disponibles".)
(Basado en `lab_results.Records`. Si `lab_results` o `lab_results.Records` es nulo o vacío, indicar "No hay resultados de laboratorios disponibles".)

Para cada tipo de examen (agrupado por `ExamType.Type`) presente en `exam_results.Records`:
Presenta la información agrupada por el `ExamType.Type`. Para cada examen dentro de ese tipo:

[NOMBRE DEL TIPO DE EXAMEN - Ej: ULTRASONIDO PARTES BLANDAS]
  - Fecha del Examen: (Extraer de `Date`, formateada dd/mm/aaaa)
  - ID del Examen (referencial): (Extraer de `ID`)
  - Código del Examen (referencial): (Extraer de `ExamType.Code`)
  - Unidad (referencial): (Extraer de `ExamType.Unit`)
  - Hallazgos Principales: (Analizar el contenido de `ExamResults`. Este campo contiene HTML. Extrae el texto significativo, elimina las etiquetas HTML y resume los hallazgos clave y la conclusión si está presente. Si el contenido es muy extenso, enfócate en la sección de conclusión o hallazgos principales. Sé conciso y claro.)

Ejemplo de cómo debería verse esta sección E: para el caso de Examenes

E. RESULTADOS DE EXÁMENES COMPLEMENTARIOS (Estudios y Laboratorios)

ULTRASONIDO PARTES BLANDAS
  - Fecha del Examen: 19/01/2024
  - ID del Examen: 6681
  - Código del Examen: ULT0516JS
  - Unidad: Ultrasonido
  - Hallazgos Principales: Exploración región base del pene. Visualización de capas en piel, musculares y tejido adiposo sin alteraciones. Se evidencia L.O.E., redondeada, mixta, a predominio líquido, con grumos, de 4 x 6 mm, en plano superficial. No se observa neoformación vascular. Conclusión: Signos ecográficos sugerentes de absceso en recidiva.

Ejemplo de cómo debería verse esta sección E: para el caso de Laboratorio
  - Fecha del Examen: 19/01/2024
  - ID del Examen: 6681
  - UROANALISIS -> EX. ORINA COMPLETA -> EX. MACROSCOPICO [COLOR] : Amarillo (Unidad si se tiene)
  - UROANALISIS -> EX. ORINA COMPLETA -> EX. MACROSCOPICO [CANTIDAD] : Escasas (Unidad si se tiene)

Formato de Salida:
El resultado debe ser un texto bien estructurado, claro y profesional, emulando la formalidad y detalle de un resumen clínico. No incluyas esta sección de "Instrucciones" en la salida final, solo el análisis clínico.

Nota Importante:
La información del paciente es sensible. El análisis debe centrarse en los datos clínicos y evitar juicios o información no pertinente. Asegúrate de manejar correctamente los casos donde los datos (`medical_history`, `exam_results` o sus `Records`) puedan ser nulos o vacíos, indicando "No disponible" o una frase similar en lugar de generar un error.
"""

# --- Interfaz de Streamlit ---

st.set_page_config(page_title="CRM SUGOS HM & Exámenes & Laboratorios v0.0.3", layout="wide")
st.title("CRM SUGOS HM & Exámenes & Laboratorios v0.0.3")
st.markdown("""
**Seleccione Entorno/Cliente**, ingrese **credenciales API** y la **Cédula**.
- El sistema consultará **Historias Médicas (HMs)** - **Resultados de Exámenes** y **Resultados de Laboratorios**.
- Luego, podrá generar un **Análisis Clínico Estructurado** utilizando IA Generativa.
""")

# --- Inicializar Flags y Estado ---
if 'kpi_run_processed' not in st.session_state:
    st.session_state.kpi_run_processed = False
if 'kpi_clear_password_input' not in st.session_state:
    st.session_state.kpi_clear_password_input = False
if 'kpi_data' not in st.session_state: # Para almacenar los datos de Historias Médicas
    st.session_state.kpi_data = None
if 'exam_data' not in st.session_state: # Para almacenar los datos de Exámenes
    st.session_state.exam_data = None
if 'lab_data' not in st.session_state: # Para almacenar los datos de Laboratorios
    st.session_state.lab_data = None
if 'clinical_analysis_text' not in st.session_state: # Para almacenar el análisis del LLM
    st.session_state.clinical_analysis_text = None
if 'gemini_api_key_verified' not in st.session_state:
    st.session_state.gemini_api_key_verified = False


# --- Cargar Configuraciones de Entorno ---
selected_config = None
ENVIRONMENT_CONFIGS = {}
try:
    if hasattr(st.secrets, 'items'):
        all_secrets = st.secrets.items()
    else:
        all_secrets = [(key, st.secrets[key]) for key in st.secrets.keys()]

    for section_key, section_content in all_secrets:
        if isinstance(section_content, dict) and section_content.get('display_name') and section_content.get('api_base_url'):
            ENVIRONMENT_CONFIGS[section_content['display_name']] = section_key

    if not ENVIRONMENT_CONFIGS:
        st.sidebar.error("Error: No se encontraron configuraciones de entorno válidas en secrets.toml.")
        st.stop()

    sorted_display_names = sorted(ENVIRONMENT_CONFIGS.keys())
    selected_display_name = st.sidebar.selectbox(
        "Seleccionar Entorno/Cliente:",
        options=sorted_display_names,
        index=0,
        key="kpi_env_select"
    )
    selected_secret_key = ENVIRONMENT_CONFIGS[selected_display_name]
    selected_config = st.secrets[selected_secret_key]

except AttributeError:
    st.sidebar.error("Error: Fallo al acceder a st.secrets. Asegúrese de que el archivo secrets.toml exista y sea accesible.")
    st.stop()
except Exception as e:
    st.sidebar.error(f"Error crítico cargando la configuración: {e}")
    st.stop()

# --- Verificación de API Key de Gemini ---
google_api_key = st.secrets.get("GOOGLE_API_KEY")
if google_api_key:
    st.session_state.gemini_api_key_verified = True
else:
    st.sidebar.error("❌ Falta 'GOOGLE_API_KEY' en st.secrets.")
    st.sidebar.markdown("El análisis con IA no estará disponible.")
    st.session_state.gemini_api_key_verified = False


# --- Inputs para Credenciales ---
st.sidebar.divider()
st.sidebar.header("Credenciales API Entorno")
default_user = st.secrets.get("api_credentials", {}).get("username", "")
default_pass = st.secrets.get("api_credentials", {}).get("password", "")

input_api_username = st.sidebar.text_input(
    "Usuario API",
    value=default_user,
    key="kpi_api_user"
)

if st.session_state.kpi_clear_password_input:
    st.session_state.kpi_api_pass = ""
    st.session_state.kpi_clear_password_input = False

input_api_password = st.sidebar.text_input(
    "Contraseña API",
    value=default_pass,
    type="password",
    key="kpi_api_pass"
)
st.sidebar.caption("Credenciales para el entorno CRM seleccionado.")

# --- Parámetros de Consulta ---
col1_params, col2_params = st.columns(2)
with col1_params:
    st.subheader("Consulta de Datos del Paciente")
    input_country_id_str = st.text_input(
        "Cédula:",
        placeholder="Número de Cédula 12345678",
        key="kpi_country_id_input"
    )

with col2_params:
    st.subheader("Modelo IA (para Análisis)")
    model_options = ['gemini-2.5-pro-exp-03-25', 'gemini-2.5-flash-preview-04-17','gemini-1.5-flash-latest', 'gemini-1.5-pro-latest']
    selected_model_name = st.selectbox(
        "Modelo Gemini:",
        options=model_options,
        index=0, # Default to flash
        key="llm_model_select",
        help="Selecciona el modelo Gemini para generar el análisis clínico."
    )


# --- Botón de Acción para Obtener KPIs y Exámenes ---
st.divider()
process_data_button_pressed = st.button(
    "1. Obtener Historias Médicas y Exámenes",
    key="kpi_submit_button"
)

if process_data_button_pressed:
    st.session_state.kpi_data = None
    st.session_state.exam_data = None
    st.session_state.clinical_analysis_text = None

    if not selected_config:
        st.error("Error crítico: No hay configuración de entorno seleccionada.")
        st.stop()

    current_api_user = st.session_state.kpi_api_user
    current_api_pass = st.session_state.kpi_api_pass

    if not current_api_user or not current_api_pass:
        st.warning("⚠️ Ingrese Usuario y Contraseña API.")
        st.session_state.kpi_clear_password_input = True
        st.stop()

    current_country_id_str = st.session_state.kpi_country_id_input
    if not current_country_id_str:
        st.warning("⚠️ Ingrese El Número de Cédula")
        st.stop()

    current_country_id = current_country_id_str.strip()
    # No se convierte a int aquí, la API puede esperar string o int.
    # La función get_kpi_data y get_exam_data lo enviarán tal cual.
    # La validación de si debe ser numérico o alfanumérico dependerá de la API.
    # Si la API requiere estrictamente un int, convertir aquí:
    # try:
    #     current_country_id_for_api = int(current_country_id)
    # except ValueError:
    #     st.warning("⚠️ La cédula debe ser un número entero si la API lo requiere así.")
    #     st.stop()
    # else:
    #    current_country_id_for_api = current_country_id # si puede ser alfanumérico

    st.session_state.kpi_clear_password_input = True
    st.info(f"Iniciando consulta de datos para la Cédula: {current_country_id}")

    with st.spinner("Autenticando con API del Entorno..."):
        token = get_api_token(current_api_user, current_api_pass, selected_config)

    if token:
        st.success(f"Autenticación API Entorno exitosa para {selected_config.get('display_name', 'entorno')}.")
        # Obtener Historias Médicas
        with st.spinner(f"Obteniendo HMs para Cédula: {current_country_id}..."):
            raw_kpi_data = get_kpi_data(token, current_country_id, selected_config)

        if raw_kpi_data is not None:
            st.session_state.kpi_data = raw_kpi_data
            st.success("Historias Médicas (HMs) obtenidas exitosamente.")
            st.subheader("Respuesta JSON de HMs (Datos Crudos):")
            try:
                pretty_json_kpi = json.dumps(raw_kpi_data, indent=2, ensure_ascii=False)
                with st.expander("Ver/Ocultar JSON de HMs", expanded=False):
                    st.code(pretty_json_kpi, language='json')
            except Exception as e:
                st.error(f"No se pudo formatear el JSON de HMs para mostrar: {e}")
                st.text(raw_kpi_data)
        else:
            st.warning("No se pudieron obtener las HMs o la respuesta estaba vacía. Se continuará con exámenes si es posible.")
            st.session_state.kpi_data = None # Asegurar que es None

        # Obtener Resultados de Exámenes
        with st.spinner(f"Obteniendo Resultados de Exámenes para Cédula: {current_country_id}..."):
            raw_exam_data = get_exam_data(token, current_country_id, selected_config)

        if raw_exam_data is not None:
            st.session_state.exam_data = raw_exam_data
            st.success("Resultados de Exámenes obtenidos exitosamente.")
            st.subheader("Respuesta JSON de Exámenes (Datos Crudos):")
            try:
                pretty_json_exam = json.dumps(raw_exam_data, indent=2, ensure_ascii=False)
                with st.expander("Ver/Ocultar JSON de Exámenes", expanded=False):
                    st.code(pretty_json_exam, language='json')
            except Exception as e:
                st.error(f"No se pudo formatear el JSON de Exámenes para mostrar: {e}")
                st.text(raw_exam_data)
        else:
            st.warning("No se pudieron obtener los Resultados de Exámenes o la respuesta estaba vacía.")
            st.session_state.exam_data = None # Asegurar que es None

        # Obtener Resultados de Laboratorios
        with st.spinner(f"Obteniendo Resultados de Exámenes para Cédula: {current_country_id}..."):
            raw_lab_data = get_lab_data(token, current_country_id, selected_config)

        if raw_lab_data is not None:
            st.session_state.lab_data = raw_lab_data
            st.success("Resultados de Laboratorio obtenidos exitosamente.")
            st.subheader("Respuesta JSON de Laboratorio (Datos Crudos):")
            try:
                pretty_json_lab = json.dumps(raw_lab_data, indent=2, ensure_ascii=False)
                with st.expander("Ver/Ocultar JSON de Laboratorio", expanded=False):
                    st.code(pretty_json_lab, language='json')
            except Exception as e:
                st.error(f"No se pudo formatear el JSON de Laboratorio para mostrar: {e}")
                st.text(raw_exam_data)
        else:
            st.warning("No se pudieron obtener los Resultados de Laboratorio o la respuesta estaba vacía.")
            st.session_state.exam_data = None # Asegurar que es None

        if st.session_state.kpi_data is None and st.session_state.exam_data is None and st.session_state.lab_data is None:
            st.error("No se pudo obtener información de Historias Médicas ni de Exámenes ni de Laboratorios.")
            st.session_state.kpi_run_processed = False
        else:
            st.session_state.kpi_run_processed = True
    else:
        st.error("Fallo en la autenticación API del Entorno. No se puede continuar.")
        st.session_state.kpi_run_processed = False
        st.session_state.kpi_data = None
        st.session_state.exam_data = None
        st.session_state.lab_data = None


# --- Botón y Lógica para Generar Análisis Clínico con LLM ---
if st.session_state.kpi_data or st.session_state.exam_data or st.session_state.lab_data: # Si tenemos al menos uno de los dos
    st.divider()
    st.subheader("Análisis Clínico con IA Generativa")

    if not st.session_state.gemini_api_key_verified:
        st.warning("La API Key de Google Gemini no está configurada en los secretos. El análisis con IA no está disponible.")
    else:
        if st.button("2. Generar Análisis Clínico con IA", key="generate_analysis_button"):
            st.session_state.clinical_analysis_text = None # Limpiar análisis previo

            medical_history_kpis = None
            if st.session_state.kpi_data:
                medical_history_kpis = st.session_state.kpi_data.get("data", {}).get("kpis", None)
                if not medical_history_kpis:
                    st.warning("La estructura del JSON de HMs no contiene 'data.kpis'. Las HMs no se incluirán en el análisis si la estructura es incorrecta.")
                    # st.json(st.session_state.kpi_data) # Mostrar JSON problemático

            exam_results_kpis = None
            if st.session_state.exam_data:
                exam_results_kpis = st.session_state.exam_data.get("data", {}).get("kpis", None)
                if not exam_results_kpis:
                    st.warning("La estructura del JSON de Exámenes no contiene 'data.kpis'. Los exámenes no se incluirán en el análisis si la estructura es incorrecta.")
                    # st.json(st.session_state.exam_data) # Mostrar JSON problemático

            lab_results_kpis = None
            if st.session_state.lab_data:
                lab_results_kpis = st.session_state.lab_data.get("data", {}).get("kpis", None)
                if not lab_results_kpis:
                    st.warning("La estructura del JSON de Laboratorios no contiene 'data.kpis'. Los Laboratorios no se incluirán en el análisis si la estructura es incorrecta.")
                    # st.json(st.session_state.lab_data) # Mostrar JSON problemático

            if not medical_history_kpis and not exam_results_kpis and not lab_results_kpis:
                st.error("No hay datos válidos de Historias Médicas ni de Exámenes para enviar al LLM.")
            else:
                # Crear el JSON combinado para el LLM
                combined_data_for_llm = {
                    "medical_history": medical_history_kpis, # Puede ser None
                    "exam_results": exam_results_kpis,      # Puede ser None
                    "lab_results": lab_results_kpis      # Puede ser None
                }

                with st.spinner(f"Generando análisis clínico con {st.session_state.llm_model_select}... Esto puede tardar unos minutos."):
                    analysis_result = generate_clinical_analysis_with_llm(
                        combined_data_for_llm,
                        st.session_state.llm_model_select,
                        PROMPT_INSTRUCTIONS_TEMPLATE,
                        google_api_key
                    )
                if analysis_result:
                    st.session_state.clinical_analysis_text = analysis_result
                    st.success("Análisis clínico generado exitosamente.")
                else:
                    st.error("Fallo al generar el análisis clínico con el LLM.")

# Mostrar el análisis clínico si fue generado
if st.session_state.clinical_analysis_text:
    st.divider()
    st.subheader("Resultado del Análisis Clínico:")
    st.markdown(st.session_state.clinical_analysis_text)


# --- Pie de página ---
st.markdown("---")
st.caption(f"CRM SUGOS HM & Exámenes & Laboratorios v0.0.3")