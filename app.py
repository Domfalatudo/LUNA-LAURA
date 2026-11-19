"""
app.py — Servidor Flask do sistema educacional Luna
Execute: python app.py
Acesse:  http://localhost:5000
"""
from flask import (Flask, abort, render_template, request,
                   session, redirect, url_for, jsonify, flash, get_flashed_messages)
import json
import os
import re
import secrets
import unicodedata
from datetime import date, datetime
from pathlib import Path
from dotenv import load_dotenv
from werkzeug.security import check_password_hash, generate_password_hash
from groq import (
    GroqError,
    gerar_json as gerar_json_groq,
    groq_configurada,
    responder_com_ferramentas,
)
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

FERRAMENTAS_ESTUDO = [
    {
        'type': 'function',
        'function': {
            'name': 'adicionar_materia',
            'description': 'Adiciona uma matéria à lista pessoal do aluno quando ele pedir.',
            'parameters': {
                'type': 'object',
                'properties': {'nome': {'type': 'string'}},
                'required': ['nome'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'renomear_materia',
            'description': 'Renomeia uma matéria existente quando o aluno pedir.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'materia': {'type': 'string', 'description': 'Nome atual exato'},
                    'novo_nome': {'type': 'string'},
                },
                'required': ['materia', 'novo_nome'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'remover_materia',
            'description': 'Remove uma matéria e suas notas somente se o aluno pedir explicitamente.',
            'parameters': {
                'type': 'object',
                'properties': {'materia': {'type': 'string', 'description': 'Nome exato'}},
                'required': ['materia'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'registrar_nota',
            'description': 'Registra uma nota informada pelo aluno em uma matéria existente.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'materia': {'type': 'string', 'description': 'Nome exato da matéria'},
                    'valor': {'type': 'number', 'description': 'Nota de 0 a 10'},
                    'titulo': {'type': 'string', 'description': 'Nome da avaliação, se informado'},
                    'data': {'type': 'string', 'description': 'Data ISO YYYY-MM-DD, se informada'},
                },
                'required': ['materia', 'valor'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'editar_nota',
            'description': 'Edita uma nota existente. Use o índice exibido no contexto do aluno.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'materia': {'type': 'string'},
                    'indice': {'type': 'integer', 'description': 'Índice da nota, começando em 1'},
                    'valor': {'type': 'number'},
                    'titulo': {'type': 'string'},
                    'data': {'type': 'string', 'description': 'Data ISO YYYY-MM-DD'},
                },
                'required': ['materia', 'indice'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'remover_nota',
            'description': 'Remove uma nota somente se o aluno pedir explicitamente.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'materia': {'type': 'string'},
                    'indice': {'type': 'integer', 'description': 'Índice da nota, começando em 1'},
                },
                'required': ['materia', 'indice'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'criar_quiz',
            'description': 'Gera e salva um quiz quando o aluno pedir.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'materia': {'type': 'string'},
                    'assunto': {'type': 'string'},
                    'quantidade': {'type': 'integer', 'description': 'De 3 a 10 questões'},
                },
                'required': ['materia', 'assunto', 'quantidade'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'criar_flashcards',
            'description': 'Gera e salva flashcards quando o aluno pedir.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'materia': {'type': 'string'},
                    'assunto': {'type': 'string'},
                    'quantidade': {'type': 'integer', 'description': 'De 3 a 20 cartões'},
                },
                'required': ['materia', 'assunto', 'quantidade'],
            },
        },
    },
    {
        'type': 'function',
        'function': {
            'name': 'registrar_sessao_estudo',
            'description': 'Registra minutos de estudo que o aluno disse explicitamente ter feito.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'minutos': {'type': 'integer', 'description': 'De 5 a 240 minutos'},
                    'assunto': {'type': 'string', 'description': 'O que estudou, se informado'},
                },
                'required': ['minutos'],
            },
        },
    },
]


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


def salvar_aluno(chave, aluno):
    usuarios = carregar_usuarios()
    if chave not in usuarios:
        raise RuntimeError('A conta do aluno não está mais disponível.')
    usuarios[chave] = aluno
    salvar_usuarios(usuarios)


