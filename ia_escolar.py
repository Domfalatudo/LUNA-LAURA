"""
=============================================================
  SISTEMA DE IA PARA CLASSIFICAÇÃO DO DESEMPENHO ESCOLAR
  Projeto de Conclusão do Ensino Técnico - IA
  Tema: Desenvolvimento Escolar
  Aluna: Laura
  Técnica: Machine Learning - Árvore de Decisão + K-NN
=============================================================

DESCRIÇÃO:
    Este sistema utiliza Machine Learning para classificar o
    desempenho de alunos em três categorias:
        - aprovado  : desempenho suficiente para aprovação
        - risco     : aluno em zona de atenção, precisa de suporte
        - reprovado : desempenho abaixo do mínimo

    Com base nas notas, frequência, horas de estudo e outros
    fatores, o modelo aprende padrões e faz previsões para
    novos alunos, auxiliando professores e coordenadores.
"""

# ── Importações ──────────────────────────────────────────────
import csv                          # leitura do arquivo de dados
import math                         # cálculos matemáticos
import random                       # embaralhamento dos dados
from collections import Counter     # contagem de classes
from pathlib import Path


# ═══════════════════════════════════════════════════════════════
#  1. CARREGAMENTO E PRÉ-PROCESSAMENTO DOS DADOS
# ═══════════════════════════════════════════════════════════════

def carregar_dados(caminho_csv):
    """
    Lê o arquivo CSV e retorna uma lista de dicionários,
    cada um representando um aluno com seus atributos.
    """
    alunos = []
    with open(caminho_csv, encoding='utf-8') as arquivo:
        leitor = csv.DictReader(arquivo)
        for linha in leitor:
            alunos.append(linha)
    return alunos


def pre_processar(alunos):
    """
    Converte os dados brutos em vetores numéricos (features)
    e rótulos (labels) que o modelo consegue processar.

    Codificação das variáveis categóricas:
        participacao_aula : baixa=0, media=1, alta=2
        situacao_familiar : instavel=0, estavel=1
        resultado         : reprovado=0, risco=1, aprovado=2
    """
    # Mapeamentos de texto para número
    map_participacao = {'baixa': 0, 'media': 1, 'alta': 2}
    map_situacao     = {'instavel': 0, 'estavel': 1}
    map_resultado    = {'reprovado': 0, 'risco': 1, 'aprovado': 2}
    map_resultado_inv = {0: 'reprovado', 1: 'risco', 2: 'aprovado'}

    X = []  # matriz de features
    y = []  # vetor de rótulos

    for a in alunos:
        # Calcula a média geral das notas
        media = (float(a['nota_portugues']) +
                 float(a['nota_matematica']) +
                 float(a['nota_ciencias']) +
                 float(a['nota_historia'])) / 4.0

        vetor = [
            float(a['nota_portugues']),
            float(a['nota_matematica']),
            float(a['nota_ciencias']),
            float(a['nota_historia']),
            media,                                        # feature derivada
            float(a['frequencia_percent']),
            float(a['horas_estudo_semana']),
            map_participacao[a['participacao_aula']],
            map_situacao[a['situacao_familiar']],
        ]
        X.append(vetor)
        y.append(map_resultado[a['resultado']])

    return X, y, map_resultado_inv


def normalizar(X_treino, X_teste):
    """
    Aplica normalização Min-Max em cada feature:
        valor_norm = (valor - min) / (max - min)

    Isso evita que features com escala maior (ex: frequência 0-100)
    dominem sobre features com escala menor (ex: notas 0-10).
    """
    n_features = len(X_treino[0])
    minimos = [min(x[i] for x in X_treino) for i in range(n_features)]
    maximos = [max(x[i] for x in X_treino) for i in range(n_features)]

    def normalizar_linha(linha):
        resultado = []
        for i, val in enumerate(linha):
            denom = maximos[i] - minimos[i]
            if denom == 0:
                resultado.append(0.0)
            else:
                resultado.append((val - minimos[i]) / denom)
        return resultado

    X_treino_norm = [normalizar_linha(x) for x in X_treino]
    X_teste_norm  = [normalizar_linha(x) for x in X_teste]
    return X_treino_norm, X_teste_norm


def dividir_dados(X, y, percentual_treino=0.8, seed=42):
    """
    Divide os dados em conjunto de treino e conjunto de teste.
    Usa 80% para treino e 20% para teste (padrão em ML).
    """
    dados = list(zip(X, y))
    random.seed(seed)
    random.shuffle(dados)

    corte = int(len(dados) * percentual_treino)
    treino = dados[:corte]
    teste  = dados[corte:]

    X_treino = [d[0] for d in treino]
    y_treino = [d[1] for d in treino]
    X_teste  = [d[0] for d in teste]
    y_teste  = [d[1] for d in teste]

    return X_treino, y_treino, X_teste, y_teste


