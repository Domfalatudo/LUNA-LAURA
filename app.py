"""
app.py — Servidor Flask do sistema educacional Luna
Execute: python app.py
Acesse:  http://localhost:5000
"""
from flask import (Flask, render_template, request,
                   session, redirect, url_for, jsonify, flash, get_flashed_messages)
import json
import os
import re
import secrets
import unicodedata
from datetime import date
from pathlib import Path
from dotenv import load_dotenv
from werkzeug.security import check_password_hash, generate_password_hash
from deepseek import DeepSeekError, deepseek_configurada, responder as responder_deepseek
from luna import Luna

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / '.env')

app = Flask(__name__, static_folder='public', static_url_path='')
app.secret_key = os.environ.get('FLASK_SECRET_KEY') or secrets.token_hex(32)
if not os.environ.get('FLASK_SECRET_KEY'):
    app.logger.warning("FLASK_SECRET_KEY não configurada; sessões serão invalidadas ao reiniciar.")

DATA_DIR = (
    Path('/tmp/luna-dados')
    if os.environ.get('VERCEL')
    else BASE_DIR / 'dados'
)
USUARIOS_PATH = DATA_DIR / 'usuarios.json'


MATERIAS_PADRAO = {
    'portugues': {'nome': 'Português', 'icone': '📝'},
    'matematica': {'nome': 'Matemática', 'icone': '🔢'},
    'ciencias': {'nome': 'Ciências', 'icone': '🔬'},
    'historia': {'nome': 'História', 'icone': '📚'},
    'geografia': {'nome': 'Geografia', 'icone': '🌍'},
    'ingles': {'nome': 'Inglês', 'icone': '🌐'},
}

# ── Helpers de dados ─────────────────────────────────────────────────────
def carregar_usuarios():
    if not USUARIOS_PATH.exists():
        return {}
    with open(USUARIOS_PATH, encoding='utf-8') as f:
        return json.load(f)

def salvar_usuarios(usuarios):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(USUARIOS_PATH, 'w', encoding='utf-8') as f:
        json.dump(usuarios, f, ensure_ascii=False, indent=2)


def chave_usuario(nome):
    return re.sub(r'\s+', '_', nome.lower().strip())


def normalizar_slug(nome):
    texto = unicodedata.normalize('NFKD', nome)
    texto = ''.join(caractere for caractere in texto if not unicodedata.combining(caractere))
    return re.sub(r'[^a-z0-9]+', '_', texto.lower()).strip('_')[:40]


def normalizar_materias(usuario):
    materias = usuario.get('materias')
    if isinstance(materias, dict):
        resultado = {}
        for slug, dados in materias.items():
            if not isinstance(dados, dict) or not isinstance(dados.get('nome'), str):
                continue
            notas = dados.get('notas', [])
            if not isinstance(notas, list):
                notas = []
            notas_validas = []
            for nota in notas:
                if isinstance(nota, (int, float)) and 0 <= nota <= 10:
                    notas_validas.append({'valor': float(nota), 'titulo': '', 'data': ''})
                elif isinstance(nota, dict) and isinstance(nota.get('valor'), (int, float)) and 0 <= nota['valor'] <= 10:
                    notas_validas.append({
                        'valor': float(nota['valor']),
                        'titulo': str(nota.get('titulo', ''))[:60],
                        'data': str(nota.get('data', ''))[:10],
                    })
            resultado[slug] = {
                'nome': dados['nome'][:40],
                'notas': notas_validas,
            }
        return resultado

    # Legacy numeric grades were prefilled examples; the old UI could not enter real grades.
    return {}


def usuario_atual():
    chave = session.get('user_key')
    if not chave:
        return None, None
    usuarios = carregar_usuarios()
    usuario = usuarios.get(chave)
    return (chave, usuario) if usuario else (None, None)


def perfil_publico(usuario):
    return {
        'nome': usuario['nome'],
        'serie': usuario.get('serie', ''),
        'ultimo_acesso': usuario.get('ultimo_acesso', []),
    }