def data_hora_atual():
    return datetime.now().astimezone().isoformat(timespec='seconds')


def nova_conversa(mensagens=None):
    criada = data_hora_atual()
    primeiras = mensagens or []
    titulo = next(
        (item.get('texto', '').strip() for item in primeiras
         if isinstance(item, dict) and item.get('tipo') == 'aluno'),
        'Nova conversa',
    )
    return {
        'id': secrets.token_urlsafe(12),
        'titulo': (titulo[:54] + '…') if len(titulo) > 55 else (titulo or 'Nova conversa'),
        'criada_em': criada,
        'atualizada_em': criada,
        'mensagens': primeiras,
    }


def conversas_do_aluno(aluno):
    conversas = aluno.get('conversas')
    if not isinstance(conversas, list):
        conversas = []
    validas = []
    for conversa in conversas:
        if (
            isinstance(conversa, dict)
            and isinstance(conversa.get('id'), str)
            and isinstance(conversa.get('mensagens'), list)
        ):
            validas.append(conversa)
    aluno['conversas'] = validas
    return validas


def preferencia_do_aluno(aluno):
    padrao = {
        'meta_diaria': 30,
        'estilo_resposta': 'equilibrada',
        'usar_exemplos': True,
    }
    valor = aluno.get('preferencias')
    if not isinstance(valor, dict):
        valor = {}
    padrao['meta_diaria'] = valor.get('meta_diaria', 30)
    if padrao['meta_diaria'] not in (15, 30, 45, 60):
        padrao['meta_diaria'] = 30
    if valor.get('estilo_resposta') in ('curta', 'equilibrada', 'detalhada'):
        padrao['estilo_resposta'] = valor['estilo_resposta']
    padrao['usar_exemplos'] = valor.get('usar_exemplos') is not False
    return padrao

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


def resolver_materia(materias, nome):
    if not isinstance(nome, str):
        return None, None
    texto = nome.strip()
    slug = normalizar_slug(texto)
    if slug in materias:
        return slug, materias[slug]
    for chave, materia in materias.items():
        if materia['nome'].casefold() == texto.casefold():
            return chave, materia
    return None, None


def _validar_data_nota(valor):
    if valor in (None, ''):
        return ''
    if not isinstance(valor, str):
        raise ValueError('A data precisa estar no formato AAAA-MM-DD.')
    try:
        date.fromisoformat(valor)
    except ValueError:
        raise ValueError('A data precisa estar no formato AAAA-MM-DD.') from None
    return valor