# ═══════════════════════════════════════════════════════════════
#  2. MODELO K-NN (K-NEAREST NEIGHBORS)
# ═══════════════════════════════════════════════════════════════

def distancia_euclidiana(a, b):
    """
    Calcula a distância euclidiana entre dois vetores.
    Fórmula: sqrt( Σ (a_i - b_i)² )
    """
    return math.sqrt(sum((ai - bi) ** 2 for ai, bi in zip(a, b)))


def knn_prever(X_treino, y_treino, amostra, k=5):
    """
    Algoritmo K-NN:
    1. Calcula a distância da amostra para todos os pontos de treino.
    2. Seleciona os K vizinhos mais próximos.
    3. Retorna a classe mais votada entre esses vizinhos.

    Parâmetro k=5: usa os 5 vizinhos mais próximos para votar.
    """
    # Calcula distâncias de 'amostra' para cada ponto de treino
    distancias = []
    for i, x in enumerate(X_treino):
        d = distancia_euclidiana(amostra, x)
        distancias.append((d, y_treino[i]))

    # Ordena do mais próximo ao mais distante
    distancias.sort(key=lambda item: item[0])

    # Pega os K mais próximos e faz votação
    k_vizinhos = [classe for _, classe in distancias[:k]]
    contagem = Counter(k_vizinhos)
    return contagem.most_common(1)[0][0]  # classe mais votada


def knn_treinar_e_avaliar(X_treino, y_treino, X_teste, y_teste, k=5):
    """
    'Treina' o K-NN (que consiste em memorizar os dados de treino)
    e avalia sua acurácia no conjunto de teste.
    """
    corretos = 0
    predicoes = []

    for i, amostra in enumerate(X_teste):
        pred = knn_prever(X_treino, y_treino, amostra, k)
        predicoes.append(pred)
        if pred == y_teste[i]:
            corretos += 1

    acuracia = corretos / len(y_teste) if y_teste else 0
    return predicoes, acuracia


# ═══════════════════════════════════════════════════════════════
#  3. MODELO BASEADO EM REGRAS (SISTEMA ESPECIALISTA)
# ═══════════════════════════════════════════════════════════════

def classificar_por_regras(nota_port, nota_mat, nota_cien, nota_hist,
                            frequencia, horas_estudo, participacao,
                            situacao_familiar):
    """
    Sistema baseado em regras que imita a lógica de um professor
    experiente. As regras foram construídas com base em critérios
    pedagógicos comuns em escolas brasileiras.

    REGRAS PRINCIPAIS:
        R1: Reprovado se média < 5.0
        R2: Reprovado se frequência < 60%
        R3: Risco se 5.0 ≤ média < 6.5
        R4: Risco se frequência entre 60-75%
        R5: Risco se horas de estudo < 3 e situação instável
        R6: Aprovado se média ≥ 6.5 e frequência ≥ 75%
    """
    media = (nota_port + nota_mat + nota_cien + nota_hist) / 4.0

    # Regras de Reprovação
    if media < 5.0:
        return 'reprovado', f"Média {media:.1f} abaixo do mínimo (5,0)"
    if frequencia < 60:
        return 'reprovado', f"Frequência {frequencia}% abaixo do mínimo (60%)"

    # Regras de Risco
    if media < 6.5:
        return 'risco', f"Média {media:.1f} na zona de risco (5,0–6,4)"
    if frequencia < 75:
        return 'risco', f"Frequência {frequencia}% na zona de atenção (60–74%)"
    if horas_estudo < 3 and situacao_familiar == 'instavel':
        return 'risco', "Pouco estudo e situação familiar instável"

    # Regra de Aprovação
    return 'aprovado', f"Média {media:.1f} e frequência {frequencia}% adequadas"


