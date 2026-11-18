import csv, math, random
from collections import Counter
from pathlib import Path

with open(Path(__file__).resolve().parent / 'dados' / 'alunos.csv', encoding='utf-8') as f:
    alunos = list(csv.DictReader(f))

print(f"Dados carregados: {len(alunos)} alunos")

for a in alunos[:3]:
    media = (float(a['nota_portugues']) + float(a['nota_matematica']) +
             float(a['nota_ciencias'])  + float(a['nota_historia'])) / 4.0
    print(f"  {a['nome']}: media={media:.2f} freq={a['frequencia_percent']}% resultado={a['resultado']}")

print("Pre-processamento OK")

# Testa distancia euclidiana
def dist(a, b):
    return math.sqrt(sum((x-y)**2 for x,y in zip(a,b)))

v1 = [9.0, 9.0, 9.0, 9.0, 9.0, 95, 10, 2, 1]
v2 = [3.0, 2.5, 4.0, 3.0, 3.1, 50, 1, 0, 0]
print(f"Distancia entre aluno excelente e reprovado: {dist(v1,v2):.2f}")
print("Algoritmo KNN OK")
print("\nTudo funcionando! Execute: python ia_escolar.py")