def _gerar_quiz(chave, aluno, slug, assunto, quantidade):
    if isinstance(quantidade, bool) or not isinstance(quantidade, int) or not 3 <= quantidade <= 10:
        raise ValueError('O quiz precisa ter de 3 a 10 questões.')
    if not isinstance(assunto, str) or not assunto.strip() or len(assunto.strip()) > 120:
        raise ValueError('Informe um assunto com até 120 caracteres.')
    materia = normalizar_materias(aluno).get(slug)
    if not materia:
        raise ValueError('A matéria escolhida não existe.')
    dados = gerar_json_groq(
        f"Crie exatamente {quantidade} questões de múltipla escolha para a matéria "
        f"{materia['nome']} sobre {assunto.strip()}. Adeque a linguagem à série "
        f"{aluno.get('serie', 'escolar')}. Cada questão deve ter 4 opções, uma única "
        "resposta correta indicada pelo índice inteiro de 0 a 3, e uma explicação curta. "
        'Retorne JSON neste formato: {"titulo":"...", "questoes":['
        '{"pergunta":"...", "opcoes":["...","...","...","..."], '
        '"correta":0, "explicacao":"..."}]}'
    )
    questoes = dados.get('questoes')
    if not isinstance(questoes, list) or len(questoes) != quantidade:
        raise GroqError('A Groq não gerou a quantidade de questões pedida. Tente novamente.')
    validadas = []
    for questao in questoes:
        if not isinstance(questao, dict):
            raise GroqError('A Groq gerou uma questão inválida. Tente novamente.')
        pergunta = questao.get('pergunta')
        opcoes = questao.get('opcoes')
        correta = questao.get('correta')
        explicacao = questao.get('explicacao', '')
        if (
            not isinstance(pergunta, str) or not pergunta.strip()
            or len(pergunta) > 500
            or not isinstance(opcoes, list) or len(opcoes) != 4
            or any(not isinstance(opcao, str) or not opcao.strip() or len(opcao) > 240 for opcao in opcoes)
            or isinstance(correta, bool) or not isinstance(correta, int) or not 0 <= correta < 4
            or not isinstance(explicacao, str) or len(explicacao) > 800
        ):
            raise GroqError('A Groq gerou uma questão inválida. Tente novamente.')
        validadas.append({
            'pergunta': pergunta.strip(),
            'opcoes': [opcao.strip() for opcao in opcoes],
            'correta': correta,
            'explicacao': explicacao.strip(),
        })
    titulo = dados.get('titulo')
    if not isinstance(titulo, str) or not titulo.strip():
        titulo = f"Quiz de {materia['nome']}: {assunto.strip()}"
    quiz = {
        'id': secrets.token_urlsafe(12),
        'titulo': titulo.strip()[:100],
        'materia_slug': slug,
        'materia': materia['nome'],
        'assunto': assunto.strip(),
        'criado_em': data_hora_atual(),
        'questoes': validadas,
    }
    recursos_usuario(aluno, 'quizzes').insert(0, quiz)
    salvar_aluno(chave, aluno)
    return quiz


def _gerar_flashcards(chave, aluno, slug, assunto, quantidade):
    if isinstance(quantidade, bool) or not isinstance(quantidade, int) or not 3 <= quantidade <= 20:
        raise ValueError('O conjunto precisa ter de 3 a 20 flashcards.')
    if not isinstance(assunto, str) or not assunto.strip() or len(assunto.strip()) > 120:
        raise ValueError('Informe um assunto com até 120 caracteres.')
    materia = normalizar_materias(aluno).get(slug)
    if not materia:
        raise ValueError('A matéria escolhida não existe.')
    dados = gerar_json_groq(
        f"Crie exatamente {quantidade} flashcards de estudo para a matéria "
        f"{materia['nome']} sobre {assunto.strip()}, adequados à série "
        f"{aluno.get('serie', 'escolar')}. Cada cartão deve ter uma pergunta ou "
        "conceito curto na frente e uma resposta correta e clara no verso. "
        'Retorne JSON neste formato: {"titulo":"...", "cartoes":['
        '{"frente":"...", "verso":"..."}]}'
    )
    cartoes = dados.get('cartoes')
    if not isinstance(cartoes, list) or len(cartoes) != quantidade:
        raise GroqError('A Groq não gerou a quantidade de flashcards pedida. Tente novamente.')
    validados = []
    for cartao in cartoes:
        if not isinstance(cartao, dict):
            raise GroqError('A Groq gerou um flashcard inválido. Tente novamente.')
        frente, verso = cartao.get('frente'), cartao.get('verso')
        if (
            not isinstance(frente, str) or not frente.strip() or len(frente) > 300
            or not isinstance(verso, str) or not verso.strip() or len(verso) > 800
        ):
            raise GroqError('A Groq gerou um flashcard inválido. Tente novamente.')
        validados.append({'frente': frente.strip(), 'verso': verso.strip()})
    titulo = dados.get('titulo')
    if not isinstance(titulo, str) or not titulo.strip():
        titulo = f"Flashcards de {materia['nome']}: {assunto.strip()}"
    deck = {
        'id': secrets.token_urlsafe(12),
        'titulo': titulo.strip()[:100],
        'materia_slug': slug,
        'materia': materia['nome'],
        'assunto': assunto.strip(),
        'criado_em': data_hora_atual(),
        'cartoes': validados,
    }
    recursos_usuario(aluno, 'flashcards').insert(0, deck)
    salvar_aluno(chave, aluno)
    return deck