def prever_desempenho_web(notas, frequencia, horas_estudo, caminho_csv):
    """Estima o desempenho com K-NN usando os dados conhecidos do aluno."""
    materias = ('portugues', 'matematica', 'ciencias', 'historia')
    valores = [float(notas[materia]) for materia in materias]
    frequencia = float(frequencia)
    horas_estudo = float(horas_estudo)

    if any(nota < 0 or nota > 10 for nota in valores):
        raise ValueError("As notas devem estar entre 0 e 10.")
    if not 0 <= frequencia <= 100:
        raise ValueError("A frequência deve estar entre 0 e 100.")
    if horas_estudo < 0:
        raise ValueError("As horas de estudo não podem ser negativas.")

    alunos = carregar_dados(caminho_csv)
    X, y, map_resultado_inv = pre_processar(alunos)
    indices = (0, 1, 2, 3, 4, 5, 6)
    X_treino = [[linha[i] for i in indices] for linha in X]
    media = sum(valores) / len(valores)
    amostra = valores + [media, frequencia, horas_estudo]

    X_treino_norm, amostra_norm = normalizar(X_treino, [amostra])
    classe = knn_prever(X_treino_norm, y, amostra_norm[0], k=5)
    classificacao = map_resultado_inv[classe]
    recomendacoes = {
        'aprovado': 'Continue com sua rotina: consistência é o que mantém o progresso.',
        'risco': 'Escolha uma matéria para revisar esta semana e acompanhe sua evolução.',
        'reprovado': 'Converse com um professor e monte um plano de reforço para as matérias prioritárias.',
    }

    return {
        'classificacao': classificacao,
        'media': media,
        'recomendacao': recomendacoes[classificacao],
    }


# ═══════════════════════════════════════════════════════════════
#  4. AVALIAÇÃO DO MODELO
# ═══════════════════════════════════════════════════════════════

def calcular_metricas(y_real, y_pred, classes):
    """
    Calcula acurácia, precisão, recall e F1-Score por classe.

    - Acurácia   : % de previsões corretas no total
    - Precisão   : das previsões de classe X, quantas estavam certas
    - Recall     : dos alunos reais de classe X, quantos foram detectados
    - F1-Score   : média harmônica entre precisão e recall
    """
    n = len(y_real)
    acuracia = sum(1 for r, p in zip(y_real, y_pred) if r == p) / n

    metricas_por_classe = {}
    for c in classes:
        tp = sum(1 for r, p in zip(y_real, y_pred) if r == c and p == c)
        fp = sum(1 for r, p in zip(y_real, y_pred) if r != c and p == c)
        fn = sum(1 for r, p in zip(y_real, y_pred) if r == c and p != c)

        precisao = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall   = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precisao * recall / (precisao + recall)
              if (precisao + recall) > 0 else 0.0)

        metricas_por_classe[c] = {
            'precisao': precisao,
            'recall':   recall,
            'f1':       f1
        }

    return acuracia, metricas_por_classe


def matriz_confusao(y_real, y_pred, classes):
    """
    Monta a matriz de confusão.
    Linhas = classe real | Colunas = classe prevista
    """
    matriz = {r: {p: 0 for p in classes} for r in classes}
    for r, p in zip(y_real, y_pred):
        matriz[r][p] += 1
    return matriz


# ═══════════════════════════════════════════════════════════════
#  5. INTERFACE DE PREVISÃO PARA NOVO ALUNO
# ═══════════════════════════════════════════════════════════════

def prever_novo_aluno(X_treino, y_treino, map_inv, k=5):
    """
    Permite ao usuário inserir os dados de um novo aluno e obter
    a previsão tanto pelo K-NN quanto pelo sistema de regras.
    """
    print("\n" + "═" * 55)
    print("  PREVISÃO PARA NOVO ALUNO")
    print("═" * 55)

    try:
        nome       = input("Nome do aluno: ")
        port       = float(input("Nota em Português  (0–10): "))
        mat        = float(input("Nota em Matemática (0–10): "))
        cien       = float(input("Nota em Ciências   (0–10): "))
        hist       = float(input("Nota em História   (0–10): "))
        freq       = float(input("Frequência (%)          : "))
        horas      = float(input("Horas de estudo/semana  : "))
        part_str   = input("Participação (baixa/media/alta): ").strip().lower()
        sit_str    = input("Situação familiar (estavel/instavel): ").strip().lower()

        map_part = {'baixa': 0, 'media': 1, 'alta': 2}
        map_sit  = {'instavel': 0, 'estavel': 1}

        if part_str not in map_part or sit_str not in map_sit:
            print("⚠ Entrada inválida para participação ou situação familiar.")
            return

        media = (port + mat + cien + hist) / 4.0

        vetor = [port, mat, cien, hist, media, freq, horas,
                 map_part[part_str], map_sit[sit_str]]

        # Normaliza usando os dados de treino
        X_treino_n, vetor_n = normalizar(X_treino, [vetor])
        vetor_norm = vetor_n[0]

        # Previsão K-NN
        pred_knn = knn_prever(X_treino_n, y_treino, vetor_norm, k)
        label_knn = map_inv[pred_knn]

        # Previsão por Regras
        label_regras, justificativa = classificar_por_regras(
            port, mat, cien, hist, freq, horas, part_str, sit_str)

        print(f"\n── Resultado para {nome} ──")
        print(f"  Média geral          : {media:.2f}")
        print(f"  Frequência           : {freq}%")
        print(f"  Modelo K-NN (k={k})  : {label_knn.upper()}")
        print(f"  Sistema de Regras    : {label_regras.upper()}")
        print(f"  Justificativa regras : {justificativa}")

        # Recomendação pedagógica
        situacao = label_knn if label_knn == label_regras else label_regras
        print("\n── Recomendação Pedagógica ──")
        if situacao == 'reprovado':
            print("  ❌ Aluno com alto risco de reprovação.")
            print("     → Encaminhar para reforço escolar imediato.")
            print("     → Contatar responsáveis.")
        elif situacao == 'risco':
            print("  ⚠  Aluno em zona de atenção.")
            print("     → Monitorar evolução nas próximas semanas.")
            print("     → Oferecer suporte pedagógico preventivo.")
        else:
            print("  ✅ Aluno com desempenho adequado.")
            print("     → Manter acompanhamento padrão.")

    except ValueError:
        print("⚠ Erro: insira valores numéricos válidos para notas e frequência.")


