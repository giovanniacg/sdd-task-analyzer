# CONTEXT_RULES: governança de contexto para agentes de IA

Fonte da verdade fornecida a qualquer assistente de IA em toda interação de geração de código
deste repositório. Transposta da Seção 3 da Especificação SDD (Fase 1). Contrato de negócio:
`specs/task_analyzer_spec.md`.

## 1. Diretrizes arquiteturais (obrigatórias)

1. Python 3.11+ como versão mínima obrigatória.
2. Type hints em todas as funções e métodos.
3. Princípio Single Responsibility (SRP) e código limpo conforme PEP 8.
4. Docstrings no padrão Google style para módulos, classes, funções e parâmetros.
5. Funções pequenas, coesas e com um único propósito.
6. Tratamento de exceções específico e com mensagens claras (exceções customizadas do domínio,
   nunca `except Exception` genérico silencioso).
7. Logs estruturados com o módulo padrão `logging` (nunca `print` para diagnóstico).
8. Código legível, com nomes descritivos em português, consistentes com o domínio do contrato.

## 2. Proibições explícitas

1. Não usar bibliotecas externas não autorizadas (o módulo usa só a biblioteca padrão; `pytest`
   é permitido somente no harness de testes).
2. Não alterar, remover ou adaptar os cenários de teste fornecidos.
3. Não modificar a estrutura de pastas definida na especificação.
4. Não persistir dados em arquivos ou bancos de dados.
5. Não alterar a assinatura (nome e parâmetros) das funções públicas sem autorização.
6. Não gerar código sem testes correspondentes para as novas funcionalidades.
7. Não inserir código duplicado ou sem necessidade.
8. Não assumir comportamentos não especificados no contrato de negócio.

## 3. Regras de interação com a IA

1. Fornecer à IA o contexto completo antes da solicitação: a especificação + este arquivo.
2. Validar se a IA compreendeu o contrato antes de gerar código (pedir que reformule o que vai fazer).
3. Solicitar explicações quando houver dúvida na solução proposta.
4. Revisar criticamente todo código gerado antes de executar o harness.
5. Rejeitar respostas que violem as proibições ou o contrato, reapresentando a regra violada em
   vez de aceitar o desvio.