def contexto_aluno_para_ia(aluno):
    materias = normalizar_materias(aluno)
    resumo = []
    for slug, materia in materias.items():
        resumo.append({
            'slug': slug,
            'nome': materia['nome'],
            'notas': [
                {'indice': indice, **nota}
                for indice, nota in enumerate(materia['notas'], start=1)
            ],
        })
    return json.dumps({
        'materias': resumo,
        'meta_diaria_minutos': preferencia_do_aluno(aluno)['meta_diaria'],
        'minutos_estudados_hoje': minutos_estudados_hoje(aluno),
    }, ensure_ascii=False)


def minutos_estudados_hoje(aluno):
    hoje = date.today().isoformat()
    sessoes = aluno.get('sessoes_estudo')
    if not isinstance(sessoes, list):
        return 0
    return sum(
        sessao.get('minutos', 0)
        for sessao in sessoes
        if isinstance(sessao, dict)
        and isinstance(sessao.get('data'), str)
        and sessao['data'][:10] == hoje
        and isinstance(sessao.get('minutos'), int)
        and not isinstance(sessao.get('minutos'), bool)
    )


def registrar_sessao_estudo(chave, aluno, minutos, assunto=''):
    if isinstance(minutos, bool) or not isinstance(minutos, int) or not 5 <= minutos <= 240:
        raise ValueError('A sessão deve ter entre 5 e 240 minutos.')
    if not isinstance(assunto, str) or len(assunto.strip()) > 80:
        raise ValueError('O assunto deve ter até 80 caracteres.')
    sessoes = aluno.get('sessoes_estudo')
    if not isinstance(sessoes, list):
        sessoes = []
    sessoes.append({
        'minutos': minutos,
        'assunto': assunto.strip(),
        'data': data_hora_atual(),
    })
    aluno['sessoes_estudo'] = sessoes
    salvar_aluno(chave, aluno)
    return minutos_estudados_hoje(aluno)


