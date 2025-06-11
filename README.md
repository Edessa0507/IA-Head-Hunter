# 🚀 IA Head Hunter - Carpeta FINAL para Firebase

## 📁 Estructura de archivos

```
FINAL/
├── firebase.json              # ✅ Configuración de Firebase
├── functions/
│   ├── main.py                # ✅ Firebase Functions (backend)
│   └── requirements.txt       # ✅ Dependencias para Functions
├── public/
│   └── index.html             # ✅ Interfaz web completa
└── README.md                  # ✅ Este archivo
```

## 🎯 Instrucciones de Deploy

### 1. Instalar Firebase CLI

```bash
npm install -g firebase-tools
```

### 2. Inicializar Firebase

```bash
firebase login
firebase init
```

**Seleccionar:**

- ✅ **Hosting** (para la interfaz web)
- ✅ **Functions** (para el backend)
- ✅ **Python 3.11** (runtime)

### 3. Configurar OpenAI (Opcional)

```bash
firebase functions:config:set openai.api_key="tu-api-key-de-openai"
```

### 4. Hacer Deploy

```bash
firebase deploy
```

## 🌐 URLs después del deploy

- **Aplicación principal:** `https://tu-proyecto.web.app`
- **API Functions:** `https://tu-proyecto.cloudfunctions.net/api`

## 🤖 Funcionalidades incluidas

### ✅ Matching de CVs

- Subida de archivos Excel con vacantes
- Subida múltiple de CVs en PDF
- Análisis automático con IA (TF-IDF + Cosine Similarity)
- Ranking de candidatos por compatibilidad

### ✅ Chatbot con IA

- Chat interactivo para evaluación de candidatos
- Análisis detallado de CVs
- Generación de preguntas para entrevistas
- Comparación de múltiples candidatos
- Sugerencias de mejora

### ✅ Análisis avanzado

- Identificación de fortalezas y debilidades
- Evaluación de experiencia relevante
- Recomendaciones específicas
- Preguntas personalizadas para entrevistas

## 🔧 Comandos útiles

```bash
# Ver logs de Functions
firebase functions:log

# Probar localmente
firebase emulators:start

# Actualizar solo Functions
firebase deploy --only functions

# Actualizar solo Hosting
firebase deploy --only hosting
```

## ⚠️ Notas importantes

- **Sin API key de OpenAI:** El chatbot funcionará en modo simulado
- **Con API key de OpenAI:** Funcionalidad completa de IA
- **Archivos temporales:** Se limpian automáticamente
- **Límites:** Firebase Functions tiene límites de tiempo y memoria

## 🎉 ¡Listo para revolucionar el reclutamiento!

Tu IA Head Hunter está completamente configurado y listo para usar.
