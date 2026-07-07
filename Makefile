# Define o shell padrão para execução dos comandos
SHELL := /bin/bash

# Variáveis de ambiente padrão para execução do projeto
PYTHONPATH := .
APP_PORT := 8000

.PHONY: help sync dev clean test lint

help:
	@echo "======================================================================"
	@echo "                       CogniFiles - CLI Manager                       "
	@echo "======================================================================"
	@echo "Comandos disponíveis:"
	@echo "  make sync     - Limpa o ambiente, recria as travas e sincroniza o UV"
	@echo "  make dev      - Inicia o servidor FastAPI em modo de desenvolvimento"
	@echo "  make clean    - Remove arquivos temporários de cache do Python e UV"
	@echo "  make lint     - Executa checagem de tipos estáticos com o Mypy/Pyright"
	@echo "======================================================================"

sync:
	@echo "🔄 Resetando travas e sincronizando dependências com o UV..."
	rm -f uv.lock
	uv sync

dev:
	@echo "🚀 Iniciando servidor FastAPI CogniFiles na porta $(APP_PORT)..."
	PYTHONPATH=$(PYTHONPATH) uv run uvicorn app.main:app --reload --port $(APP_PORT)

clean:
	@echo "🧹 Limpando caches e arquivos temporários (*.pyc, .pytest_cache)..."
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type d -name ".pytest_cache" -exec rm -r {} +
	find . -type d -name ".mypy_cache" -exec rm -r {} +
	find . -type d -name ".uv" -exec rm -r {} +

lint:
	@echo "🔍 Executando análise estática de tipos..."
	uv run pyright app/