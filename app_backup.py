import streamlit as st
import os

from langchain_ollama import OllamaLLM, OllamaEmbeddings
from langchain_chroma import Chroma

from langchain_core.prompts import PromptTemplate

st.markdown(
    "<style>img {max-width: 100%;}</style>",
    unsafe_allow_html=True
)

st.set_page_config(
    page_title="VESIT Academic Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)
st.markdown("""
<style>
    .main {
        background-color: #f8f9fb;
    }

    header {visibility: hidden;}
    
    /* Remove default Streamlit header styling */
    .stApp > header {
        display: none;
    }

    .block-container {
        padding-top: 1rem;
        max-width: 1100px;
    }

    .chat-container {
        background: white;
        border-radius: 10px;
        padding: 1rem;
        border: 1px solid #e0e0e0;
    }
    
    .pdf-attachment {
        background-color: #e8f4f8;
        border: 1px solid #b3d9e6;
        border-radius: 8px;
        padding: 12px;
        margin-top: 10px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    .pdf-link {
        color: #0b3c5d;
        text-decoration: none;
        font-weight: 500;
    }
    
    .pdf-link:hover {
        text-decoration: underline;
    }
    
    .pdf-icon {
        font-size: 1.2rem;
    }
</style>
""", unsafe_allow_html=True)

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ===== Institute Header =====
st.markdown("<br>", unsafe_allow_html=True)

# Better centered logo layout with improved proportions
col1, col2, col3 = st.columns([1, 8, 1])

with col2:
    st.image("static/logo.png", width=600)

# Clean center-aligned text below logo
st.markdown(
    """
    <div style="text-align:center; margin-top:15px; padding: 0 20px;">
        <div style="font-size:1.8rem; font-weight:600; color:#0b3c5d; margin-bottom:8px;">
            Vivekanand Education Society's Institute of Technology
        </div>
        <div style="font-size:1.1rem; color:#444; line-height:1.4;">
            Welcome to VESIT Academic Assistant<br>
            Your AI-powered guide for academic queries and exam preparation
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown("<hr style='margin:25px 0; border:1px solid #e0e0e0;'>", unsafe_allow_html=True)


with st.sidebar:
    st.markdown("### Academic Assistant")
    st.markdown(
        """
        This assistant provides responses based on  
        officially provided academic material.

        **Intended Use**
        - Concept clarification
        - Exam-oriented revision
        - Quick reference

        **Limitations**
        - Not a replacement for faculty guidance
        """
    )
    st.markdown("---")
    st.caption(
        "Vivekanand Education Society's Institute of Technology\n\n"
        "For official confirmation, consult faculty or department notices."
    )

@st.cache_resource
def load_system():
    embeddings = OllamaEmbeddings(
        model="qwen2.5:1.5b",
        base_url="http://localhost:11434"
    )

    vectorstore = Chroma(
        persist_directory="chroma_db",
        embedding_function=embeddings
    )

    retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 3}
)

    llm = OllamaLLM(
        model="qwen2.5:1.5b",
        base_url="http://localhost:11434",
        temperature=0.1
    )

    return llm, retriever

llm, retriever = load_system()


PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template="""
You are the official academic assistant of
Vivekanand Education Society’s Institute of Technology (VESIT).

STRICT RULES (DO NOT BREAK):
- Use ONLY the provided context to answer
- DO NOT guess or expand abbreviations
- DO NOT use general knowledge for institute-related questions
- If the answer is NOT found in the context, clearly say:
  "This information is not available in the official data."

Context:
{context}

Question:
{question}

Answer (professional, official tone):
"""
)


st.markdown('<div class="chat-container">', unsafe_allow_html=True)

for q, a in st.session_state.chat_history:
    with st.chat_message("user"):
        st.write(q)
    with st.chat_message("assistant"):
        st.write(a)

st.markdown('</div>', unsafe_allow_html=True)



question = st.chat_input("Enter your academic question here")

# Initialize variables outside the question block
context = ""
source_pdf = None
pdf_path = None
docs = None


if question:
    with st.chat_message("user"):
        st.write(question)

    with st.chat_message("assistant"):
        with st.spinner("Retrieving relevant academic information..."):

            docs = retriever.invoke(question)

            # ❌ NO CONTEXT → NO LLM
            if not docs:
                answer = "This information is not available in the official data."
                source_pdf = None

            else:
                # ✅ Combine top results (stronger context)
                context = "\n\n".join([doc.page_content for doc in docs[:3]])

                source_pdf = docs[0].metadata.get("source")

                answer = llm.invoke(
                    PROMPT.format(
                        context=context,
                        question=question
                    )
                )

        st.write(answer)

        # 📄 PDF attachment (only if real PDF)
        if source_pdf and source_pdf.lower().endswith(".pdf"):
            pdf_path = os.path.join("data", source_pdf)

            if os.path.exists(pdf_path):
                with open(pdf_path, "rb") as f:
                    st.download_button(
                        label=f"📥 Download {source_pdf}",
                        data=f.read(),
                        file_name=source_pdf,
                        mime="application/pdf"
                    )

    st.session_state.chat_history.append((question, answer))


st.markdown("---")
st.caption(
    "VESIT Academic Assistant • Retrieval-Augmented Generation System"
)