def obter_materias_usuario(chave, usuario):
    materias = normalizar_materias(usuario)
    if materias != usuario.get('materias'):
        usuario['materias'] = materias
        usuario.pop('notas', None)
        usuarios = carregar_usuarios()
        usuarios[chave] = usuario
        salvar_usuarios(usuarios)
    return materias


def senha_valida(usuario, senha):
    armazenada = usuario.get('senha', '')
    if armazenada.startswith(('scrypt:', 'pbkdf2:')):
        return check_password_hash(armazenada, senha), False
    return secrets.compare_digest(armazenada, senha), True


def csrf_token():
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_urlsafe(32)
    return session['csrf_token']


@app.before_request
def proteger_post_com_csrf():
    if request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
        esperado = session.get('csrf_token', '')
        recebido = request.headers.get('X-CSRFToken') or request.form.get('csrf_token', '')
        if not esperado or not secrets.compare_digest(esperado, recebido):
            return ('Token de segurança inválido. Atualize a página e tente novamente.', 400)


@app.context_processor
def disponibilizar_token_csrf():
    return {'csrf_token': csrf_token}


# ── Rotas de autenticação ────────────────────────────────────────────────
@app.route('/')
def index():
    if 'aluno' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    erro = None
    aba = request.args.get('acao', 'entrar')
    if aba not in ('entrar', 'cadastrar'):
        aba = 'entrar'
    if request.method == 'POST':
        nome  = request.form.get('nome', '').strip()
        serie = request.form.get('serie', '').strip()
        senha = request.form.get('senha', '')
        acao  = request.form.get('acao', 'entrar')
        aba = acao if acao in ('entrar', 'cadastrar') else 'entrar'
        usuarios = carregar_usuarios()
        chave = chave_usuario(nome)
        usuario_existente = usuarios.get(chave) or next(
            (usuario for usuario in usuarios.values()
             if chave_usuario(usuario.get('nome', '')) == chave),
            None
        )
        chave_existente = next(
            (chave_db for chave_db, usuario in usuarios.items()
             if usuario is usuario_existente),
            None
        )

        if acao == 'cadastrar':
            if not nome or not serie or not senha:
                erro = 'Preencha todos os campos.'
            elif len(senha) < 8:
                erro = 'Crie uma senha com pelo menos 8 caracteres.'
            elif usuario_existente:
                erro = 'Já existe um aluno com esse nome. Tente fazer login.'
            else:
                usuarios[chave] = {
                    'nome': nome,
                    'serie': serie,
                    'senha': generate_password_hash(senha),
                    'materias': {},
                    'ultimo_acesso': []
                }
                salvar_usuarios(usuarios)
                session.clear()
                session['user_key'] = chave
                session['aluno'] = perfil_publico(usuarios[chave])
                csrf_token()
                return redirect(url_for('dashboard'))
        else:
            senha_correta = False
            precisa_migrar_senha = False
            if usuario_existente:
                senha_correta, precisa_migrar_senha = senha_valida(usuario_existente, senha)
            if usuario_existente and senha_correta:
                if precisa_migrar_senha:
                    usuario_existente['senha'] = generate_password_hash(senha)
                    salvar_usuarios(usuarios)
                session.clear()
                session['user_key'] = chave_existente
                session['aluno'] = perfil_publico(usuario_existente)
                csrf_token()
                return redirect(url_for('dashboard'))
            else:
                erro = 'Nome ou senha incorretos.'
    return render_template(
        'login.html',
        erro=erro,
        aba=aba,
        conta_excluida=request.args.get('conta_excluida') == '1',
    )

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ── Rotas principais ─────────────────────────────────────────────────────
@app.route('/dashboard')
def dashboard():
    chave, aluno = usuario_atual()
    if not aluno:
        return redirect(url_for('login'))
    materias = obter_materias_usuario(chave, aluno)
    cards = []
    todas_notas = []
    for slug, materia in materias.items():
        notas = materia['notas']
        valores = [nota['valor'] for nota in notas]
        media = sum(valores) / len(valores) if valores else None
        todas_notas.extend(valores)
        cards.append({
            'slug': slug,
            'nome': materia['nome'],
            'icone': MATERIAS_PADRAO.get(slug, {}).get('icone', '📘'),
            'media': media,
            'quantidade': len(notas),
        })
    media_geral = sum(todas_notas) / len(todas_notas) if todas_notas else None
    return render_template(
        'dashboard.html',
        aluno=perfil_publico(aluno),
        materias=cards,
        media_geral=media_geral,
        total_notas=len(todas_notas),
    )


