import streamlit as st
import requests
import os
from urllib.parse import urljoin, urlencode
import json # Para el pretty print del JSON y para el LLM
import time # Para spinners y posibles timeouts

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

        # No mostrar éxito aquí, se mostrará después de la verificación de API Key
        # st.success(f"Autenticación exitosa para {config.get('display_name', 'el entorno seleccionado')}.")
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
    """Obtiene datos del endpoint de KPI."""
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

    # st.info(f"Consultando KPI URL: {kpi_url}")
    # st.info(f"Con payload: {json.dumps(payload, indent=2)}")

    try:
        response = requests.get(kpi_url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        return data
    except requests.exceptions.HTTPError as e:
        st.error(f"Error HTTP {e.response.status_code} al obtener datos de KPI desde {kpi_url}.")
        try:
            st.error(f"Respuesta del servidor: {e.response.text}")
        except Exception:
            st.error("No se pudo obtener el detalle de la respuesta del servidor.")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error de conexión al obtener datos de KPI desde {kpi_url}: {e}")
        return None
    except json.JSONDecodeError:
        st.error(f"Error decodificando JSON de la respuesta de {kpi_url}. Respuesta recibida:")
        st.code(response.text, language='text')
        return None
    except Exception as e:
        st.error(f"Error inesperado al obtener datos de KPI: {e}")
        return None

# --- FUNCIÓN PARA GEMINI ---
def generate_clinical_analysis_with_llm(kpi_json_data_for_llm, model_name, prompt_instructions_template, gemini_api_key):
    """Genera análisis clínico usando Gemini."""
    try:
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel(model_name)

        # Inyectar el JSON de KPIs en el prompt
        # Asumimos que kpi_json_data_for_llm es el objeto data.kpis
        json_string_for_prompt = json.dumps(kpi_json_data_for_llm, indent=2, ensure_ascii=False)
        full_prompt = prompt_instructions_template.replace("{json_data_placeholder}", json_string_for_prompt)

        # st.subheader("Prompt enviado al LLM (para depuración):")
        # st.text_area("Prompt:", full_prompt, height=300)


        generation_config = genai.GenerationConfig(
            temperature=0.2, # Más determinista para seguir instrucciones
            # top_p=0.9,
            max_output_tokens=8192 # Asegurar que la respuesta no se corte
        )

        response = model.generate_content(
            full_prompt,
            generation_config=generation_config,
            request_options={'timeout': 600} # 10 minutos de timeout
        )
        return response.text

    except genai.types.generation_types.BlockedPromptException as blocked_error:
        st.error("Error: La solicitud al LLM fue bloqueada por políticas de seguridad.")
        try:
            feedback = getattr(blocked_error, 'response', {}).get('prompt_feedback', None)
            if feedback: st.warning(f"Razón del bloqueo: {feedback}")
            elif response and hasattr(response, 'prompt_feedback'): st.warning(f"Feedback: {response.prompt_feedback}")
        except Exception: pass
        return None
    except Exception as e:
        st.error(f"Ocurrió un error durante la generación con el LLM: {e}")
        if hasattr(e, 'message'): st.error(f"Detalle: {e.message}")
        return None

# --- Prompt para Gemini (Instrucciones para el Análisis Clínico) ---
PROMPT_INSTRUCTIONS_TEMPLATE = """
Instrucciones Detalladas para la Generación del Análisis Clínico:

Interpretación del JSON:
Aquí está el JSON con los datos del paciente:
{json_data_placeholder}

Analiza el JSON proporcionado para extraer todos los registros médicos del paciente. Procesa todos los objetos dentro del array "Records".
Consolidación del Historial Médico:

Reúne toda la información relevante de cada registro para construir un historial médico completo y cronológico.
Generación del Análisis Clínico (siguiendo un esquema de referencia tipo PDF):
El informe final debe estructurarse de la siguiente manera. Si alguna información no está disponible en el JSON para un campo específico del esquema de referencia, indícalo claramente (ej. "No disponible en JSON" o "Dato no suministrado").

A. IDENTIFICACIÓN DEL PACIENTE

Nombre: (Extraer de Patient.Name)
Cédula (referencial): (Extraer de Patient.CountryID.).
Número de Atenciones: (Contar el número de registros en Records)
Fechas de Atenciones: (Listar todas las Date de los registros, formateadas dd/mm/aaaa HH:MM AM/PM)

B. ANTECEDENTES (Consolidar de todos los registros, principalmente de History.Description. Buscar patrones o información recurrente.)

Personales: (Condiciones médicas preexistentes, alergias, hábitos, etc., de History.Description y Sickness si es relevante para el historial general).
Familiares: (Condiciones médicas en la familia del paciente, si se menciona en History.Description).
Quirúrgicos: (Intervenciones quirúrgicas previas, si se mencionan en History.Description).
Ginecológicos: (Si se mencionan en History.Description).
Epidemiológicos/Otros: (Inmunizaciones, exposición a enfermedades, viajes, hábitos específicos como tabaquismo (Tabáquicos), alcohol (OH), ocupación, etc., desde History.Description).

C. ORGANIZACIÓN CRONOLÓGICA DE DATOS POR EVENTO DE ATENCIÓN
(Para cada registro en Records dentro del JSON proporcionado):

Consulta [ID del Registro] (Usar el ID principal del registro, ej. "Consulta 2750")
Fecha de consulta: (Usar Date)
Motivo de Consulta: (Usar Reason)
Enfermedad Actual / Padecimiento: (Usar Sickness. Describir la condición que llevó a la consulta).
Signos Vitales: (TAS: VitalSigns.TAS mmHg, TAD: VitalSigns.TAD mmHg, FC: VitalSigns.FC x', Peso: VitalSigns.Weight Kg, Talla: VitalSigns.Size Mts. Indicar "0", "No registrado" o "No aplica" si el valor es 0, null o no es pertinente para la consulta).
Examen Físico: (Usar PhysicalExam.Description. Indicar si está vacío o no aplica. Notar PhysicalExam.Type).
Diagnósticos: (Listar cada diagnóstico de Diagnostics: [ID] - [Name]. Si Diagnostics es null, vacío, o no aplica, indicar "Sin diagnósticos registrados para este evento" o similar).
Exámenes Indicados/Realizados: (Listar cada examen de Exams: [ID] - [Name]. Si Exams es null, vacío, o no aplica, indicar "Sin exámenes indicados/realizados para este evento").
Tratamiento(s), Plan de Acción y Comentarios:
Medicamentos: (Listar cada medicamento de Medicines: [Name] ([Generic], [Code]) - Dosis/Presentación: [Presentation] - Indicaciones: [Indications] - Laboratorio: [Laboratory]. Si Medicines es null o no aplica, indicar "Sin medicamentos recetados para este evento").
Indicaciones Generales/Comentarios: (Usar Comments. Ejemplo: "Reposo por RestDays días", "Uso de epicondilera 15 días").
Días de Reposo: (Usar RestDays si es > 0).

D. GENERACIÓN DE RESUMEN Y ANÁLISIS LONGITUDINAL

Resumen Conciso de la Atención por Evento: (Para cada fecha de atención, resumir brevemente: ej. "dd/mm/aaaa: Consulta por [Motivo principal]. Diagnóstico(s) principal(es): [Diagnósticos]. Tratamiento principal: [Medicamento/Indicación].")
Análisis Longitudinal de Hallazgos Positivos y Negativos:
Condiciones Clínicas Persistentes/Recurrentes: (Identificar condiciones que aparecen en múltiples registros o que se mencionan como crónicas en los antecedentes).
Evolución de Diagnósticos: (Cómo han cambiado, se han resuelto o se han añadido diagnósticos con el tiempo).
Tendencias en Signos Vitales: (Si hay suficientes datos, comentar tendencias en peso, TAS/TAD, etc.).
Respuesta a Tratamientos (si se puede inferir): (Mencionar si se observa mejoría, recurrencia a pesar del tratamiento, o efectos secundarios, basado en Comments o consultas subsecuentes).
Patrones Notables: (Cualquier otro patrón observado: tipos de medicamentos frecuentemente recetados, necesidad de múltiples consultas para un mismo problema, adherencia (si se infiere), etc.).
Alertas y Recomendaciones (basadas en el análisis): (Conclusión general sobre el estado de salud del paciente, posibles riesgos identificados, y si se desprenden recomendaciones generales del análisis consolidado).

Formato de Salida:
El resultado debe ser un texto bien estructurado, claro y profesional, emulando la formalidad y detalle de un resumen clínico. No incluyas esta sección de "Instrucciones" en la salida final, solo el análisis clínico.

Nota Importante:
La información del paciente es sensible. El análisis debe centrarse en los datos clínicos y evitar juicios o información no pertinente.
"""

# --- Interfaz de Streamlit ---

st.set_page_config(page_title="CRM SUGOS MRs v0.0.1", layout="wide")
st.title("CRM SUGOS MRs v0.0.1")
st.markdown("""
**Seleccione Entorno/Cliente**, ingrese **credenciales API** y el **Country ID**.
- El sistema consultará los registros médicos (KPIs).
- Luego, podrá generar un **Análisis Clínico Estructurado** utilizando IA Generativa (Google Gemini).
""")

# --- Inicializar Flags y Estado ---
if 'kpi_run_processed' not in st.session_state:
    st.session_state.kpi_run_processed = False
if 'kpi_clear_password_input' not in st.session_state:
    st.session_state.kpi_clear_password_input = False
if 'kpi_data' not in st.session_state: # Para almacenar los datos del KPI
    st.session_state.kpi_data = None
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
# st.sidebar.divider()
# st.sidebar.subheader("Configuración IA Generativa")
google_api_key = st.secrets.get("GOOGLE_API_KEY")
if google_api_key:
    # st.sidebar.success("✅ API Key de Google Gemini encontrada.")
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
    st.subheader("Parámetros de Consulta de Historias Médicas")
    input_country_id_str = st.text_input(
        "Cédula:",
        placeholder="Número de Cédula 12345678",
        key="kpi_country_id_input"
    )

with col2_params:
    st.subheader("Modelo IA (para Análisis)")
    model_options = ['gemini-2.5-pro-exp-03-25', 'gemini-2.5-flash-preview-04-17','gemini-1.5-flash-latest','gemini-1.5-pro-latest'] # Ajusta según disponibilidad y preferencia
    selected_model_name = st.selectbox(
        "Modelo Gemini:",
        options=model_options,
        index=0,
        key="llm_model_select",
        help="Selecciona el modelo Gemini para generar el análisis clínico."
    )


# --- Botón de Acción para Obtener KPIs ---
st.divider()
process_kpi_button_pressed = st.button(
    "1. Obtener Historias Médicas",
    key="kpi_submit_button"
)

if process_kpi_button_pressed:
    st.session_state.kpi_data = None # Limpiar datos anteriores
    st.session_state.clinical_analysis_text = None # Limpiar análisis anterior

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

    # Permitir que el country_id sea numérico o alfanumérico
    current_country_id = current_country_id_str.strip()
    try:
        current_country_id = int(current_country_id_str.strip())
    except ValueError:
        st.warning("⚠️ La cédula debe ser un número entero.") # Ajustado, puede ser alfanumérico
        st.stop()

    st.session_state.kpi_clear_password_input = True

    st.info(f"Iniciando consulta de Historias Medicas para el Cédula: {current_country_id}")

    with st.spinner("Autenticando con API del Entorno..."):
        token = get_api_token(current_api_user, current_api_pass, selected_config)

    if token:
        st.success(f"Autenticación API Entorno exitosa para {selected_config.get('display_name', 'entorno')}.")
        with st.spinner(f"Obteniendo HMs para Cédula: {current_country_id}..."):
            raw_kpi_data = get_kpi_data(token, current_country_id, selected_config)

        if raw_kpi_data is not None:
            st.session_state.kpi_data = raw_kpi_data # Guardar los datos completos
            st.success("Historias Médicas (HMs) obtenidas exitosamente.")
            st.subheader("Respuesta JSON de HMs (Datos Crudos):")
            try:
                pretty_json = json.dumps(raw_kpi_data, indent=2, ensure_ascii=False)
                with st.expander("Ver/Ocultar JSON completo", expanded=False):
                    st.code(pretty_json, language='json')
            except Exception as e:
                st.error(f"No se pudo formatear el JSON para mostrar: {e}")
                st.text("Datos crudos:")
                st.text(raw_kpi_data)
            st.session_state.kpi_run_processed = True
        else:
            st.error("No se pudieron obtener las HMs o la respuesta estaba vacía.")
            st.session_state.kpi_run_processed = False
            st.session_state.kpi_data = None
    else:
        st.error("Fallo en la autenticación API del Entorno. No se puede continuar.")
        st.session_state.kpi_run_processed = False
        st.session_state.kpi_data = None

# --- Botón y Lógica para Generar Análisis Clínico con LLM ---
if st.session_state.kpi_data:
    st.divider()
    st.subheader("Análisis Clínico con IA Generativa")

    if not st.session_state.gemini_api_key_verified:
        st.warning("La API Key de Google Gemini no está configurada en los secretos. El análisis con IA no está disponible.")
    else:
        if st.button("2. Generar Análisis Clínico con IA", key="generate_analysis_button"):
            st.session_state.clinical_analysis_text = None # Limpiar análisis previo
            # Extraer la parte relevante del JSON para el LLM
            # El prompt espera un JSON que contenga Patient y Records
            kpis_data_for_llm = st.session_state.kpi_data.get("data", {}).get("kpis", None)

            if not kpis_data_for_llm:
                st.error("Error: La estructura del JSON de MRs no contiene 'data.kpis' como se esperaba. No se puede generar el análisis.")
                st.json(st.session_state.kpi_data) # Mostrar el JSON problemático
            else:
                with st.spinner(f"Generando análisis clínico con {st.session_state.llm_model_select}... Esto puede tardar unos minutos."):
                    analysis_result = generate_clinical_analysis_with_llm(
                        kpis_data_for_llm,
                        st.session_state.llm_model_select,
                        PROMPT_INSTRUCTIONS_TEMPLATE,
                        google_api_key # Pasar la API key verificada
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
st.caption(f"CRM SUGOS MRs v0.0.1")