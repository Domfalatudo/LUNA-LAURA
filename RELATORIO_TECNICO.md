# RELATÓRIO TÉCNICO — TCC ENSINO TÉCNICO PROFISSIONALIZANTE
**Componente Curricular:** Inteligência Artificial  
**Tema:** Criando uma IA do Zero: da concepção ao protótipo funcional  
**Projeto escolhido:** Classificador Inteligente de Desempenho Escolar  
**Modalidade:** Individual  

---

## CAPA E IDENTIFICAÇÃO

| Campo | Informação |
|---|---|
| Título | Sistema de IA para Classificação do Desempenho Escolar |
| Tema geral | Desenvolvimento Escolar |
| Técnica de IA | Machine Learning (K-Nearest Neighbors) + Sistema Baseado em Regras |
| Linguagem | Python 3 (sem bibliotecas externas) |
| Arquivo principal | `ia_escolar.py` |
| Dados | `dados/alunos.csv` (30 registros) |

---

## 1. INTRODUÇÃO E JUSTIFICATIVA

A evasão escolar e a reprovação são problemas sérios no Brasil. Segundo dados históricos do INEP, milhares de alunos deixam a escola anualmente por dificuldades acadêmicas que, em muitos casos, poderiam ter sido identificadas e tratadas mais cedo.

Professores e coordenadores pedagógicos frequentemente lidam com turmas numerosas e têm dificuldade de identificar, de forma sistemática, quais alunos estão em risco de reprovação antes que seja tarde demais para intervir.

A Inteligência Artificial pode ser uma aliada nesse processo. Um sistema capaz de analisar notas, frequência e hábitos de estudo pode sinalizar automaticamente quais alunos precisam de atenção, liberando o professor para focar na intervenção em vez de na triagem.

---

## 2. PROBLEMA E OBJETIVOS

### Problema
Como identificar, de forma automatizada e antecipada, alunos com risco de reprovação a partir de dados acadêmicos, para que a escola possa intervir a tempo?

### Público-alvo
Professores, coordenadores pedagógicos e secretarias escolares de escolas de ensino fundamental e médio.

### Objetivo geral
Desenvolver um sistema classificador que, a partir de notas, frequência e informações comportamentais, categorize automaticamente o desempenho de cada aluno em: **aprovado**, **em risco** ou **reprovado**.

### Objetivos específicos
1. Implementar o algoritmo K-Nearest Neighbors (K-NN) do zero, sem bibliotecas de ML.
2. Implementar um sistema baseado em regras pedagógicas como segundo classificador.
3. Comparar os dois modelos e analisar os resultados.
4. Oferecer recomendações pedagógicas automáticas.
5. Avaliar limitações, vieses e aspectos éticos do sistema.

---

## 3. FUNDAMENTAÇÃO TEÓRICA

### 3.1 O que é Machine Learning?

Machine Learning (aprendizado de máquina) é uma subárea da IA que permite que computadores aprendam padrões a partir de dados, sem serem explicitamente programados para cada situação. Em vez de o programador escrever regras manualmente, o algoritmo descobre as regras sozinho a partir dos exemplos.

### 3.2 Classificação supervisionada

Este projeto utiliza **aprendizado supervisionado**: o modelo recebe exemplos já rotulados (alunos com seus resultados conhecidos) e aprende a associar as características ao resultado. Depois, aplica esse aprendizado a novos casos.

### 3.3 Algoritmo K-NN (K-Nearest Neighbors)

O K-NN é um dos algoritmos mais intuitivos de ML. Seu funcionamento:

1. **Treinamento**: memoriza todos os exemplos rotulados.
2. **Previsão**: para um novo aluno, calcula a distância dele para todos os exemplos memorizados.
3. **Decisão**: os K vizinhos mais próximos "votam" — a classe mais votada é o resultado.

**Distância euclidiana** (usada neste projeto):
```
d(a, b) = √( Σ (a_i - b_i)² )
```

**Por que K=5?** Com K muito pequeno (1), o modelo fica sensível a ruídos; com K muito grande, perde precisão local. K=5 é um valor equilibrado e amplamente usado.

### 3.4 Sistema Baseado em Regras (SBR)

Um Sistema Baseado em Regras codifica conhecimento especializado na forma de regras "SE... ENTÃO...". Neste projeto, as regras foram construídas com base em critérios pedagógicos reais:

- SE média < 5,0 → REPROVADO
- SE frequência < 60% → REPROVADO
- SE 5,0 ≤ média < 6,5 → RISCO
- SE frequência entre 60-75% → RISCO
- SE média ≥ 6,5 E frequência ≥ 75% → APROVADO

### 3.5 Normalização Min-Max

As features têm escalas diferentes (notas de 0–10, frequência de 0–100%). Sem normalização, a frequência dominaria o cálculo de distância no K-NN. A normalização Min-Max resolve isso:

```
valor_norm = (valor - mínimo) / (máximo - mínimo)
```

Resultado: todos os valores ficam entre 0 e 1.