@app.route('/notas', methods=['GET', 'POST'])
def notas():
    chave, aluno = usuario_atual()
    if not aluno:
        return redirect(url_for('login'))
    materias = obter_materias_usuario(chave, aluno)
    erro = None
    sucesso = None

    if request.method == 'POST':
        acao = request.form.get('acao', '')
        if acao == 'adicionar_materia':
            nome = request.form.get('nome_materia', '').strip()
            slug = normalizar_slug(nome)
            if not nome or not slug or len(nome) > 40:
                erro = 'Digite um nome de matéria com até 40 caracteres.'
            elif len(materias) >= 30:
                erro = 'Você já cadastrou o limite de 30 matérias.'
            elif slug in materias or any(
                materia['nome'].casefold() == nome.casefold()
                for materia in materias.values()
            ):
                erro = 'Essa matéria já está na sua lista.'
            else:
                materias[slug] = {'nome': nome, 'notas': []}
                sucesso = 'Matéria adicionada. Quando tiver uma nota, você pode registrá-la aqui.'
        elif acao == 'adicionar_nota':
            slug = request.form.get('slug', '')
            materia = materias.get(slug)
            titulo = request.form.get('titulo', '').strip()
            valor_texto = request.form.get('valor', '').strip().replace(',', '.')
            data_texto = request.form.get('data', '').strip()
            try:
                valor = float(valor_texto)
            except ValueError:
                valor = -1
            data_valida = True
            if data_texto:
                try:
                    date.fromisoformat(data_texto)
                except ValueError:
                    data_valida = False
            if not materia:
                erro = 'Não encontrei essa matéria na sua lista.'
            elif not 0 <= valor <= 10:
                erro = 'A nota deve ser um número entre 0 e 10.'
            elif len(titulo) > 60:
                erro = 'O nome da avaliação deve ter até 60 caracteres.'
            elif not data_valida:
                erro = 'Informe uma data válida.'
            elif len(materia['notas']) >= 50:
                erro = 'Essa matéria já tem o limite de 50 avaliações.'
            else:
                materia['notas'].append({
                    'valor': valor,
                    'titulo': titulo,
                    'data': data_texto,
                })
                sucesso = 'Nota registrada.'
        elif acao == 'remover_materia':
            slug = request.form.get('slug', '')
            if slug not in materias:
                erro = 'Essa matéria não está na sua lista.'
            else:
                del materias[slug]
                sucesso = 'Matéria removida.'
        elif acao == 'remover_nota':
            slug = request.form.get('slug', '')
            materia = materias.get(slug)
            try:
                indice = int(request.form.get('indice', '-1'))
            except ValueError:
                indice = -1
            if not materia or not 0 <= indice < len(materia['notas']):
                erro = 'Não encontrei essa avaliação para remover.'
            else:
                materia['notas'].pop(indice)
                sucesso = 'Avaliação removida.'
        else:
            erro = 'Ação inválida.'

        if not erro:
            usuarios = carregar_usuarios()
            aluno['materias'] = materias
            aluno.pop('notas', None)
            usuarios[chave] = aluno
            salvar_usuarios(usuarios)
            flash(sucesso, 'success')
            return redirect(url_for('notas'))

    lista_materias = [
        {'slug': slug, **materia}
        for slug, materia in sorted(materias.items(), key=lambda item: item[1]['nome'].casefold())
    ]
    return render_template(
        'notas.html',
        aluno=perfil_publico(aluno),
        materias=lista_materias,
        erro=erro,
        sucesso=(get_flashed_messages(category_filter=['success']) or [None])[-1],
    )


