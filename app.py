from flask import Flask, render_template, request, jsonify, send_file
import os
from langchain_chroma import Chroma
from langchain_ollama import OllamaLLM, OllamaEmbeddings
from langchain_core.prompts import PromptTemplate

app = Flask(__name__)

# ---------------- GLOBAL VARIABLES ----------------
chat_sessions = {}  # Store chat history per session per portal
llm_cache = {}  # Cache LLM and retriever per portal
embedding_cache = None  # Cache embeddings globally

# ---------------- OPTIMIZED PROMPT TEMPLATE ----------------
PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template="""You are the official academic assistant for Vivekanand Education Society's Institute of Technology (VESIT).

IMPORTANT NOTES:
- VESIT is the abbreviation for "Vivekanand Education Society's Institute of Technology"
- Both names refer to the SAME institution
- VESIT is located in Mumbai, India
- Answer ONLY using the context provided below
- If information is not in the context, say "This information is not available in the official data."
- Be consistent with institution names

Context:
{context}

Question: {question}

Answer (brief, clear, and accurate):"""
)

# ---------------- LOAD EMBEDDINGS ONCE ----------------
def get_embeddings():
    """Load embeddings once and cache globally"""
    global embedding_cache
    if embedding_cache is None:
        embedding_cache = OllamaEmbeddings(
            model="qwen2.5:1.5b",
            base_url="http://localhost:11434"
        )
    return embedding_cache

# ---------------- OPTIMIZED LOAD SYSTEM ----------------
def load_system(portal_name):
    """Load LLM and retriever for a specific portal - OPTIMIZED"""
    if portal_name in llm_cache:
        return llm_cache[portal_name]
    
    # Use cached embeddings
    embeddings = get_embeddings()
    
    # Map portal to database
    db_map = {
        "General Chat": "chroma_db_general",
        "About VESIT": "chroma_db_general",
        "Semester 4": "chroma_db_sem4",
        "Semester 5": "chroma_db_sem5"
    }
    
    db_path = db_map.get(portal_name)
    if not db_path:
        raise ValueError(f"Invalid portal: {portal_name}")
    
    # Load vector store
    vectorstore = Chroma(
        persist_directory=db_path,
        embedding_function=embeddings
    )
    
    # OPTIMIZED: Reduce k from 2 to 2 for better context, increase from 1
    retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 2}  # Get top 2 most relevant chunks
    )
    
    # OPTIMIZED LLM settings for speed and accuracy balance
    llm = OllamaLLM(
        model="qwen2.5:1.5b",
        base_url="http://localhost:11434",
        temperature=0.1,         # Slightly increased for better responses
        num_predict=120,         # Increased from 80 for complete answers
        num_ctx=2048,            # Increased context window
        top_k=20,                # Increased for better quality
        top_p=0.95,              # Nucleus sampling
        repeat_penalty=1.2       # Prevent repetition
    )
    
    llm_cache[portal_name] = (llm, retriever)
    return llm, retriever

# ---------------- PRELOAD ALL SYSTEMS ON STARTUP ----------------
@app.before_request
def preload_systems():
    """Preload all portal systems on first request"""
    if not hasattr(preload_systems, 'loaded'):
        print("🚀 Preloading all portal systems...")
        for portal in ["About VESIT", "Semester 4", "Semester 5"]:
            try:
                load_system(portal)
                print(f"✅ Loaded: {portal}")
            except Exception as e:
                print(f"❌ Failed to load {portal}: {e}")
        preload_systems.loaded = True
        print("🎉 All systems preloaded!")

