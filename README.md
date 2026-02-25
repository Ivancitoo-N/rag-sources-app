# RAG Sources App 🧠

Una aplicación web de RAG (Retrieval-Augmented Generation) totalmente **local** para consultar fuentes de documentos exclusivas con búsqueda híbrida, generación basada en hechos (CRAG) y citaciones directas.

![Aesthetic Visualization](https://img.shields.io/badge/Design-Glassmorphism-blueviolet)
![Tech](https://img.shields.io/badge/Stack-FastAPI%20%2B%20React-blue)
![Privacy](https://img.shields.io/badge/Privacy-100%25%20Local-green)

## ✨ Características Principales

- **🔍 Búsqueda Híbrida**: Combina búsqueda semántica (ChromaDB + Sentence-Transformers) con búsqueda léxica (BM25) mediante **Reciprocal Rank Fusion (RRF)**.
- **🛡 CRAG (Corrective RAG)**: Evalúa la relevancia de los fragmentos recuperados antes de generar la respuesta para evitar alucinaciones.
- **📄 Extracción de Alta Precisión**: Utiliza **Docling** para procesar PDFs, DOCX y Markdown con una precisión excelente en tablas y estructuras complejas.
- **📁 Colecciones (Multi-Chat)**: Organiza tus documentos en grupos aislados. Las consultas en una colección no tienen acceso a los datos de otra.
- **📍 Citaciones Directas**: Cada respuesta del IA incluye referencias precisas al documento y página de origen.
- **🎨 Interfaz Premium**: Diseño moderno con Glassmorphism, temas oscuros y animaciones fluidas.

## 🛠 Requisitos Previos

- **Python 3.10+**
- **Node.js 18+**
- **Ollama** (opcional, para ejecución local de LLM) o clave de **OpenAI API**.

## 🚀 Instalación Rápida (Windows)

1. **Clonar el repositorio** (o descargar los archivos).
2. **Configurar el entorno**:
   ```bash
   cp backend/.env.example backend/.env
   ```
   Edita `backend/.env` para configurar tu proveedor de LLM (`ollama` o `openai`).
3. **Lanzar la aplicación**:
   Simplemente ejecuta el archivo:
   ```cmd
   start.bat
   ```
   *Este script instalará automáticamente las dependencias, configurará el entorno virtual y lanzará tanto el backend como el frontend en terminales separadas.*

## 📂 Estructura del Proyecto

- `backend/`: API FastAPI, lógica de ingesta, stores de vectores (ChromaDB) y búsqueda híbrida.
- `frontend/`: Interfaz React + Vite + TypeScript con soporte para Drag & Drop.
- `data/`: Almacenamiento local persistente para ChromaDB y el índice BM25.

## ⚙️ Configuración (.env)

| Variable | Descripción | Valor por defecto |
|----------|-------------|-------------------|
| `LLM_PROVIDER` | Proveedor de LLM | `ollama` |
| `OLLAMA_MODEL` | Modelo de Ollama | `llama3.2` |
| `OPENAI_API_KEY` | Key de OpenAI | `sk-...` |
| `CRAG_RELEVANCE_THRESHOLD` | Umbral de relevancia | `0.20` |

## 🛡 Seguridad y Privacidad

Esta aplicación está diseñada para ser **local-first**. Tus documentos nunca salen de tu máquina durante el proceso de ingesta o búsqueda léxica/vectorial. Si usas Ollama, el 100% de la lógica (incluyendo la generación) es privada.

---
*Desarrollado con enfoque en precisión industrial y experiencia de usuario premium.*