def executar_ferramenta_estudo(chave, aluno, nome, argumentos):
    materias = normalizar_materias(aluno)
    try:
        if nome == 'registrar_sessao_estudo':
            total = registrar_sessao_estudo(
                chave, aluno, argumentos.get('minutos'), argumentos.get('assunto', '')
            )
            return {'ok': True, 'acao': nome, 'minutos_hoje': total}
        if nome == 'adicionar_materia':
            texto = argumentos.get('nome')
            slug = normalizar_slug(texto) if isinstance(texto, str) else ''
            if not isinstance(texto, str) or not texto.strip() or len(texto.strip()) > 40 or not slug:
                return {'ok': False, 'erro': 'O nome da matéria precisa ter até 40 caracteres.'}
            if len(materias) >= 30:
                return {'ok': False, 'erro': 'O limite é de 30 matérias.'}
            if slug in materias or any(m['nome'].casefold() == texto.strip().casefold() for m in materias.values()):
                return {'ok': False, 'erro': 'Essa matéria já está cadastrada.'}
            materias[slug] = {'nome': texto.strip(), 'notas': []}
            aluno['materias'] = materias
            salvar_aluno(chave, aluno)
            return {'ok': True, 'acao': nome, 'materia': texto.strip()}

        slug, materia = resolver_materia(materias, argumentos.get('materia'))
        if nome == 'renomear_materia':
            novo_nome = argumentos.get('novo_nome')
            novo_slug = normalizar_slug(novo_nome) if isinstance(novo_nome, str) else ''
            if not materia:
                return {'ok': False, 'erro': 'Matéria não encontrada. Confira a lista atual.'}
            if not isinstance(novo_nome, str) or not novo_nome.strip() or len(novo_nome.strip()) > 40 or not novo_slug:
                return {'ok': False, 'erro': 'O novo nome precisa ter até 40 caracteres.'}
            if novo_slug != slug and novo_slug in materias:
                return {'ok': False, 'erro': 'Já existe uma matéria com esse nome.'}
            del materias[slug]
            materia['nome'] = novo_nome.strip()
            materias[novo_slug] = materia
            aluno['materias'] = materias
            for colecao in ('quizzes', 'flashcards'):
                for item in recursos_usuario(aluno, colecao):
                    if item.get('materia_slug') == slug:
                        item['materia_slug'] = novo_slug
                        item['materia'] = novo_nome.strip()
            salvar_aluno(chave, aluno)
            return {'ok': True, 'acao': nome, 'materia': novo_nome.strip()}

        if nome == 'remover_materia':
            if not materia:
                return {'ok': False, 'erro': 'Matéria não encontrada.'}
            del materias[slug]
            aluno['materias'] = materias
            salvar_aluno(chave, aluno)
            return {'ok': True, 'acao': nome, 'materia': materia['nome']}

        if nome in ('registrar_nota', 'editar_nota', 'remover_nota'):
            if not materia:
                return {'ok': False, 'erro': 'Matéria não encontrada. Confira a lista atual.'}
            if nome == 'registrar_nota':
                valor = argumentos.get('valor')
                titulo = argumentos.get('titulo', '')
                data_texto = _validar_data_nota(argumentos.get('data', ''))
                if isinstance(valor, bool) or not isinstance(valor, (int, float)) or not 0 <= valor <= 10:
                    return {'ok': False, 'erro': 'A nota deve estar entre 0 e 10.'}
                if not isinstance(titulo, str) or len(titulo.strip()) > 60:
                    return {'ok': False, 'erro': 'O título da avaliação deve ter até 60 caracteres.'}
                if len(materia['notas']) >= 50:
                    return {'ok': False, 'erro': 'Essa matéria já tem 50 avaliações.'}
                materia['notas'].append({
                    'valor': float(valor),
                    'titulo': titulo.strip(),
                    'data': data_texto,
                })
            else:
                indice = argumentos.get('indice')
                if isinstance(indice, bool) or not isinstance(indice, int) or not 1 <= indice <= len(materia['notas']):
                    return {'ok': False, 'erro': 'Índice de avaliação inválido.'}
                nota = materia['notas'][indice - 1]
                if nome == 'remover_nota':
                    materia['notas'].pop(indice - 1)
                else:
                    valor = argumentos.get('valor')
                    titulo = argumentos.get('titulo')
                    data_texto = argumentos.get('data')
                    if valor is not None:
                        if isinstance(valor, bool) or not isinstance(valor, (int, float)) or not 0 <= valor <= 10:
                            return {'ok': False, 'erro': 'A nota deve estar entre 0 e 10.'}
                        nota['valor'] = float(valor)
                    if titulo is not None:
                        if not isinstance(titulo, str) or len(titulo.strip()) > 60:
                            return {'ok': False, 'erro': 'O título da avaliação deve ter até 60 caracteres.'}
                        nota['titulo'] = titulo.strip()
                    if data_texto is not None:
                        nota['data'] = _validar_data_nota(data_texto)
                    if valor is None and titulo is None and data_texto is None:
                        return {'ok': False, 'erro': 'Informe o que deve ser alterado na avaliação.'}
            aluno['materias'] = materias
            salvar_aluno(chave, aluno)
            return {
                'ok': True,
                'acao': nome,
                'materia': materia['nome'],
                'nota': None if nome == 'remover_nota' else materia['notas'][-1 if nome == 'registrar_nota' else indice - 1],
            }

        if nome in ('criar_quiz', 'criar_flashcards'):
            if not materia:
                return {'ok': False, 'erro': 'Cadastre primeiro essa matéria em Minhas matérias.'}
            assunto = argumentos.get('assunto')
            quantidade = argumentos.get('quantidade')
            recurso = (
                _gerar_quiz(chave, aluno, slug, assunto, quantidade)
                if nome == 'criar_quiz'
                else _gerar_flashcards(chave, aluno, slug, assunto, quantidade)
            )
            tipo = 'quiz' if nome == 'criar_quiz' else 'flashcards'
            return {
                'ok': True,
                'acao': nome,
                'titulo': recurso['titulo'],
                'url': f"/{tipo}/{recurso['id']}",
            }
    except ValueError as erro:
        return {'ok': False, 'erro': str(erro)}
    return {'ok': False, 'erro': 'Ação não reconhecida.'}


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
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    chave, aluno = usuario_atual()
    if not aluno:
        return redirect(url_for('login'))
    if request.method == 'POST':
        acao = request.form.get('acao')
        try:
            minutos = int(request.form.get('minutos', '0'))
        except ValueError:
            minutos = 0
        assunto = request.form.get('assunto', '').strip()
        if acao != 'registrar_sessao_estudo':
            return ('Ação inválida.', 400)
        try:
            registrar_sessao_estudo(chave, aluno, minutos, assunto)
        except ValueError as error:
            flash(str(error), 'error')
        else:
            flash('Sessão de estudo registrada. Cada passo conta.', 'success')
        return redirect(url_for('dashboard'))
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
    preferencias = preferencia_do_aluno(aluno)
    minutos_hoje = minutos_estudados_hoje(aluno)
    return render_template(
        'dashboard.html',
        aluno=perfil_publico(aluno),
        materias=cards,
        media_geral=media_geral,
        total_notas=len(todas_notas),
        preferencias=preferencias,
        minutos_hoje=minutos_hoje,
        progresso_meta=min(100, round(minutos_hoje / preferencias['meta_diaria'] * 100)),
        quizzes_count=len(recursos_usuario(aluno, 'quizzes')),
        flashcards_count=len(recursos_usuario(aluno, 'flashcards')),
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
                           ia_ativa=groq_configurada())