# ═══════════════════════════════════════════════════════════════
#  6. CASOS DE TESTE DOCUMENTADOS
# ═══════════════════════════════════════════════════════════════

def executar_casos_de_teste(X_treino, y_treino, map_inv, k=5):
    """
    Executa os 5 casos de teste obrigatórios do projeto.
    Cada caso tem entrada conhecida e resultado esperado definido.
    """
    casos = [
        # (nome, port, mat, cien, hist, freq, horas, part, sit, esperado)
        ("CASO 1 — Aluno excelente",
         9.5, 9.0, 9.0, 8.5, 97, 12, 'alta', 'estavel', 'aprovado'),
        ("CASO 2 — Aluno reprovado por nota",
         3.0, 2.5, 4.0, 3.5, 90, 8, 'media', 'estavel', 'reprovado'),
        ("CASO 3 — Aluno reprovado por falta",
         7.0, 7.5, 6.5, 7.0, 45, 5, 'media', 'estavel', 'reprovado'),
        ("CASO 4 — Aluno em zona de risco",
         5.5, 5.0, 6.0, 5.5, 72, 4, 'media', 'instavel', 'risco'),
        ("CASO 5 — Aluno no limite de aprovação",
         6.5, 6.0, 7.0, 6.5, 76, 5, 'media', 'estavel', 'aprovado'),
    ]

    map_part = {'baixa': 0, 'media': 1, 'alta': 2}
    map_sit  = {'instavel': 0, 'estavel': 1}
    map_num  = {'reprovado': 0, 'risco': 1, 'aprovado': 2}

    print("\n" + "═" * 65)
    print("  CASOS DE TESTE")
    print("═" * 65)

    acertos = 0
    for caso in casos:
        nome, port, mat, cien, hist, freq, horas, part, sit, esperado = caso
        media = (port + mat + cien + hist) / 4.0

        vetor = [port, mat, cien, hist, media, freq, horas,
                 map_part[part], map_sit[sit]]

        X_treino_n, vetor_n = normalizar(X_treino, [vetor])
        pred_knn_num = knn_prever(X_treino_n, y_treino, vetor_n[0], k)
        pred_knn = map_inv[pred_knn_num]

        pred_regras, just = classificar_por_regras(
            port, mat, cien, hist, freq, horas, part, sit)

        acerto_knn    = "✅" if pred_knn == esperado    else "❌"
        acerto_regras = "✅" if pred_regras == esperado else "❌"
        if pred_knn == esperado:
            acertos += 1

        print(f"\n  {nome}")
        print(f"    Notas: Port={port} | Mat={mat} | Cien={cien} | Hist={hist}")
        print(f"    Média={media:.2f} | Freq={freq}% | Horas={horas}h")
        print(f"    Esperado   : {esperado.upper()}")
        print(f"    K-NN       : {pred_knn.upper()} {acerto_knn}")
        print(f"    Regras     : {pred_regras.upper()} {acerto_regras}  ({just})")

    print(f"\n  Acurácia nos casos de teste (K-NN): {acertos}/{len(casos)} = {acertos/len(casos)*100:.0f}%")


# ═══════════════════════════════════════════════════════════════
#  7. PROGRAMA PRINCIPAL
# ═══════════════════════════════════════════════════════════════