@app.route('/perfil', methods=['GET', 'POST'])
def perfil():
    chave, aluno = usuario_atual()
    if not aluno:
        return redirect(url_for('login'))
    erro = None
    sucesso = None

    if request.method == 'POST':
        acao = request.form.get('acao', '')
        if acao == 'atualizar_perfil':
            nome = request.form.get('nome', '').strip()
            serie = request.form.get('serie', '').strip()
            usuarios = carregar_usuarios()
            nome_em_uso = any(
                outra_chave != chave and chave_usuario(usuario.get('nome', '')) == chave_usuario(nome)
                for outra_chave, usuario in usuarios.items()
            )
            if not nome or len(nome) > 80 or not serie or len(serie) > 60:
                erro = 'Informe um nome (até 80 caracteres) e uma série válidos.'
            elif nome_em_uso:
                erro = 'Esse nome já está associado a outra conta.'
            else:
                aluno['nome'] = nome
                aluno['serie'] = serie
                usuarios[chave] = aluno
                salvar_usuarios(usuarios)
                session['aluno'] = perfil_publico(aluno)
                sucesso = 'Seus dados foram atualizados.'
                flash(sucesso, 'success')
                return redirect(url_for('perfil'))
        elif acao == 'alterar_senha':
            senha_atual = request.form.get('senha_atual', '')
            senha_nova = request.form.get('senha_nova', '')
            confirmar = request.form.get('confirmar_senha', '')
            senha_correta, _ = senha_valida(aluno, senha_atual)
            if not senha_correta:
                erro = 'A senha atual não confere.'
            elif len(senha_nova) < 8:
                erro = 'A nova senha precisa ter pelo menos 8 caracteres.'
            elif senha_nova != confirmar:
                erro = 'A confirmação da nova senha está diferente.'
            else:
                usuarios = carregar_usuarios()
                aluno['senha'] = generate_password_hash(senha_nova)
                usuarios[chave] = aluno
                salvar_usuarios(usuarios)
                sucesso = 'Senha alterada. Ela foi armazenada de forma protegida.'
                flash(sucesso, 'success')
                return redirect(url_for('perfil'))
        elif acao == 'excluir_conta':
            senha_atual = request.form.get('senha_atual', '')
            confirmacao = request.form.get('confirmacao', '').strip()
            senha_correta, _ = senha_valida(aluno, senha_atual)
            if not senha_correta:
                erro = 'A senha não confere; a conta não foi excluída.'
            elif confirmacao != 'EXCLUIR':
                erro = 'Digite EXCLUIR para confirmar a exclusão permanente.'
            else:
                usuarios = carregar_usuarios()
                usuarios.pop(chave, None)
                salvar_usuarios(usuarios)
                session.clear()
                return redirect(url_for('login', conta_excluida='1'))
        else:
            erro = 'Ação inválida.'

    return render_template(
        'perfil.html',
        aluno=perfil_publico(aluno),
        erro=erro,
        sucesso=(get_flashed_messages(category_filter=['success']) or [None])[-1],
    )


MATERIAS_INFO = {
    'portugues':  {'nome': 'Português',   'icone': '📝', 'cor': '#fff'},
    'matematica': {'nome': 'Matemática',  'icone': '🔢', 'cor': '#fff'},
    'ciencias':   {'nome': 'Ciências',    'icone': '🔬', 'cor': '#fff'},
    'historia':   {'nome': 'História',    'icone': '📚', 'cor': '#fff'},
    'geografia':  {'nome': 'Geografia',   'icone': '🌍', 'cor': '#fff'},
    'ingles':     {'nome': 'Inglês',      'icone': '🌐', 'cor': '#fff'},
}