def recursos_usuario(aluno, colecao):
    itens = aluno.get(colecao)
    if not isinstance(itens, list):
        itens = []
    validos = [item for item in itens if isinstance(item, dict) and isinstance(item.get('id'), str)]
    aluno[colecao] = validos
    return validos


@app.route('/quizzes', methods=['GET', 'POST'])
def quizzes():
    chave, aluno = usuario_atual()
    if not aluno:
        return redirect(url_for('login'))
    erro = None
    materias = obter_materias_usuario(chave, aluno)
    if request.method == 'POST':
        slug = request.form.get('materia', '')
        assunto = request.form.get('assunto', '').strip()
        try:
            quantidade = int(request.form.get('quantidade', '5'))
            if slug not in materias:
                raise ValueError('Escolha uma matéria cadastrada.')
            quiz = _gerar_quiz(chave, aluno, slug, assunto, quantidade)
            return redirect(url_for('quiz_detail', quiz_id=quiz['id']))
        except ValueError as error:
            erro = str(error)
        except GroqError as error:
            erro = str(error)
    return render_template(
        'quizzes.html',
        aluno=perfil_publico(aluno),
        materias=[{'slug': slug, **item} for slug, item in materias.items()],
        quizzes=recursos_usuario(aluno, 'quizzes'),
        erro=erro,
    )


@app.route('/quizzes/<quiz_id>', methods=['GET', 'POST'])
def quiz_detail(quiz_id):
    chave, aluno = usuario_atual()
    if not aluno:
        return redirect(url_for('login'))
    itens = recursos_usuario(aluno, 'quizzes')
    quiz = next((item for item in itens if item['id'] == quiz_id), None)
    if not quiz:
        abort(404)
    if request.method == 'POST':
        aluno['quizzes'] = [item for item in itens if item['id'] != quiz_id]
        salvar_aluno(chave, aluno)
        return redirect(url_for('quizzes'))
    return render_template('quiz_detail.html', aluno=perfil_publico(aluno), quiz=quiz)


@app.route('/flashcards', methods=['GET', 'POST'])
def flashcards():
    chave, aluno = usuario_atual()
    if not aluno:
        return redirect(url_for('login'))
    erro = None
    materias = obter_materias_usuario(chave, aluno)
    if request.method == 'POST':
        slug = request.form.get('materia', '')
        assunto = request.form.get('assunto', '').strip()
        try:
            quantidade = int(request.form.get('quantidade', '8'))
            if slug not in materias:
                raise ValueError('Escolha uma matéria cadastrada.')
            deck = _gerar_flashcards(chave, aluno, slug, assunto, quantidade)
            return redirect(url_for('flashcards_detail', deck_id=deck['id']))
        except ValueError as error:
            erro = str(error)
        except GroqError as error:
            erro = str(error)
    return render_template(
        'flashcards.html',
        aluno=perfil_publico(aluno),
        materias=[{'slug': slug, **item} for slug, item in materias.items()],
        decks=recursos_usuario(aluno, 'flashcards'),
        erro=erro,
    )


