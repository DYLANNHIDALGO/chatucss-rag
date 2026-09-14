import os
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="UCSS Chatbot AI")

# Servir archivos estáticos y plantillas
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

from rag_engine import init_rag_chain

rag_chain = None

@app.on_event("startup")
async def startup_event():
    global rag_chain
    print("Iniciando motor RAG e indexando documentos...")
    rag_chain = init_rag_chain()
    print("¡Base de datos vectorial y motor RAG listos!")

class QueryRequest(BaseModel):
    question: str

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    # Sintaxis compatible con las últimas versiones de Starlette/FastAPI
    return templates.TemplateResponse(request=request, name="index.html")

@app.post("/api/chat")
async def chat_endpoint(payload: QueryRequest):
    if not rag_chain:
        return JSONResponse(
            status_code=503,
            content={"answer": "El servidor se está iniciando, intenta en unos segundos."}
        )
    
    try:
        answer = await rag_chain.ainvoke(payload.question)
        return {"answer": answer}
    except Exception as e:
        print(f"Error en chat_endpoint: {e}")
        return JSONResponse(
            status_code=500,
            content={"answer": f"Ocurrió un error al procesar tu consulta: {str(e)}"}
        )