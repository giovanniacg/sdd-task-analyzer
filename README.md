# sdd-task-analyzer

Módulo de análise de tarefas e produtividade, desenvolvido com **Spec-Driven Development (SDD)**
e geração de código assistida por IA. Projeto cumulativo da disciplina Bootcamp III (CEUB EAD).

- **Autor:** Gabriel Marques da Rocha
- **Contrato de negócio:** [`specs/task_analyzer_spec.md`](specs/task_analyzer_spec.md)
- **Governança de IA:** [`CONTEXT_RULES.md`](CONTEXT_RULES.md)

## Estrutura

```
sdd-task-analyzer/
├── README.md
├── CONTEXT_RULES.md
├── .gitignore
├── requirements.txt
├── specs/task_analyzer_spec.md
├── tests/test_harness.py
└── src/task_analyzer.py
```

## Como executar

Requer Python 3.11+.

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m pytest tests/ -v
```

## Uso

```python
from datetime import datetime, timedelta, timezone
from src.task_analyzer import analisar_tarefas

inicio = datetime(2026, 10, 1, 9, 0, tzinfo=timezone.utc)
tarefas = [{
    "id_tarefa": 1, "titulo": "Exemplo", "prioridade": "alta", "status": "concluida",
    "data_criacao": inicio, "data_inicio": inicio,
    "data_conclusao": inicio + timedelta(minutes=60), "prazo": inicio + timedelta(hours=2),
}]
print(analisar_tarefas(tarefas))
```

## Status do build

Harness `pytest`: ver seção de testes do relatório técnico da Fase 2 (100% aprovado).