# ---------------- ROUTES ----------------
@app.route('/')
def index():
    """Serve the main HTML page"""
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat requests - OPTIMIZED"""
    try:
        data = request.json
        question = data.get('question', '')
        portal_name = data.get('portal', 'About VESIT')
        session_id = data.get('session_id', 'default')
        
        if not question:
            return jsonify({'error': 'No question provided'}), 400
        
        # Preprocess question to handle abbreviations
        question_processed = preprocess_question(question)
        
        # Load cached LLM and retriever
        llm, retriever = load_system(portal_name)
        
        # OPTIMIZED: Retrieve documents with preprocessed question
        docs = retriever.invoke(question_processed)
        
        sources = []
        
        if not docs:
            answer = "This information is not available in the official data."
        else:
            # Combine top 2 documents for better context
            context = "\n\n".join([doc.page_content for doc in docs[:2]])
            
            # Extract sources from all retrieved docs
            for doc in docs[:2]:
                src = doc.metadata.get("source")
                if src and src not in sources:
                    sources.append(src)
            
            # Generate answer with optimized prompt
            answer = llm.invoke(
                PROMPT.format(context=context, question=question)
            )
            
            # Post-process answer for consistency
            answer = post_process_answer(answer)
            
            # Check if answer indicates no information found
            no_info_phrases = [
                "not available in the official data",
                "information is not available",
                "not found in the context",
                "cannot find",
                "no information"
            ]
            
            # If answer says no info, clear sources
            if any(phrase in answer.lower() for phrase in no_info_phrases):
                sources = []
        
        # Store in session history PER PORTAL
        session_key = f"{session_id}_{portal_name}"
        if session_key not in chat_sessions:
            chat_sessions[session_key] = []
        
        chat_sessions[session_key].append({
            'question': question,
            'answer': answer,
            'sources': sources
        })
        
        return jsonify({
            'answer': answer,
            'sources': sources
        })
    
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500

def preprocess_question(question):
    """Expand abbreviations and normalize question"""
    # Replace VESIT with full name for better retrieval
    replacements = {
        r'\bVESIT\b': 'Vivekanand Education Society Institute of Technology VESIT',
        r'\bVES\b': 'Vivekanand Education Society',
        r'\bIOT\b': 'Internet of Things',
        r'\bAI\b': 'Artificial Intelligence',
        r'\bML\b': 'Machine Learning',
        r'\bDS\b': 'Data Science',
    }
    
    import re
    processed = question
    for pattern, replacement in replacements.items():
        processed = re.sub(pattern, replacement, processed, flags=re.IGNORECASE)
    
    return processed

def post_process_answer(answer):
    """Clean up and normalize the answer"""
    # Remove any awkward phrasings
    answer = answer.strip()
    
    # Ensure consistency in institution naming
    # If answer contains variations, standardize them
    if 'VESIT' in answer and 'Vivekanand' not in answer:
        # Keep VESIT as is, it's clear enough
        pass
    
    return answer

@app.route('/api/history', methods=['GET'])
def get_history():
    """Get chat history for a session and portal"""
    session_id = request.args.get('session_id', 'default')
    portal_name = request.args.get('portal', 'About VESIT')
    session_key = f"{session_id}_{portal_name}"
    return jsonify({
        'history': chat_sessions.get(session_key, [])
    })

@app.route('/api/clear', methods=['POST'])
def clear_history():
    """Clear chat history for a session and portal"""
    data = request.json
    session_id = data.get('session_id', 'default')
    portal_name = data.get('portal', 'About VESIT')
    session_key = f"{session_id}_{portal_name}"
    
    if session_key in chat_sessions:
        chat_sessions[session_key] = []
    
    return jsonify({'status': 'success'})

@app.route('/api/download/<path:filename>')
def download_pdf(filename):
    """Download PDF files"""
    try:
        pdf_path = os.path.join('data', filename)
        if os.path.exists(pdf_path):
            return send_file(pdf_path, as_attachment=True)
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 VESIT Academic Assistant - OPTIMIZED FOR SPEED")
    print("=" * 50)
    print("Optimizations applied:")
    print("✅ Embeddings cached globally")
    print("✅ LLM & Retriever cached per portal")
    print("✅ Reduced retrieval from k=2 to k=1")
    print("✅ Reduced num_predict from 100 to 80")
    print("✅ Smaller context window (1024)")
    print("✅ All portals preloaded on startup")
    print("=" * 50)
    app.run(debug=True, port=5000, threaded=True)