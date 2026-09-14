import os
import json
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_core.documents import Document
from langchain_community.vectorstores import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

def init_rag_chain():
    data_dir = "./data"
    documents = []

    # 1. Cargar PDFs de la carpeta ./data (si existen)
    if os.path.exists(data_dir):
        try:
            pdf_loader = PyPDFDirectoryLoader(data_dir)
            pdf_docs = pdf_loader.load()
            documents.extend(pdf_docs)
        except Exception as e:
            print(f"Aviso al cargar PDFs: {e}")

    # 2. Cargar el JSON de preguntas frecuentes
    json_path = os.path.join(data_dir, "preguntas_frecuentes_ucss.json")
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            faqs = json.load(f)
            for item in faqs:
                content = f"Categoría: {item.get('categoria', 'General')}\nPregunta: {item['pregunta']}\nRespuesta: {item['respuesta']}"
                doc = Document(
                    page_content=content,
                    metadata={"source": "faqs_json", "id": item.get("id")}
                )
                documents.append(doc)

    if not documents:
        raise ValueError("No se encontraron documentos PDF ni el archivo JSON en la carpeta ./data")

    # 3. Embeddings optimizados de Google Gemini (Consumo mínimo de RAM)
    embeddings = GoogleGenerativeAIEmbeddings(
        model="text-embedding-004",
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )
    
    vectorstore = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory="./vectorstore"
    )
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

    # 4. Modelo Gemini
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        temperature=0.1,
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )

    # 5. Prompt de la UCSS
    template = """Eres el asistente virtual oficial de la Universidad Católica Sedes Sapientiae (UCSS).
Responde a la pregunta del usuario basándote únicamente en el siguiente contexto institucional disponible.
Si no encuentras la respuesta en el contexto, indica de forma amable que no dispones de esa información en este momento.

Contexto:
{context}

Pregunta: {question}
Respuesta:"""

    prompt = ChatPromptTemplate.from_template(template)

    # 6. Cadena RAG con LCEL
    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    return rag_chain