CONTEUDOS = {
    'matematica': {
        'topicos': [
            {
                'titulo': 'Frações no dia a dia',
                'texto': 'Uma fração representa uma parte de um todo. Pense em uma pizza dividida em 8 fatias — se você comer 3, comeu 3/8 da pizza.',
                'exemplo': 'Exemplo real: Uma garrafa de 1 litro tem 1000ml. Beber 250ml é beber 1/4 da garrafa.',
                'formula': 'Numerador / Denominador = Parte / Todo'
            },
            {
                'titulo': 'Porcentagem e Descontos',
                'texto': 'Porcentagem significa "por cem". Muito usada em descontos, juros, notas e estatísticas.',
                'exemplo': 'Exemplo real: Um tênis de R$200 com 30% de desconto. 30% de 200 = 60. Valor final: R$140.',
                'formula': '% = (Valor × Porcentagem) ÷ 100'
            },
            {
                'titulo': 'Equações do 1º Grau',
                'texto': 'Uma equação é como um quebra-cabeça matemático: você precisa descobrir o valor de x.',
                'exemplo': 'Exemplo real: Você tem R$50 e quer comprar camisetas de R$15. Quantas cabe? 15x = 50 → x = 3 (sobram R$5).',
                'formula': 'ax + b = c → x = (c - b) / a'
            },
        ],
        'exercicios': [
            {'pergunta': 'Uma loja dá 20% de desconto em um produto de R$150. Qual o preço final?', 'resposta': 'R$120 (20% de 150 = 30 → 150 - 30 = 120)'},
            {'pergunta': 'Resolva: 3x + 6 = 18', 'resposta': 'x = 4 (3x = 18-6 = 12 → x = 12/3 = 4)'},
            {'pergunta': 'Uma pizza tem 8 fatias. João comeu 3. Que fração ele comeu?', 'resposta': '3/8 da pizza'},
        ]
    },
    'portugues': {
        'topicos': [
            {
                'titulo': 'Como fazer uma boa redação',
                'texto': 'Uma boa redação tem estrutura clara: Introdução (apresenta o tema), Desenvolvimento (argumentos) e Conclusão (solução/reflexão).',
                'exemplo': 'Exemplo: Para escrever sobre "tecnologia e jovens", introduza o tema, apresente 2 argumentos com exemplos reais e conclua com uma reflexão.',
                'formula': 'Introdução → 2 parágrafos de desenvolvimento → Conclusão'
            },
            {
                'titulo': 'Sujeito e Predicado',
                'texto': 'O sujeito é sobre quem/o que a frase fala. O predicado é o que se diz sobre o sujeito (sempre contém um verbo).',
                'exemplo': '"Os alunos estudaram muito." → Sujeito: Os alunos | Predicado: estudaram muito.',
                'formula': 'Dica: Pergunte "Quem?" ao verbo → a resposta é o sujeito.'
            },
            {
                'titulo': 'Uso da Crase',
                'texto': 'Crase é a fusão da preposição "a" com o artigo feminino "a". Aparece antes de palavras femininas precedidas de preposição.',
                'exemplo': '"Vou à escola" (à = a + a). Teste: troque por masculino → "Vou ao colégio". Se couber "ao", usa crase.',
                'formula': 'Se couber "ao" no masculino → usa crase no feminino.'
            },
        ],
        'exercicios': [
            {'pergunta': 'Identifique sujeito e predicado: "A professora explicou a matéria com cuidado."', 'resposta': 'Sujeito: A professora | Predicado: explicou a matéria com cuidado'},
            {'pergunta': 'Complete com "a" ou "à": "Fui ___ biblioteca ontem."', 'resposta': 'à biblioteca (usa crase — feminino + preposição)'},
            {'pergunta': 'Qual a estrutura básica de uma dissertação?', 'resposta': 'Introdução + Desenvolvimento (2 parágrafos) + Conclusão'},
        ]
    },
    'ciencias': {
        'topicos': [
            {
                'titulo': 'Fotossíntese — a fábrica das plantas',
                'texto': 'Fotossíntese é o processo que plantas usam para produzir seu próprio alimento usando luz solar, água e gás carbônico.',
                'exemplo': 'Exemplo real: As árvores de uma cidade absorvem CO₂ (poluição) e liberam O₂ que respiramos. São verdadeiras purificadoras de ar!',
                'formula': '6CO₂ + 6H₂O + luz → C₆H₁₂O₆ (glicose) + 6O₂'
            },
            {
                'titulo': 'A Célula — unidade da vida',
                'texto': 'Toda vida é feita de células. Elas têm membrana (proteção), citoplasma (meio interno) e núcleo (controle/DNA).',
                'exemplo': 'Exemplo real: Seu corpo tem ~37 trilhões de células. Cada uma é como uma fábrica independente com funções específicas.',
                'formula': 'Célula animal: membrana + núcleo + organelas (sem parede celular)'
            },
            {
                'titulo': 'Sistema Digestório',
                'texto': 'O sistema digestório transforma alimentos em nutrientes que o corpo pode usar. É uma linha de produção biológica.',
                'exemplo': 'Exemplo real: Uma pizza que você come demora ~6-8 horas para ser totalmente digerida e os nutrientes absorvidos.',
                'formula': 'Boca → Esôfago → Estômago → Intestino Delgado → Intestino Grosso'
            },
        ],
        'exercicios': [
            {'pergunta': 'Quais são os ingredientes que a planta usa na fotossíntese?', 'resposta': 'Luz solar + água (H₂O) + gás carbônico (CO₂)'},
            {'pergunta': 'Qual a função do núcleo celular?', 'resposta': 'Controlar as atividades da célula e guardar o DNA (material genético)'},
            {'pergunta': 'O que a planta libera como subproduto da fotossíntese?', 'resposta': 'Oxigênio (O₂)'},
        ]
    },
    'historia': {
        'topicos': [
            {
                'titulo': 'Brasil Colônia (1500–1822)',
                'texto': 'Por 322 anos, o Brasil foi colônia de Portugal. Esse período moldou nossa língua, cultura e desigualdades sociais.',
                'exemplo': 'Exemplo real: O português que falamos hoje é herança direta desse período. Assim como muitas tradições culturais, culinárias e religiosas.',
                'formula': '1500 (chegada) → 1530 (colonização efetiva) → 1822 (Independência)'
            },
            {
                'titulo': 'Abolição da Escravidão',
                'texto': 'A escravidão no Brasil durou de ~1550 a 1888 — mais de 300 anos. A resistência nunca parou: Quilombo dos Palmares, revoltas, fugas.',
                'exemplo': 'Exemplo real: O Brasil foi o último país das Américas a abolir a escravidão (1888) e o que mais recebeu africanos escravizados (~40% do total).',
                'formula': 'Lei do Ventre Livre (1871) → Lei dos Sexagenários (1885) → Lei Áurea (1888)'
            },
            {
                'titulo': 'República Brasileira',
                'texto': 'A República foi proclamada em 15 de novembro de 1889 pelo Marechal Deodoro da Fonseca, encerrando o Império de D. Pedro II.',
                'exemplo': 'Exemplo real: O Hino Nacional que cantamos hoje foi composto durante o Império, mas a letra republicana foi acrescentada depois.',
                'formula': 'Império (1822–1889) → República Velha → Era Vargas → Ditadura Militar → Nova República'
            },
        ],
        'exercicios': [
            {'pergunta': 'Em que ano o Brasil proclamou sua Independência?', 'resposta': '1822, pelo príncipe D. Pedro I às margens do Rio Ipiranga'},
            {'pergunta': 'Qual lei aboliu definitivamente a escravidão no Brasil?', 'resposta': 'Lei Áurea, assinada pela Princesa Isabel em 13 de maio de 1888'},
            {'pergunta': 'O que foi o Quilombo dos Palmares?', 'resposta': 'Grande comunidade de africanos escravizados fugidos no séc. XVII, liderada por Zumbi dos Palmares'},
        ]
    },
    'geografia': {
        'topicos': [
            {
                'titulo': 'Biomas Brasileiros',
                'texto': 'O Brasil tem 6 biomas: Amazônia, Cerrado, Mata Atlântica, Caatinga, Pampa e Pantanal. Cada um com fauna e flora únicas.',
                'exemplo': 'Exemplo real: O Cerrado é chamado de "berço das águas" — nasce dele os principais rios que abastecem o Brasil inteiro.',
                'formula': 'Amazônia (49%) > Cerrado (22%) > Caatinga (10%) > Mata Atlântica (13%) > Pampa (2%) > Pantanal (2%)'
            },
            {
                'titulo': 'Regiões do Brasil',
                'texto': 'O Brasil é dividido em 5 regiões: Norte, Nordeste, Centro-Oeste, Sudeste e Sul. Cada uma tem características geográficas, climáticas e culturais próprias.',
                'exemplo': 'Exemplo real: O Sudeste (SP, RJ, MG, ES) concentra ~42% da população e ~55% do PIB brasileiro.',
                'formula': 'Norte + Nordeste + Centro-Oeste + Sudeste + Sul = Brasil'
            },
            {
                'titulo': 'Coordenadas Geográficas',
                'texto': 'Latitude mede a distância do Equador (norte/sul). Longitude mede a distância do Meridiano de Greenwich (leste/oeste).',
                'exemplo': 'Exemplo real: O GPS do seu celular usa exatamente latitude e longitude para saber onde você está no planeta!',
                'formula': 'Coordenadas: Latitude (-90° a +90°) × Longitude (-180° a +180°)'
            },
        ],
        'exercicios': [
            {'pergunta': 'Qual é o maior bioma do Brasil?', 'resposta': 'Amazônia, ocupando cerca de 49% do território nacional'},
            {'pergunta': 'Em qual região do Brasil está localizado o Pantanal?', 'resposta': 'Centro-Oeste (principalmente Mato Grosso e Mato Grosso do Sul)'},
            {'pergunta': 'O que mede a latitude de um ponto na Terra?', 'resposta': 'A distância angular em relação à linha do Equador (norte ou sul)'},
        ]
    },
    'ingles': {
        'topicos': [
            {
                'titulo': 'Simple Present — Rotinas',
                'texto': 'Usado para falar de hábitos, rotinas e fatos permanentes. Com he/she/it, adiciona-se -s ou -es ao verbo.',
                'exemplo': 'Exemplo real: "I study English every day." (Eu estudo inglês todo dia.) / "She works at a school." (Ela trabalha numa escola.)',
                'formula': 'I/You/We/They + verbo | He/She/It + verbo+s'
            },
            {
                'titulo': 'Simple Past — Passado',
                'texto': 'Usado para falar de ações concluídas no passado. Verbos regulares recebem -ed; irregulares têm formas próprias.',
                'exemplo': 'Exemplo real: "Yesterday I watched a movie." (Ontem eu assisti um filme.) / "She went to the store." (Ela foi à loja.)',
                'formula': 'Regular: verb + ed | Irregular: forma própria (go→went, eat→ate, see→saw)'
            },
            {
                'titulo': 'Pronomes Pessoais',
                'texto': 'Os pronomes em inglês substituem os nomes. São: I, You, He, She, It, We, You (pl.), They.',
                'exemplo': 'Exemplo real: Em inglês não existe "ele" e "ela" para objetos — tudo vira "it". Ex: "The phone is new. It is mine." (O celular é novo. Ele é meu.)',
                'formula': 'Singular: I, You, He, She, It | Plural: We, You, They'
            },
        ],
        'exercicios': [
            {'pergunta': 'Complete: "He ___ (play) soccer on weekends."', 'resposta': 'plays (3ª pessoa do singular: play + s = plays)'},
            {'pergunta': 'Passe para o passado: "I eat lunch at noon."', 'resposta': 'I ate lunch at noon. (eat é verbo irregular → ate)'},
            {'pergunta': 'Traduza: "They study at night."', 'resposta': 'Eles/Elas estudam à noite.'},
        ]
    },
}

