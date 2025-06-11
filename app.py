from flask import Flask, render_template, request, jsonify, send_file
import os
import pandas as pd
import pdfplumber
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import tempfile
import json
from werkzeug.utils import secure_filename

# Chatbot IA (simulado si no hay openai)
try:
    from chatbot import IAHeadHunterChatbot
    chatbot = IAHeadHunterChatbot()
except Exception:
    chatbot = None

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def unir_columnas_vacante(row):
    return ' '.join([str(valor) for valor in row if pd.notnull(valor)])

def extraer_texto_pdf(archivo):
    try:
        with pdfplumber.open(archivo) as pdf:
            texto = ''
            for pagina in pdf.pages:
                texto += pagina.extract_text() or ''
        return texto
    except Exception as e:
        return f"Error al procesar PDF: {str(e)}"

def calcular_similitud(texto_cv, texto_vacante):
    try:
        vectorizer = TfidfVectorizer().fit([texto_cv, texto_vacante])
        vectores = vectorizer.transform([texto_cv, texto_vacante])
        return float(cosine_similarity(vectores[0], vectores[1])[0][0])
    except Exception as e:
        return 0.0

@app.route('/')
def index():
    return send_file(os.path.join('public', 'index.html'))

@app.route('/api/match', methods=['POST'])
def match_cvs():
    try:
        if 'vacantes' not in request.files:
            return jsonify({'error': 'No se proporcionó archivo de vacantes'}), 400
        vacantes_file = request.files['vacantes']
        if vacantes_file.filename == '':
            return jsonify({'error': 'No se seleccionó archivo de vacantes'}), 400
        vacantes_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(vacantes_file.filename))
        vacantes_file.save(vacantes_path)
        vacantes_df = pd.read_excel(vacantes_path)
        vacantes_df['texto_vacante'] = vacantes_df.apply(unir_columnas_vacante, axis=1)
        cvs = []
        for file in request.files.getlist('cvs'):
            if file.filename != '' and file.filename.lower().endswith('.pdf'):
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                texto = extraer_texto_pdf(filepath)
                cvs.append({'nombre_archivo': filename, 'texto': texto})
        if not cvs:
            return jsonify({'error': 'No se proporcionaron CVs válidos'}), 400
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
        resultados.sort(key=lambda x: x['puntaje'], reverse=True)
        os.remove(vacantes_path)
        for cv in cvs:
            cv_path = os.path.join(app.config['UPLOAD_FOLDER'], cv['nombre_archivo'])
            if os.path.exists(cv_path):
                os.remove(cv_path)
        return jsonify({
            'success': True,
            'resultados': resultados,
            'total_cvs': len(cvs),
            'total_vacantes': len(vacantes_df)
        })
    except Exception as e:
        return jsonify({'error': f'Error en el procesamiento: {str(e)}'}), 500

@app.route('/api/ejemplo', methods=['POST'])
def crear_archivos_ejemplo():
    try:
        vacantes_ejemplo = [
            {'Título': 'Desarrollador Python Senior', 'Descripción': 'Desarrollo de aplicaciones web con Python, Django y bases de datos', 'Requisitos': 'Python, Django, SQL, Git, 3+ años experiencia', 'Salario': '40000-60000 USD'},
            {'Título': 'Analista de Datos', 'Descripción': 'Análisis de datos y creación de reportes', 'Requisitos': 'Python, Pandas, SQL, Excel, PowerBI', 'Salario': '35000-50000 USD'},
            {'Título': 'Desarrollador Frontend', 'Descripción': 'Desarrollo de interfaces de usuario', 'Requisitos': 'JavaScript, React, HTML, CSS, Git', 'Salario': '30000-45000 USD'}
        ]
        df_vacantes = pd.DataFrame(vacantes_ejemplo)
        vacantes_path = os.path.join(app.config['UPLOAD_FOLDER'], 'vacantes_ejemplo.xlsx')
        df_vacantes.to_excel(vacantes_path, index=False)
        return jsonify({'success': True, 'message': 'Archivos de ejemplo creados', 'vacantes_path': vacantes_path})
    except Exception as e:
        return jsonify({'error': f'Error creando archivos: {str(e)}'}), 500

@app.route('/api/chat', methods=['POST'])
def chat_with_ai():
    try:
        if not chatbot:
            return jsonify({'success': True, 'response': 'El chatbot IA no está disponible en este entorno.', 'timestamp': pd.Timestamp.now().isoformat()})
        data = request.get_json()
        user_message = data.get('message', '')
        context = data.get('context', {})
        if not user_message:
            return jsonify({'error': 'Mensaje requerido'}), 400
        response = chatbot.chat(user_message, context)
        return jsonify({'success': True, 'response': response, 'timestamp': pd.Timestamp.now().isoformat()})
    except Exception as e:
        return jsonify({'error': f'Error en el chat: {str(e)}'}), 500

@app.route('/api/analyze-cv', methods=['POST'])
def analyze_cv():
    try:
        if not chatbot:
            return jsonify({'success': False, 'error': 'El chatbot IA no está disponible en este entorno.'})
        data = request.get_json()
        cv_text = data.get('cv_text', '')
        job_requirements = data.get('job_requirements', '')
        if not cv_text:
            return jsonify({'error': 'Texto del CV requerido'}), 400
        analysis = chatbot.analyze_cv(cv_text, job_requirements)
        return jsonify({'success': True, 'analysis': analysis})
    except Exception as e:
        return jsonify({'error': f'Error analizando CV: {str(e)}'}), 500

@app.route('/api/compare-candidates', methods=['POST'])
def compare_candidates():
    try:
        if not chatbot:
            return jsonify({'success': False, 'error': 'El chatbot IA no está disponible en este entorno.'})
        data = request.get_json()
        candidates = data.get('candidates', [])
        job_requirements = data.get('job_requirements', '')
        if not candidates:
            return jsonify({'error': 'Lista de candidatos requerida'}), 400
        comparison = chatbot.compare_candidates(candidates, job_requirements)
        return jsonify({'success': True, 'comparison': comparison})
    except Exception as e:
        return jsonify({'error': f'Error comparando candidatos: {str(e)}'}), 500

@app.route('/api/generate-questions', methods=['POST'])
def generate_interview_questions():
    try:
        if not chatbot:
            return jsonify({'success': False, 'error': 'El chatbot IA no está disponible en este entorno.'})
        data = request.get_json()
        cv_text = data.get('cv_text', '')
        job_requirements = data.get('job_requirements', '')
        if not cv_text:
            return jsonify({'error': 'Texto del CV requerido'}), 400
        questions = chatbot.generate_interview_questions(cv_text, job_requirements)
        return jsonify({'success': True, 'questions': questions})
    except Exception as e:
        return jsonify({'error': f'Error generando preguntas: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 