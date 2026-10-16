"""TaskAnalyzer: métricas de produtividade a partir de tarefas registradas.

Implementa o contrato da especificação SDD (specs/task_analyzer_spec.md): tempo médio de
conclusão e taxa de atraso, gerais e por prioridade, usando apenas a biblioteca padrão.
Todas as datas são tratadas em UTC.
"""

import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

PRIORIDADES: tuple[str, ...] = ("baixa", "media", "alta")
STATUS_VALIDOS: tuple[str, ...] = ("concluida", "pendente", "cancelada")
CAMPOS_OBRIGATORIOS: tuple[str, ...] = (
    "id_tarefa",
    "titulo",
    "prioridade",
    "status",
    "data_criacao",
    "prazo",
)
CASAS_DECIMAIS = 2


class TarefaInvalidaError(ValueError):
    """Tarefa com dados inconsistentes ou fora do contrato de entrada."""


class MetricasIndisponiveisError(ValueError):
    """Não há tarefas concluídas válidas para calcular as métricas."""


def _rotulo(tarefa: dict[str, Any]) -> str:
    """Retorna o identificador da tarefa para uso em mensagens de erro.

    Args:
        tarefa: Registro da tarefa.

    Returns:
        Texto no formato "tarefa <id>".
    """
    return f"tarefa {tarefa.get('id_tarefa', '?')}"


def _validar_campos(tarefa: dict[str, Any]) -> None:
    """Valida presença e valores aceitos dos campos obrigatórios.

    Args:
        tarefa: Registro da tarefa.

    Raises:
        TarefaInvalidaError: Se faltar campo ou o valor estiver fora do contrato.
    """
    for campo in CAMPOS_OBRIGATORIOS:
        if campo not in tarefa:
            raise TarefaInvalidaError(f"{_rotulo(tarefa)}: campo obrigatório ausente: {campo}")

    id_tarefa = tarefa["id_tarefa"]
    if isinstance(id_tarefa, bool) or not isinstance(id_tarefa, int) or id_tarefa <= 0:
        raise TarefaInvalidaError(f"{_rotulo(tarefa)}: id_tarefa deve ser inteiro maior que 0")
    if not isinstance(tarefa["titulo"], str) or not tarefa["titulo"].strip():
        raise TarefaInvalidaError(f"{_rotulo(tarefa)}: titulo não pode ser vazio")
    if tarefa["prioridade"] not in PRIORIDADES:
        raise TarefaInvalidaError(
            f"{_rotulo(tarefa)}: prioridade inválida: {tarefa['prioridade']!r}"
        )
    if tarefa["status"] not in STATUS_VALIDOS:
        raise TarefaInvalidaError(f"{_rotulo(tarefa)}: status inválido: {tarefa['status']!r}")


def _validar_datas_conclusao(tarefa: dict[str, Any]) -> None:
    """Valida as datas de execução de uma tarefa concluída.

    Args:
        tarefa: Registro de tarefa com status "concluida".

    Raises:
        TarefaInvalidaError: Se faltar data_inicio/data_conclusao ou se a conclusão for
            anterior ao início.
    """
    inicio = tarefa.get("data_inicio")
    conclusao = tarefa.get("data_conclusao")
    if inicio is None or conclusao is None:
        raise TarefaInvalidaError(
            f"{_rotulo(tarefa)}: tarefa concluída sem data_inicio ou data_conclusao"
        )
    if conclusao < inicio:
        raise TarefaInvalidaError(f"{_rotulo(tarefa)}: data_conclusao anterior a data_inicio")


def _validar_tarefas(tarefas: list[dict[str, Any]]) -> None:
    """Valida todas as tarefas da entrada antes de qualquer cálculo.

    Args:
        tarefas: Lista de tarefas da entrada.

    Raises:
        TarefaInvalidaError: Na primeira inconsistência encontrada.
    """
    ids_vistos: set[Any] = set()
    for tarefa in tarefas:
        _validar_campos(tarefa)
        if tarefa["id_tarefa"] in ids_vistos:
            raise TarefaInvalidaError(f"{_rotulo(tarefa)}: id_tarefa repetido na lista")
        ids_vistos.add(tarefa["id_tarefa"])
        if tarefa["status"] == "concluida":
            _validar_datas_conclusao(tarefa)


def _minutos_de_conclusao(tarefa: dict[str, Any]) -> float:
    """Calcula o tempo de conclusão (data_conclusao - data_inicio) em minutos.

    Args:
        tarefa: Registro de tarefa concluída e já validada.

    Returns:
        Duração em minutos.
    """
    return (tarefa["data_conclusao"] - tarefa["data_inicio"]).total_seconds() / 60


def _esta_atrasada(tarefa: dict[str, Any]) -> bool:
    """Indica se a conclusão ocorreu depois do prazo.

    Args:
        tarefa: Registro de tarefa concluída e já validada.

    Returns:
        True se data_conclusao for posterior ao prazo.
    """
    prazo: datetime = tarefa["prazo"]
    return tarefa["data_conclusao"] > prazo


def _calcular_metricas(concluidas: list[dict[str, Any]]) -> dict[str, float | int]:
    """Calcula tempo médio, taxa de atraso e quantidade de um grupo de concluídas.

    Grupo vazio retorna zeros (usado apenas em prioridades sem tarefas concluídas).

    Args:
        concluidas: Tarefas concluídas e válidas do grupo.

    Returns:
        Dicionário com tempo_medio_conclusao_min, taxa_atraso_percentual e quantidade_tarefas.
    """
    quantidade = len(concluidas)
    if quantidade == 0:
        return {
            "tempo_medio_conclusao_min": 0.0,
            "taxa_atraso_percentual": 0.0,
            "quantidade_tarefas": 0,
        }
    tempo_total = sum(_minutos_de_conclusao(t) for t in concluidas)
    atrasadas = sum(1 for t in concluidas if _esta_atrasada(t))
    return {
        "tempo_medio_conclusao_min": round(tempo_total / quantidade, CASAS_DECIMAIS),
        "taxa_atraso_percentual": round(atrasadas / quantidade * 100, CASAS_DECIMAIS),
        "quantidade_tarefas": quantidade,
    }


def analisar_tarefas(tarefas: list[dict]) -> dict:
    """Analisa tarefas e devolve métricas de produtividade.

    Somente tarefas com status "concluida" entram no cálculo. Os resultados são
    arredondados com 2 casas decimais e não há efeitos colaterais.

    Args:
        tarefas: Lista de tarefas no formato do contrato de entrada.

    Returns:
        Dicionário com tempo_medio_conclusao_min, taxa_atraso_percentual,
        quantidade_tarefas e indicadores_por_prioridade (baixa, media, alta).

    Raises:
        TarefaInvalidaError: Se alguma tarefa tiver dados inconsistentes.
        MetricasIndisponiveisError: Se não houver nenhuma tarefa concluída.
    """
    logger.info("Analisando %d tarefa(s)", len(tarefas))
    _validar_tarefas(tarefas)

    concluidas = [t for t in tarefas if t["status"] == "concluida"]
    if not concluidas:
        raise MetricasIndisponiveisError(
            "Nenhuma tarefa concluída na entrada: não há dados para calcular as métricas."
        )

    resultado: dict[str, Any] = dict(_calcular_metricas(concluidas))
    resultado["indicadores_por_prioridade"] = {
        prioridade: _calcular_metricas([t for t in concluidas if t["prioridade"] == prioridade])
        for prioridade in PRIORIDADES
    }
    logger.info("Análise concluída: %d tarefa(s) concluída(s)", len(concluidas))
    return resultado