@app.route('/materia/<nome_materia>')
def materia(nome_materia):
    chave, aluno = usuario_atual()
    if not aluno:
        return redirect(url_for('login'))
    materias = obter_materias_usuario(chave, aluno)
    if nome_materia not in materias:
        return redirect(url_for('dashboard'))
    info = MATERIAS_INFO.get(nome_materia, {
        'nome': materias[nome_materia]['nome'],
        'icone': '📘',
        'cor': '#fff',
    })
    conteudo = CONTEUDOS.get(nome_materia, {'topicos': [], 'exercicios': []})

    historico = aluno.get('ultimo_acesso', [])
    if nome_materia in historico:
        historico.remove(nome_materia)
    historico.insert(0, nome_materia)
    aluno['ultimo_acesso'] = historico[:3]
    usuarios = carregar_usuarios()
    usuarios[chave] = aluno
    salvar_usuarios(usuarios)
    session['aluno'] = perfil_publico(aluno)

    return render_template('materia.html',
                           aluno=aluno,
                           materia=nome_materia,
                           info=info,
                           conteudo=conteudo,
                           materias_info=MATERIAS_INFO,
                           ia_ativa=deepseek_configurada())

# ── Chat API ─────────────────────────────────────────────────────────────
@app.route('/chat')
def chat():
    _, aluno = usuario_atual()
    if not aluno:
        return redirect(url_for('login'))
    if 'historico_chat' not in session:
        session['historico_chat'] = []
    luna = Luna(aluno['nome'], aluno.get('serie', ''))
    boas_vindas = luna.mensagem_boas_vindas() if not session['historico_chat'] else None
    return render_template('chat.html',
                           aluno=perfil_publico(aluno),
                           historico=session['historico_chat'],
                           boas_vindas=boas_vindas,
                           ia_ativa=deepseek_configurada())