### 3.6 Avaliação do modelo

**Acurácia**: proporção de previsões corretas.  
**Precisão**: das previsões de classe X, quantas eram realmente X.  
**Recall**: dos casos reais de classe X, quantos foram corretamente identificados.  
**F1-Score**: média harmônica entre precisão e recall (equilibra os dois).  
**Matriz de confusão**: tabela mostrando onde o modelo acerta e erra.

---

## 4. METODOLOGIA E TECNOLOGIAS

| Item | Descrição |
|---|---|
| Linguagem | Python 3 |
| Bibliotecas | Apenas módulos padrão: `csv`, `math`, `random`, `collections` |
| Algoritmo principal | K-Nearest Neighbors (implementado do zero) |
| Algoritmo auxiliar | Sistema baseado em regras pedagógicas |
| Dados | 30 registros sintéticos de alunos fictícios |
| Divisão treino/teste | 80% treino / 20% teste |
| Validação | Avaliação com acurácia, precisão, recall, F1 e matriz de confusão |

**Decisão técnica — por que implementar sem bibliotecas externas?**  
O documento do trabalho exige que o estudante compreenda e explique o funcionamento do modelo. Implementar o K-NN do zero garante esse entendimento, pois cada linha de código tem uma razão explicável.

---

## 5. ARQUITETURA E FLUXO DE FUNCIONAMENTO

```
┌─────────────────────────────────────────────────────────┐
│                     FLUXO DO SISTEMA                    │
└─────────────────────────────────────────────────────────┘

[1] ENTRADA DE DADOS
    └─ Arquivo CSV com 30 alunos
       (notas, frequência, horas de estudo, participação, situação familiar)

[2] PRÉ-PROCESSAMENTO
    ├─ Conversão de texto para número (codificação)
    ├─ Cálculo da média geral (feature derivada)
    └─ Normalização Min-Max

[3] DIVISÃO DOS DADOS
    ├─ 80% → Conjunto de Treino (24 amostras)
    └─ 20% → Conjunto de Teste  ( 6 amostras)

[4] MODELOS
    ├─ Modelo 1: K-NN (k=5)
    │   ├─ Memoriza dados de treino
    │   └─ Prevê por distância euclidiana + votação
    └─ Modelo 2: Sistema de Regras
        └─ Aplica regras pedagógicas fixas

[5] AVALIAÇÃO
    ├─ Acurácia, Precisão, Recall, F1-Score
    └─ Matriz de Confusão

[6] SAÍDA
    ├─ Classificação: APROVADO / RISCO / REPROVADO
    └─ Recomendação pedagógica automática
```

---

## 6. DESCRIÇÃO DA IMPLEMENTAÇÃO

### Arquivos do projeto
```
projeto_ia_escolar/
├── ia_escolar.py          ← Código principal
├── dados/
│   └── alunos.csv         ← Base de dados dos alunos
├── RELATORIO_TECNICO.md   ← Este relatório
└── README.md              ← Instruções de execução
```

### Módulos implementados

| Função | Descrição |
|---|---|
| `carregar_dados()` | Lê o CSV e retorna lista de dicionários |
| `pre_processar()` | Converte dados em vetores numéricos |
| `normalizar()` | Aplica Min-Max nas features |
| `dividir_dados()` | Separa 80% treino / 20% teste |
| `distancia_euclidiana()` | Calcula distância entre dois vetores |
| `knn_prever()` | Classifica uma amostra pelo K-NN |
| `knn_treinar_e_avaliar()` | Avalia o modelo no conjunto de teste |
| `classificar_por_regras()` | Classifica por regras pedagógicas |
| `calcular_metricas()` | Calcula acurácia, precisão, recall, F1 |
| `matriz_confusao()` | Monta a matriz de confusão |
| `prever_novo_aluno()` | Interface para previsão interativa |
| `executar_casos_de_teste()` | Executa os 5 casos de teste documentados |
| `exibir_estatisticas()` | Mostra estatísticas descritivas dos dados |

### Features utilizadas (variáveis de entrada)

| # | Feature | Tipo | Escala |
|---|---|---|---|
| 1 | Nota em Português | numérico | 0–10 |
| 2 | Nota em Matemática | numérico | 0–10 |
| 3 | Nota em Ciências | numérico | 0–10 |
| 4 | Nota em História | numérico | 0–10 |
| 5 | Média geral (derivada) | numérico | 0–10 |
| 6 | Frequência (%) | numérico | 0–100 |
| 7 | Horas de estudo/semana | numérico | 0–20 |
| 8 | Participação em aula | categórico → numérico | 0, 1, 2 |
| 9 | Situação familiar | categórico → numérico | 0, 1 |

---

## 7. TESTES E RESULTADOS

### Casos de Teste

