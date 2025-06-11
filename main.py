import firebase_functions
from firebase_functions import https_fn
import pandas as pd
import pdfplumber
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import tempfile
import os
import json
from werkzeug.utils import secure_filename

def unir_columnas_vacante(row):
    """Unir todas las columnas de una vacante en un solo string"""
    return ' '.join([str(valor) for valor in row if pd.notnull(valor)])

def extraer_texto_pdf(archivo_path):
    """Extraer texto de un archivo PDF"""
    try:
        with pdfplumber.open(archivo_path) as pdf:
            texto = ''
            for pagina in pdf.pages:
                texto += pagina.extract_text() or ''
        return texto
    except Exception as e:
        return f"Error al procesar PDF: {str(e)}"

def calcular_similitud(texto_cv, texto_vacante):
    """Calcular similitud entre CV y vacante usando TF-IDF y cosine similarity"""
    try:
        vectorizer = TfidfVectorizer().fit([texto_cv, texto_vacante])
        vectores = vectorizer.transform([texto_cv, texto_vacante])
        return float(cosine_similarity(vectores[0], vectores[1])[0][0])
    except Exception as e:
        return 0.0

@https_fn.on_request()
def api(req: https_fn.Request) -> https_fn.Response:
    """Función principal que maneja todas las peticiones de la API"""
    
    # Configurar CORS
    if req.method == 'OPTIONS':
        return https_fn.Response(
            status=200,
            headers={
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type',
            }
        )
    
    # Configurar headers CORS para todas las respuestas
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Content-Type': 'application/json'
    }
    
    try:
        if req.path == '/api/ejemplo':
            return crear_archivos_ejemplo(headers)
        elif req.path == '/api/match':
            return procesar_matching(req, headers)
        else:
            return https_fn.Response(
                json.dumps({'error': 'Endpoint no encontrado'}),
                status=404,
                headers=headers
            )
    except Exception as e:
        return https_fn.Response(
            json.dumps({'error': f'Error interno: {str(e)}'}),
            status=500,
            headers=headers
        )

def crear_archivos_ejemplo(headers):
    """Crear archivos de ejemplo"""
    try:
        # Crear vacantes de ejemplo
        vacantes_ejemplo = [
            {
                'Título': 'Desarrollador Python Senior',
                'Descripción': 'Desarrollo de aplicaciones web con Python, Django y bases de datos',
                'Requisitos': 'Python, Django, SQL, Git, 3+ años experiencia',
                'Salario': '40000-60000 USD'
            },
            {
                'Título': 'Analista de Datos',
                'Descripción': 'Análisis de datos y creación de reportes',
                'Requisitos': 'Python, Pandas, SQL, Excel, PowerBI',
                'Salario': '35000-50000 USD'
            },
            {
                'Título': 'Desarrollador Frontend',
                'Descripción': 'Desarrollo de interfaces de usuario',
                'Requisitos': 'JavaScript, React, HTML, CSS, Git',
                'Salario': '30000-45000 USD'
            }
        ]
        
        df_vacantes = pd.DataFrame(vacantes_ejemplo)
        
        return https_fn.Response(
            json.dumps({
                'success': True,
                'message': 'Archivos de ejemplo creados',
                'vacantes': vacantes_ejemplo
            }),
            status=200,
            headers=headers
        )
        
    except Exception as e:
        return https_fn.Response(
            json.dumps({'error': f'Error creando archivos: {str(e)}'}),
            status=500,
            headers=headers
        )

def procesar_matching(req, headers):
    """Procesar matching de CVs con vacantes"""
    try:
        # Verificar que sea POST
        if req.method != 'POST':
            return https_fn.Response(
                json.dumps({'error': 'Método no permitido'}),
                status=405,
                headers=headers
            )
        
        # Obtener datos del formulario
        form_data = req.form
        files = req.files
        
        if 'vacantes' not in files:
            return https_fn.Response(
                json.dumps({'error': 'No se proporcionó archivo de vacantes'}),
                status=400,
                headers=headers
            )
        
        vacantes_file = files['vacantes']
        if vacantes_file.filename == '':
            return https_fn.Response(
                json.dumps({'error': 'No se seleccionó archivo de vacantes'}),
                status=400,
                headers=headers
            )
        
        # Guardar archivo de vacantes temporalmente
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as temp_vacantes:
            vacantes_file.save(temp_vacantes.name)
            vacantes_path = temp_vacantes.name
        
        # Leer vacantes
        vacantes_df = pd.read_excel(vacantes_path)
        vacantes_df['texto_vacante'] = vacantes_df.apply(unir_columnas_vacante, axis=1)
        
        # Procesar CVs
        cvs = []
        cv_files = files.getlist('cvs')
        
        for file in cv_files:
            if file.filename != '' and file.filename.lower().endswith('.pdf'):
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_cv:
                    file.save(temp_cv.name)
                    cv_path = temp_cv.name
                
                texto = extraer_texto_pdf(cv_path)
                cvs.append({
                    'nombre_archivo': secure_filename(file.filename),
                    'texto': texto
                })
                
                # Limpiar archivo temporal
                os.unlink(cv_path)
        
        if not cvs:
            return https_fn.Response(
                json.dumps({'error': 'No se proporcionaron CVs válidos'}),
                status=400,
                headers=headers
            )
        
        # Calcular matches
        resultados = []
        for idx_vac, vacante in vacantes_df.iterrows():
            for cv in cvs:
                puntaje = calcular_similitud(cv['texto'], vacante['texto_vacante'])
                resultados.append({
                    'vacante_id': int(idx_vac),
                    'vacante_titulo': str(vacante.iloc[0]) if len(vacante) > 0 else f'Vacante {idx_vac}',
                    'cv_nombre': cv['nombre_archivo'],
                    'puntaje': round(puntaje * 100, 2),
                    'estado': 'Excelente' if puntaje > 0.8 else 'Bueno' if puntaje > 0.6 else 'Regular' if puntaje > 0.4 else 'Bajo'
                })
        
        # Ordenar por puntaje
        resultados.sort(key=lambda x: x['puntaje'], reverse=True)
        
        # Limpiar archivo temporal de vacantes
        os.unlink(vacantes_path)
        
        return https_fn.Response(
            json.dumps({
                'success': True,
                'resultados': resultados,
                'total_cvs': len(cvs),
                'total_vacantes': len(vacantes_df)
            }),
            status=200,
            headers=headers
        )
        
    except Exception as e:
        return https_fn.Response(
            json.dumps({'error': f'Error en el procesamiento: {str(e)}'}),
            status=500,
            headers=headers
        ) 