@app.route('/flashcards/<deck_id>', methods=['GET', 'POST'])
def flashcards_detail(deck_id):
    chave, aluno = usuario_atual()
    if not aluno:
        return redirect(url_for('login'))
    itens = recursos_usuario(aluno, 'flashcards')
    deck = next((item for item in itens if item['id'] == deck_id), None)
    if not deck:
        abort(404)
    if request.method == 'POST':
        aluno['flashcards'] = [item for item in itens if item['id'] != deck_id]
        salvar_aluno(chave, aluno)
        return redirect(url_for('flashcards'))
    return render_template('flashcards_detail.html', aluno=perfil_publico(aluno), deck=deck)


@app.route('/configuracoes', methods=['GET', 'POST'])
def configuracoes():
    chave, aluno = usuario_atual()
    if not aluno:
        return redirect(url_for('login'))
    erro = None
    sucesso = None
    preferencias = preferencia_do_aluno(aluno)
    if request.method == 'POST':
        try:
            meta = int(request.form.get('meta_diaria', '30'))
        except ValueError:
            meta = 0
        estilo = request.form.get('estilo_resposta', '')
        if meta not in (15, 30, 45, 60):
            erro = 'Escolha uma meta diária entre 15 e 60 minutos.'
        elif estilo not in ('curta', 'equilibrada', 'detalhada'):
            erro = 'Escolha um estilo de resposta válido.'
        else:
            aluno['preferencias'] = {
                'meta_diaria': meta,
                'estilo_resposta': estilo,
                'usar_exemplos': request.form.get('usar_exemplos') == 'on',
            }
            salvar_aluno(chave, aluno)
            preferencias = preferencia_do_aluno(aluno)
            sucesso = 'Preferências salvas.'
    return render_template(
        'configuracoes.html',
        aluno=perfil_publico(aluno),
        preferencias=preferencias,
        erro=erro,
        sucesso=sucesso,
    )


# ── Chat API ─────────────────────────────────────────────────────────────
@app.route('/chat')
def chat():
    chave, aluno = usuario_atual()
    if not aluno:
        return redirect(url_for('login'))
    conversas = conversas_do_aluno(aluno)
    if not conversas:
        legado = session.pop('historico_chat', [])
        mensagens = [
            item for item in legado
            if isinstance(item, dict)
            and item.get('tipo') in ('aluno', 'luna')
            and isinstance(item.get('texto'), str)
        ] if isinstance(legado, list) else []
        conversas.append(nova_conversa(mensagens))
    pedida = request.args.get('conversa')
    ativa = next((item for item in conversas if item['id'] == pedida), None)
    if not ativa:
        ativa = next(
            (item for item in conversas if item['id'] == aluno.get('conversa_ativa')),
            conversas[-1],
        )
    aluno['conversa_ativa'] = ativa['id']
    salvar_aluno(chave, aluno)
    luna = Luna(aluno['nome'], aluno.get('serie', ''))
    conversas_ordenadas = sorted(
        conversas, key=lambda item: item.get('atualizada_em', ''), reverse=True
    )
    return render_template('chat.html',
                           aluno=perfil_publico(aluno),
                           historico=ativa['mensagens'],
                           conversas=conversas_ordenadas,
                           conversa_ativa=ativa,
                           boas_vindas=luna.mensagem_boas_vindas() if not ativa['mensagens'] else None,
                           ia_ativa=groq_configurada())


@app.route('/api/chat/conversas', methods=['POST'])
def api_nova_conversa():
    chave, aluno = usuario_atual()
    if not aluno:
        return jsonify({'erro': 'Não autenticado'}), 401
    conversas = conversas_do_aluno(aluno)
    conversa = nova_conversa()
    conversas.append(conversa)
    aluno['conversa_ativa'] = conversa['id']
    salvar_aluno(chave, aluno)
    return jsonify({'id': conversa['id']})


