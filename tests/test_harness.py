"""Test Harness do TaskAnalyzer (pytest).

Traduz os cenários de aceite da especificação (secao 2) em testes automatizados:
Cenário 1 (sucesso), Cenário 2 (exceção/erro) e casos de borda.
"""

from datetime import datetime, timedelta, timezone

import pytest

from src.task_analyzer import (
    MetricasIndisponiveisError,
    TarefaInvalidaError,
    analisar_tarefas,
)

BASE = datetime(2026, 10, 1, 9, 0, tzinfo=timezone.utc)


def _tarefa(
    id_tarefa: int,
    prioridade: str = "alta",
    status: str = "concluida",
    minutos: int | None = 60,
    atrasada: bool = False,
) -> dict:
    """Monta uma tarefa de teste.

    Args:
        id_tarefa: Identificador da tarefa.
        prioridade: "baixa", "media" ou "alta".
        status: "concluida", "pendente" ou "cancelada".
        minutos: Duração em minutos (ignorada se a tarefa não for concluída).
        atrasada: Se True, o prazo vence antes da conclusão.

    Returns:
        Dicionário de tarefa no formato do contrato.
    """
    tarefa: dict = {
        "id_tarefa": id_tarefa,
        "titulo": f"Tarefa {id_tarefa}",
        "prioridade": prioridade,
        "status": status,
        "data_criacao": BASE - timedelta(days=1),
        "data_inicio": None,
        "data_conclusao": None,
        "prazo": BASE + timedelta(days=1),
    }
    if status == "concluida" and minutos is not None:
        tarefa["data_inicio"] = BASE
        tarefa["data_conclusao"] = BASE + timedelta(minutes=minutos)
        if atrasada:
            tarefa["prazo"] = BASE + timedelta(minutes=minutos - 1)
    return tarefa


@pytest.fixture
def tarefas_referencia() -> list[dict]:
    """Conjunto de referência da spec: 4 concluídas (1 atrasada) e 1 pendente."""
    return [
        _tarefa(1, "alta", minutos=60),
        _tarefa(2, "alta", minutos=120),
        _tarefa(3, "media", minutos=30, atrasada=True),
        _tarefa(4, "baixa", minutos=90),
        _tarefa(5, "alta", status="pendente"),
    ]


# --- Cenário 1: sucesso -------------------------------------------------------


def test_metricas_gerais_com_tarefas_validas(tarefas_referencia):
    resultado = analisar_tarefas(tarefas_referencia)

    assert resultado["tempo_medio_conclusao_min"] == 75.0
    assert resultado["taxa_atraso_percentual"] == 25.0
    assert resultado["quantidade_tarefas"] == 4


def test_indicadores_por_prioridade(tarefas_referencia):
    por_prioridade = analisar_tarefas(tarefas_referencia)["indicadores_por_prioridade"]

    assert por_prioridade["alta"] == {
        "tempo_medio_conclusao_min": 90.0,
        "taxa_atraso_percentual": 0.0,
        "quantidade_tarefas": 2,
    }
    assert por_prioridade["media"] == {
        "tempo_medio_conclusao_min": 30.0,
        "taxa_atraso_percentual": 100.0,
        "quantidade_tarefas": 1,
    }
    assert por_prioridade["baixa"] == {
        "tempo_medio_conclusao_min": 90.0,
        "taxa_atraso_percentual": 0.0,
        "quantidade_tarefas": 1,
    }


def test_ignora_tarefas_nao_concluidas(tarefas_referencia):
    com_ruido = tarefas_referencia + [
        _tarefa(6, "baixa", status="cancelada"),
        _tarefa(7, "media", status="pendente"),
    ]

    assert analisar_tarefas(com_ruido) == analisar_tarefas(tarefas_referencia)


def test_arredonda_com_duas_casas_decimais():
    tarefas = [_tarefa(1, minutos=10), _tarefa(2, minutos=10), _tarefa(3, minutos=11)]

    resultado = analisar_tarefas(tarefas)

    assert resultado["tempo_medio_conclusao_min"] == 10.33
    assert resultado["taxa_atraso_percentual"] == 0.0


def test_prioridade_sem_tarefas_concluidas_retorna_zeros():
    resultado = analisar_tarefas([_tarefa(1, "alta", minutos=60)])

    assert resultado["indicadores_por_prioridade"]["baixa"] == {
        "tempo_medio_conclusao_min": 0.0,
        "taxa_atraso_percentual": 0.0,
        "quantidade_tarefas": 0,
    }


def test_nao_altera_a_lista_de_entrada(tarefas_referencia):
    copia = [dict(t) for t in tarefas_referencia]

    analisar_tarefas(tarefas_referencia)

    assert tarefas_referencia == copia


# --- Cenário 2: exceção / erro -------------------------------------------------


def test_excecao_data_conclusao_antes_do_inicio():
    tarefa = _tarefa(42, minutos=60)
    tarefa["data_conclusao"] = tarefa["data_inicio"] - timedelta(minutes=5)

    with pytest.raises(TarefaInvalidaError, match="42"):
        analisar_tarefas([tarefa])


def test_excecao_concluida_sem_datas_de_execucao():
    tarefa = _tarefa(7, minutos=None)
    tarefa["status"] = "concluida"

    with pytest.raises(TarefaInvalidaError, match="7"):
        analisar_tarefas([tarefa])


def test_excecao_sem_tarefas_concluidas():
    apenas_pendentes = [_tarefa(1, status="pendente"), _tarefa(2, status="cancelada")]

    with pytest.raises(MetricasIndisponiveisError):
        analisar_tarefas(apenas_pendentes)


def test_excecao_lista_vazia():
    with pytest.raises(MetricasIndisponiveisError):
        analisar_tarefas([])


# --- Validações do contrato de entrada ----------------------------------------


@pytest.mark.parametrize(
    ("campo", "valor"),
    [("prioridade", "urgente"), ("status", "arquivada"), ("titulo", "  ")],
)
def test_excecao_valor_fora_do_contrato(campo, valor):
    tarefa = _tarefa(9)
    tarefa[campo] = valor

    with pytest.raises(TarefaInvalidaError, match="9"):
        analisar_tarefas([tarefa])


def test_excecao_campo_obrigatorio_ausente():
    tarefa = _tarefa(3)
    del tarefa["prazo"]

    with pytest.raises(TarefaInvalidaError, match="prazo"):
        analisar_tarefas([tarefa])


def test_excecao_id_repetido():
    with pytest.raises(TarefaInvalidaError, match="repetido"):
        analisar_tarefas([_tarefa(1), _tarefa(1)])


@pytest.mark.parametrize("id_invalido", [0, -1, "1", True])
def test_excecao_id_invalido(id_invalido):
    tarefa = _tarefa(1)
    tarefa["id_tarefa"] = id_invalido

    with pytest.raises(TarefaInvalidaError):
        analisar_tarefas([tarefa])