@app.route('/api/chat', methods=['POST'])
def api_chat():
    _, aluno = usuario_atual()
    if not aluno:
        return jsonify({'erro': 'Não autenticado'}), 401
    dados = request.get_json()
    mensagem = (dados or {}).get('mensagem', '').strip()
    materia_contexto = (dados or {}).get('materia', None)
    if not mensagem:
        return jsonify({'resposta': 'Me manda sua dúvida! 😊'})
    if len(mensagem) > 4000:
        return jsonify({'erro': 'A mensagem deve ter no máximo 4.000 caracteres.'}), 400
    luna = Luna(aluno['nome'], aluno.get('serie', ''))
    if deepseek_configurada():
        try:
            resposta = responder_deepseek(
                mensagem,
                session.get('historico_chat', []),
                materia_contexto,
            )
        except DeepSeekError as error:
            app.logger.warning("Falha na resposta do DeepSeek: %s", error)
            return jsonify({'erro': str(error)}), 502
    else:
        resposta = luna.responder(mensagem, materia_contexto)
    if 'historico_chat' not in session:
        session['historico_chat'] = []
    historico = list(session['historico_chat'])
    historico.append({'tipo': 'aluno', 'texto': mensagem})
    historico.append({'tipo': 'luna',  'texto': resposta})
    session['historico_chat'] = historico[-30:]
    session.modified = True
    return jsonify({'resposta': resposta})

@app.route('/api/limpar_chat', methods=['POST'])
def limpar_chat():
    session['historico_chat'] = []
    session.modified = True
    return jsonify({'ok': True})

if __name__ == '__main__':
    print("\n🌙 Luna — Sistema Educacional com IA")
    print("━" * 40)
    print("Acesse: http://localhost:5000")
    print("Para parar: Ctrl+C\n")
    app.run(debug=True, port=5000)