@app.route('/api/chat/conversas/<conversa_id>', methods=['DELETE'])
def api_excluir_conversa(conversa_id):
    chave, aluno = usuario_atual()
    if not aluno:
        return jsonify({'erro': 'Não autenticado'}), 401
    conversas = conversas_do_aluno(aluno)
    restantes = [item for item in conversas if item['id'] != conversa_id]
    if len(restantes) == len(conversas):
        return jsonify({'erro': 'Conversa não encontrada.'}), 404
    if not restantes:
        restantes.append(nova_conversa())
    aluno['conversas'] = restantes
    if aluno.get('conversa_ativa') == conversa_id:
        aluno['conversa_ativa'] = restantes[-1]['id']
    salvar_aluno(chave, aluno)
    return jsonify({'id': aluno['conversa_ativa']})


@app.route('/api/chat', methods=['POST'])
def api_chat():
    chave, aluno = usuario_atual()
    if not aluno:
        return jsonify({'erro': 'Não autenticado'}), 401
    dados = request.get_json(silent=True)
    if not isinstance(dados, dict):
        return jsonify({'erro': 'Envie uma mensagem válida.'}), 400
    mensagem = (dados or {}).get('mensagem', '').strip()
    materia_contexto = (dados or {}).get('materia', None)
    if not mensagem:
        return jsonify({'resposta': 'Me manda sua dúvida! 😊'})
    if len(mensagem) > 4000:
        return jsonify({'erro': 'A mensagem deve ter no máximo 4.000 caracteres.'}), 400
    conversas = conversas_do_aluno(aluno)
    conversa = next(
        (item for item in conversas if item['id'] == aluno.get('conversa_ativa')),
        None,
    )
    if conversa is None:
        conversa = nova_conversa()
        conversas.append(conversa)
        aluno['conversa_ativa'] = conversa['id']
    luna = Luna(aluno['nome'], aluno.get('serie', ''))
    if groq_configurada():
        try:
            resposta = responder_com_ferramentas(
                mensagem,
                conversa['mensagens'],
                materia_contexto,
                contexto_aluno_para_ia(aluno),
                preferencia_do_aluno(aluno),
                FERRAMENTAS_ESTUDO,
                lambda nome, argumentos: executar_ferramenta_estudo(
                    chave, aluno, nome, argumentos
                ),
            )
        except GroqError as error:
            app.logger.warning("Falha na resposta da Luna: %s", error)
            return jsonify({'erro': str(error)}), 502
    else:
        resposta = luna.responder(mensagem, materia_contexto)
    agora = data_hora_atual()
    conversa['mensagens'].append({'tipo': 'aluno', 'texto': mensagem, 'data': agora})
    conversa['mensagens'].append({'tipo': 'luna', 'texto': resposta, 'data': agora})
    if conversa['titulo'] == 'Nova conversa':
        conversa['titulo'] = (mensagem[:54] + '…') if len(mensagem) > 55 else mensagem
    conversa['atualizada_em'] = agora
    salvar_aluno(chave, aluno)
    return jsonify({'resposta': resposta, 'conversa_id': conversa['id']})

@app.route('/api/limpar_chat', methods=['POST'])
def limpar_chat():
    chave, aluno = usuario_atual()
    if not aluno:
        return jsonify({'erro': 'Não autenticado'}), 401
    conversa = next(
        (item for item in conversas_do_aluno(aluno)
         if item['id'] == aluno.get('conversa_ativa')),
        None,
    )
    if not conversa:
        return jsonify({'erro': 'Conversa não encontrada.'}), 404
    conversa['mensagens'] = []
    conversa['titulo'] = 'Nova conversa'
    conversa['atualizada_em'] = data_hora_atual()
    salvar_aluno(chave, aluno)
    return jsonify({'ok': True})

if __name__ == '__main__':
    print("━" * 40)
    print("Acesse: http://localhost:5000")
    app.run(debug=True, port=5000)