| # | Descrição | Notas | Freq | Esperado | K-NN | Regras |
|---|---|---|---|---|---|---|
| 1 | Aluno excelente | Média 9.0 | 97% | aprovado | ✅ aprovado | ✅ aprovado |
| 2 | Reprovado por nota | Média 3.1 | 90% | reprovado | ✅ reprovado | ✅ reprovado |
| 3 | Reprovado por falta | Média 7.0 | 45% | reprovado | ✅ reprovado | ✅ reprovado |
| 4 | Zona de risco | Média 5.5 | 72% | risco | ✅ risco | ✅ risco |
| 5 | Limite de aprovação | Média 6.5 | 76% | aprovado | ✅ aprovado | ✅ aprovado |

**Acurácia nos casos de teste: 5/5 = 100%**

### Avaliação no conjunto de teste (6 amostras)
*(Resultado gerado na execução — pode variar conforme a divisão aleatória)*

- Acurácia geral esperada: **~85–100%** (conjunto pequeno)
- O modelo performa melhor nos casos extremos (excelente / muito ruim)
- Casos no limite entre classes são os mais difíceis

---

## 8. LIMITAÇÕES, ASPECTOS ÉTICOS E MELHORIAS FUTURAS

### 8.1 Limitações técnicas

1. **Base de dados pequena**: 30 alunos é insuficiente para um modelo robusto em produção. Em um cenário real, seriam necessários centenas ou milhares de registros.
2. **Dados sintéticos**: os dados foram criados manualmente, o que pode introduzir padrões artificialmente simples que o modelo aprende facilmente.
3. **Ausência de validação cruzada**: com 30 amostras, a divisão aleatória impacta muito o resultado. Cross-validation seria mais adequado.
4. **K-NN é sensível a outliers**: um aluno com características muito atípicas pode ser classificado incorretamente.
5. **Features limitadas**: outros fatores relevantes (histórico anterior, problemas de saúde, histórico socioeconômico) não foram incluídos.

### 8.2 Aspectos éticos e riscos

**Viés algorítmico:**  
O modelo aprende os padrões dos dados históricos. Se historicamente alunos de determinado perfil (situação familiar instável, por exemplo) foram mais reprovados, o modelo pode perpetuar essa associação de forma injusta.

**Risco de estigmatização:**  
Classificar um aluno como "risco" ou "reprovado" automaticamente pode influenciar negativamente a percepção do professor, gerando uma profecia autorrealizável (efeito Pigmalião invertido).

**Privacidade de dados:**  
Os dados escolares são sensíveis. Um sistema real precisaria estar em conformidade com a LGPD (Lei Geral de Proteção de Dados), com acesso restrito a profissionais autorizados.

**Uso indevido:**  
O sistema deve ser uma ferramenta de apoio à decisão, nunca substituir o julgamento humano do professor ou coordenador.

**Responsabilidade da previsão:**  
Uma previsão incorreta (falso positivo para "reprovado") pode causar estresse desnecessário ao aluno. Uma previsão incorreta (falso negativo para "risco") pode deixar de acionar um suporte necessário.

### 8.3 Melhorias futuras

1. Ampliar a base de dados com registros reais (anonimizados).
2. Implementar validação cruzada (k-fold cross-validation).
3. Adicionar algoritmos adicionais (Naive Bayes, Regressão Logística) para comparação.
4. Criar interface gráfica com gráficos de desempenho.
5. Permitir importação de planilhas reais de notas escolares.
6. Adicionar explicabilidade: mostrar quais features mais influenciaram a decisão.
7. Implementar alertas periódicos baseados em evolução bimestral.

---

## 9. CONCLUSÃO

Este projeto demonstrou que é possível construir um sistema funcional de classificação de desempenho escolar usando Machine Learning implementado do zero em Python, sem dependência de bibliotecas externas especializadas.

O algoritmo K-NN, apesar de simples, apresentou boa performance nos testes realizados, especialmente quando combinado com normalização adequada das features. O sistema de regras complementou o K-NN, fornecendo justificativas interpretáveis para cada classificação.

O desenvolvimento deste projeto permitiu compreender na prática conceitos fundamentais de IA: como os dados são estruturados e processados, como um modelo aprende padrões, como é avaliada a qualidade de um classificador e quais são os riscos éticos de sistemas automatizados de tomada de decisão.

A principal lição foi que um sistema de IA é tão bom quanto os dados que utiliza, e que nenhuma previsão automática deve substituir o olhar humano e cuidadoso de um educador.

---

## 10. REFERÊNCIAS

- MITCHELL, Tom. *Machine Learning*. McGraw-Hill, 1997.
- GÉRON, Aurélien. *Hands-On Machine Learning with Scikit-Learn, Keras, and TensorFlow*. O'Reilly, 2022.
- INEP — Instituto Nacional de Estudos e Pesquisas Educacionais Anísio Teixeira. Taxas de Rendimento Escolar. Disponível em: https://www.gov.br/inep
- Python Software Foundation. Documentação oficial do Python 3. Disponível em: https://docs.python.org/3/
- Brasil. *Lei nº 13.709/2018 — Lei Geral de Proteção de Dados (LGPD)*. Disponível em: https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm
