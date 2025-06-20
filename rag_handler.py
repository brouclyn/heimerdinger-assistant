# Fichier : rag_handler.py
# Description : Version avancée avec un meilleur découpage et le MultiQueryRetriever.

import streamlit as st
from langchain_community.document_loaders import DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain_google_genai import GoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.retrievers.multi_query import MultiQueryRetriever
import os

FAISS_INDEX_PATH = "faiss_index"

def create_vector_store():
    """Charge les documents, les divise, crée les embeddings et sauvegarde l'index FAISS."""
    
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("Clé API Gemini non trouvée. Veuillez la configurer.")
        st.stop()
    
    st.write("Démarrage de l'indexation de la base de connaissances...")
    
    # Charge les .txt ET les .pdf
    loader = DirectoryLoader('./knowledge_base/', glob="**/*[.txt,.pdf]")
    documents = loader.load()
    st.write(f"{len(documents)} document(s) chargé(s).")

    # Un meilleur découpage pour garder plus de contexte entre les morceaux
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=150)
    texts = text_splitter.split_documents(documents)
    st.write(f"Les documents ont été divisés en {len(texts)} morceaux (chunks).")

    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=st.secrets["GEMINI_API_KEY"])
    
    try:
        db = FAISS.from_documents(texts, embeddings)
        db.save_local(FAISS_INDEX_PATH)
        st.success("La base de connaissances a été créée et sauvegardée avec succès !")
    except Exception as e:
        st.error(f"Une erreur est survenue lors de la création de la base de données vectorielle : {e}")


def query_rag_system(question: str) -> str:
    """Interroge le système RAG pour obtenir une réponse basée sur les documents."""

    if "GEMINI_API_KEY" not in st.secrets:
        return "Erreur : Clé API non configurée."
    
    if not os.path.exists(FAISS_INDEX_PATH):
        return "Erreur : La base de connaissances (index FAISS) n'a pas encore été créée. Veuillez l'indexer d'abord."

    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=st.secrets["GEMINI_API_KEY"])
    db = FAISS.load_local(FAISS_INDEX_PATH, embeddings, allow_dangerous_deserialization=True)
    llm = GoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=st.secrets["GEMINI_API_KEY"], temperature=0.3)

    # On utilise le MultiQueryRetriever pour une recherche plus intelligente
    retriever_from_llm = MultiQueryRetriever.from_llm(
        retriever=db.as_retriever(search_kwargs={"k": 5}), llm=llm
    )
    
    # Notre Prompt Template en français pour guider l'IA
    prompt_template = """
    Contexte:
    {context}
    Basé **uniquement** sur le contexte ci-dessus, réponds de manière détaillée et en français à la question suivante.
    Si le contexte ne contient pas la réponse, dis simplement "D'après mes documents, je n'ai pas d'information à ce sujet.".
    
    Question: {question}
    
    Réponse en français:"""
    
    QA_CHAIN_PROMPT = PromptTemplate.from_template(prompt_template)

    # Création de la chaîne de Question/Réponse
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever_from_llm, # On utilise notre nouveau retriever intelligent
        return_source_documents=True,
        chain_type_kwargs={"prompt": QA_CHAIN_PROMPT} 
    )

    # On exécute la chaîne et on récupère le résultat
    result = qa_chain.invoke({"query": question})

    # On affiche les sources dans le terminal pour le débogage
    print("\n--- Documents récupérés pour la question ---")
    for doc in result['source_documents']:
        page_num = doc.metadata.get('page', '?')
        source_file = os.path.basename(doc.metadata.get('source', 'Inconnue'))
        print(f"  > [Fichier: {source_file}, Page: {page_num}] : \"{doc.page_content[:250].strip()}...\"")
    print("------------------------------------------\n")

    return result["result"]