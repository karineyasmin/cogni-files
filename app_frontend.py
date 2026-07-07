from __future__ import annotations
from typing import Any, Dict, List, Optional
import streamlit as st
import requests
from requests import Response

# Configuração da página do Streamlit
st.set_page_config(page_title="Tutor Acadêmico Local", page_icon="📚", layout="wide")

# Constantes de configuração e endpoints da API local
BASE_URL: str = "http://localhost:8000/api/v1"
UPLOAD_URL: str = f"{BASE_URL}/documents/upload"
CHAT_URL: str = f"{BASE_URL}/chat/query"

st.title("📚 Tutor Acadêmico RAG 100% Local")
st.subheader("Estude seus documentos de forma privada e offline com Llama 3.2")

# -----------------------------------------------------------------------------
# SIDEBAR - Gerenciamento de Coleções e Upload
# -----------------------------------------------------------------------------
with st.sidebar:
    st.header("📁 Painel de Controle")

    collection_name: str = st.text_input(
        "Nome da Coleção de Estudos",
        value="Analise_Preditiva",
        help="Evite caracteres especiais na criação, o backend irá sanitizar automaticamente.",
    )

    st.divider()

    st.subheader("📤 Upload de Material")
    uploaded_file: Optional[Any] = st.file_uploader(
        "Selecione um arquivo PDF", type=["pdf"]
    )

    if st.button("Processar e Indexar Documento", use_container_width=True):
        if uploaded_file is not None and collection_name:
            with st.spinner(
                "Extraindo textos e indexando chunks localmente... Isso pode levar alguns segundos."
            ):
                try:
                    # Preparação estrita dos payloads e mutipart/form-data
                    files: Dict[str, tuple[str, bytes, str]] = {
                        "file": (
                            uploaded_file.name,
                            uploaded_file.getvalue(),
                            "application/pdf",
                        )
                    }
                    data: Dict[str, str] = {"collection_name": collection_name}

                    response: Response = requests.post(
                        UPLOAD_URL, files=files, data=data
                    )

                    if response.status_code == 201:
                        res_data: Dict[str, Any] = response.json()
                        st.success(f"✓ '{uploaded_file.name}' indexado com sucesso!")
                        st.info(
                            f"Total de chunks criados: {res_data.get('total_chunks', 'N/A')}"
                        )
                    else:
                        st.error(
                            f"Falha no processamento: {response.status_code} - {response.text}"
                        )
                except Exception as e:
                    st.error(f"Erro de conexão com o backend: {str(e)}")
        else:
            st.warning(
                "Por favor, selecione um arquivo PDF e defina um nome de coleção."
            )

# -----------------------------------------------------------------------------
# CORPO PRINCIPAL - Chat Acadêmico
# -----------------------------------------------------------------------------
st.info(f"💬 Sala de Aula Ativa: **{collection_name}**")

# Inicializa o histórico de conversa de forma tipada dentro do State do Streamlit
if "messages" not in st.session_state:
    st.session_state.messages = []

# Força a tipagem estrita da lista de mensagens para o linter estático
chat_history: List[Dict[str, str]] = st.session_state.messages

# Renderiza o histórico de mensagens armazenadas na tela
message: Dict[str, str]
for message in chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Entrada de texto para a dúvida do aluno
prompt: Optional[str] = st.chat_input(
    "Digite sua dúvida com base nos documentos enviados..."
)

if prompt:
    # 1. Mostra a mensagem do usuário no chat imediatamente
    with st.chat_message("user"):
        st.markdown(prompt)

    # Adiciona ao histórico da sessão
    chat_history.append({"role": "user", "content": prompt})

    # 2. Dispara a requisição síncrona para o backend FastAPI
    with st.chat_message("assistant"):
        with st.spinner("Ollama processando resposta com base na CPU local..."):
            try:
                # Converte o histórico para o formato aceito pelo QueryRequest Schema do backend
                formatted_history: List[Dict[str, str]] = [
                    {
                        "role": "user" if m["role"] == "user" else "assistant",
                        "content": m["content"],
                    }
                    for m in chat_history[:-1]
                ]

                payload: Dict[str, Any] = {
                    "collection_name": collection_name,
                    "prompt": prompt,
                    "history": formatted_history,
                }

                # Execução da chamada HTTP com timeout estendido para inferência local em CPU
                response = requests.post(CHAT_URL, json=payload, timeout=180.0)

                if response.status_code == 200:
                    response_json: Dict[str, Any] = response.json()
                    answer: str = str(response_json.get("answer", ""))
                    st.markdown(answer)

                    # Salva a resposta do assistente de IA no histórico da sessão
                    chat_history.append({"role": "assistant", "content": answer})

                    # Expansor técnico para depuração das fontes extraídas do ChromaDB
                    with st.expander("🔍 Ver contextos recuperados do ChromaDB"):
                        retrieved_contexts: List[str] = response_json.get(
                            "retrieved_contexts", []
                        )
                        idx: int
                        ctx: str
                        for idx, ctx in enumerate(retrieved_contexts):
                            st.caption(f"**Trecho {idx + 1}:**")
                            st.code(ctx, language="text")
                else:
                    st.error(
                        f"Erro no motor LLM: {response.status_code} - {response.text}"
                    )

            except requests.exceptions.Timeout:
                st.error(
                    "Tempo limite esgotado. A CPU local demorou mais de 3 minutos para responder."
                )
            except Exception as e:
                st.error(f"Falha de comunicação com o backend: {str(e)}")
