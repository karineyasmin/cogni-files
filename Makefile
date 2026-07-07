.PHONY: help up down restart logs build clean ollama-model

# Comando padrão caso digite apenas 'make'
help:
	@echo "======================================================================"
	@echo "                   COGNIFILES - LOCAL RAG TUTOR                       "
	@echo "======================================================================"
	@echo " Comandos disponíveis:"
	@echo "  make up            - Sobe toda a infraestrutura em segundo plano"
	@echo "  make down          - Derruba todos os containers e limpa a rede"
	@echo "  make restart       - Reinicia os containers aplicando alterações"
	@echo "  make build         - Força a reconstrução das imagens (Docker + uv)"
	@echo "  make logs          - Exibe os logs unificados em tempo real"
	@echo "  make ollama-model  - Baixa o modelo Llama 3.2 dentro do container"
	@echo "  make clean         - Limpa caches locais do Python (.pyc, __pycache__)"
	@echo "======================================================================"

# Sobe os containers em modo daemon (segundo plano)
up:
	docker compose up -d
	@echo "🚀 Ambiente subindo! Acesse o frontend em http://localhost:8501"

# Derruba os containers
down:
	docker compose down

# Força o rebuild das imagens (ótimo se alterar o pyproject.toml ou uv.lock)
build:
	docker compose build --no-cache

# Reinicia a aplicação de forma rápida
restart:
	docker compose restart

# Monitora os logs de todos os serviços (FastAPI, Streamlit, MongoDB, Ollama)
logs:
	docker compose logs -f

# Baixa o modelo Llama de 1B parâmetros direto no volume do container Ollama
ollama-model:
	docker exec -it rag_ollama ollama run llama3.2:1b

# Remove caches locais caso queira rodar algo fora do Docker eventualmente
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	@echo "🧹 Caches locais limpos com sucesso!"