def main():
    print("=" * 65)
    print("  SISTEMA DE IA — CLASSIFICAÇÃO DO DESEMPENHO ESCOLAR")
    print("  Projeto TCC | Componente: Inteligência Artificial")
    print("=" * 65)

    # ── Carrega e processa dados ──────────────────────────────
    caminho = Path(__file__).resolve().parent / "dados" / "alunos.csv"
    alunos_brutos = carregar_dados(caminho)
    print(f"\n✔ {len(alunos_brutos)} registros de alunos carregados.")

    X, y, map_inv = pre_processar(alunos_brutos)

    # ── Divide em treino e teste ──────────────────────────────
    X_treino, y_treino, X_teste, y_teste = dividir_dados(X, y, 0.8)
    print(f"✔ Treino: {len(X_treino)} amostras | Teste: {len(X_teste)} amostras")

    # ── Normalização ──────────────────────────────────────────
    X_treino_n, X_teste_n = normalizar(X_treino, X_teste)

    # ── Treino e avaliação do K-NN ────────────────────────────
    K = 5
    predicoes, acuracia = knn_treinar_e_avaliar(
        X_treino_n, y_treino, X_teste_n, y_teste, k=K)

    classes_num = [0, 1, 2]
    acuracia, metricas = calcular_metricas(y_teste, predicoes, classes_num)
    matriz = matriz_confusao(y_teste, predicoes, classes_num)

    # ── Exibe resultados ──────────────────────────────────────
    nomes_classes = {0: 'reprovado', 1: 'risco', 2: 'aprovado'}

    print("\n" + "─" * 55)
    print(f"  RESULTADOS DO MODELO K-NN (k={K})")
    print("─" * 55)
    print(f"  Acurácia geral: {acuracia * 100:.1f}%\n")

    print(f"  {'Classe':<12} {'Precisão':>10} {'Recall':>10} {'F1-Score':>10}")
    print("  " + "─" * 44)
    for c in classes_num:
        m = metricas[c]
        print(f"  {nomes_classes[c]:<12} {m['precisao']:>10.2f} "
              f"{m['recall']:>10.2f} {m['f1']:>10.2f}")

    print("\n  Matriz de Confusão (linhas=real, colunas=previsto):")
    header = f"  {'':12}" + "".join(f"{nomes_classes[c]:>12}" for c in classes_num)
    print(header)
    for r in classes_num:
        linha = f"  {nomes_classes[r]:<12}"
        for p in classes_num:
            linha += f"{matriz[r][p]:>12}"
        print(linha)

    # ── Casos de teste ────────────────────────────────────────
    executar_casos_de_teste(X_treino_n, y_treino, map_inv, k=K)

    # ── Menu interativo ───────────────────────────────────────
    while True:
        print("\n" + "─" * 55)
        print("  MENU")
        print("  [1] Prever desempenho de novo aluno")
        print("  [2] Exibir estatísticas do conjunto de dados")
        print("  [0] Sair")
        opcao = input("  Escolha: ").strip()

        if opcao == '1':
            prever_novo_aluno(X_treino_n, y_treino, map_inv, k=K)
        elif opcao == '2':
            exibir_estatisticas(alunos_brutos)
        elif opcao == '0':
            print("\n  Encerrando o sistema. Até logo!")
            break
        else:
            print("  Opção inválida.")


def exibir_estatisticas(alunos):
    """Exibe estatísticas descritivas do conjunto de dados."""
    total = len(alunos)
    contagem = Counter(a['resultado'] for a in alunos)

    medias_gerais = []
    for a in alunos:
        m = (float(a['nota_portugues']) + float(a['nota_matematica']) +
             float(a['nota_ciencias'])  + float(a['nota_historia'])) / 4.0
        medias_gerais.append(m)

    print("\n" + "─" * 55)
    print("  ESTATÍSTICAS DO CONJUNTO DE DADOS")
    print("─" * 55)
    print(f"  Total de alunos     : {total}")
    print(f"  Aprovados           : {contagem['aprovado']}  "
          f"({contagem['aprovado']/total*100:.1f}%)")
    print(f"  Em risco            : {contagem['risco']}   "
          f"({contagem['risco']/total*100:.1f}%)")
    print(f"  Reprovados          : {contagem['reprovado']}  "
          f"({contagem['reprovado']/total*100:.1f}%)")
    print(f"  Média geral da turma: {sum(medias_gerais)/len(medias_gerais):.2f}")
    print(f"  Maior média         : {max(medias_gerais):.2f}")
    print(f"  Menor média         : {min(medias_gerais):.2f}")


if __name__ == "__main__":
    main()
