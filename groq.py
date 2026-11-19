"""Integração da Luna com a API compatível com OpenAI da Groq."""
import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


API_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODEL = "openai/gpt-oss-20b"
SYSTEM_PROMPT = (
    "Você é Luna, uma assistente de estudos paciente e didática. "
    "Responda em português brasileiro, com rigor e linguagem adequada a estudantes. "
    "Seja objetiva por padrão; aprofunde quando pedirem. Use exemplos corretos e "
    "pertinentes, sem inventar nomes, fatos ou analogias estranhas. Revise a resposta "
    "para evitar erros, repetições e finais interrompidos. Se não souber, admita. "
    "Use Markdown simples, sem HTML. Escreva fórmulas inline como $v=f\\lambda$ e "
    "equações em bloco como $$v=\\frac{\\Delta s}{\\Delta t}$$. "
    "Não faça tabelas longas nem listas extensas sem necessidade. "
    "Quando o usuário pedir para registrar ou alterar matérias/notas, use a ferramenta "
    "adequada; só diga que salvou se a ferramenta confirmar. Nunca altere dados sem "
    "um pedido explícito. Ao criar um quiz ou conjunto de flashcards, inclua o link "
    "retornado pela ferramenta para o aluno abrir o material. Registre uma sessão de "
    "estudo quando o aluno pedir para anotar os minutos que estudou."
)


class GroqError(RuntimeError):
    """Erro seguro para exibição quando a API da Groq não responde."""


def groq_configurada():
    return bool(os.environ.get("GROQ_API_KEY", "").strip())


def _enviar(payload):
    api_key = os.environ.get("GROQ_API_KEY", "").strip()
    if not api_key:
        raise GroqError(
            "A chave da API da Groq não está configurada. "
            "Adicione GROQ_API_KEY ao arquivo .env e reinicie o app."
        )

    request = Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "LunaStudyAssistant/1.0",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=60) as response:
            data = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        if error.code == 401:
            raise GroqError(
                "A API da Groq recusou a chave. Confira GROQ_API_KEY no arquivo .env."
            ) from None
        if error.code == 403:
            raise GroqError(
                "A API da Groq negou o acesso (HTTP 403). Confira a conexão e o acesso à API."
            ) from None
        if error.code == 429:
            raise GroqError(
                "O limite de uso da API da Groq foi atingido. Confira os limites da sua conta."
            ) from None
        raise GroqError(
            f"A API da Groq retornou um erro (HTTP {error.code}). Tente novamente mais tarde."
        ) from None
    except (TimeoutError, URLError):
        raise GroqError(
            "Não foi possível conectar à API da Groq. Verifique a internet e tente novamente."
        ) from None
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise GroqError(
            "A API da Groq retornou uma resposta inválida. Tente novamente."
        ) from None
    if not isinstance(data, dict):
        raise GroqError("A API da Groq retornou uma resposta inválida.")
    return data


def _mensagens(mensagem, historico=None, materia_contexto=None,
               contexto_aluno=None, preferencias=None):
    system = SYSTEM_PROMPT
    if materia_contexto:
        system += f" A matéria em foco é {materia_contexto}."
    preferencias = preferencias or {}
    estilo = preferencias.get("estilo_resposta", "equilibrada")
    if estilo == "curta":
        system += " Prefira respostas curtas, com os pontos essenciais."
    elif estilo == "detalhada":
        system += " Explique passo a passo e inclua exemplos quando ajudarem."
    if preferencias.get("usar_exemplos") is False:
        system += " Evite exemplos, a menos que o usuário os peça."
    if contexto_aluno:
        system += f"\nDados atuais do aluno (use apenas quando relevante): {contexto_aluno[:6000]}"

    mensagens = [{"role": "system", "content": system}]
    for item in (historico or [])[-12:]:
        if not isinstance(item, dict):
            continue
        role = "user" if item.get("tipo") == "aluno" else "assistant"
        content = item.get("texto")
        if isinstance(content, str) and content.strip():
            mensagens.append({"role": role, "content": content[:4000]})
    mensagens.append({"role": "user", "content": mensagem[:4000]})
    return mensagens


def _payload(mensagens, max_completion_tokens=2500):
    return {
        "model": os.environ.get("GROQ_MODEL", DEFAULT_MODEL),
        "messages": mensagens,
        "stream": False,
        "max_completion_tokens": max_completion_tokens,
    }


def _mensagem_assistente(data):
    try:
        return data["choices"][0]["message"]
    except (KeyError, IndexError, TypeError):
        raise GroqError(
            "A API da Groq não retornou uma resposta válida. Tente novamente."
        ) from None


def _texto_assistente(message):
    resposta = message.get("content")
    if not isinstance(resposta, str) or not resposta.strip():
        raise GroqError(
            "A API da Groq não retornou uma resposta válida. Tente novamente."
        )
    return resposta.strip()


def responder(mensagem, historico=None, materia_contexto=None,
              contexto_aluno=None, preferencias=None):
    mensagens = _mensagens(
        mensagem, historico, materia_contexto, contexto_aluno, preferencias
    )
    return _texto_assistente(_mensagem_assistente(_enviar(_payload(mensagens))))


def responder_com_ferramentas(mensagem, historico, materia_contexto,
                              contexto_aluno, preferencias, ferramentas, executar):
    mensagens = _mensagens(
        mensagem, historico, materia_contexto, contexto_aluno, preferencias
    )
    payload = _payload(mensagens)
    payload["tools"] = ferramentas
    payload["tool_choice"] = "auto"

    for _ in range(4):
        message = _mensagem_assistente(_enviar(payload))
        chamadas = message.get("tool_calls") or []
        if not chamadas:
            return _texto_assistente(message)
        mensagens.append({
            "role": "assistant",
            "content": message.get("content"),
            "tool_calls": chamadas,
        })
        for chamada in chamadas:
            chamada_id = chamada.get("id")
            funcao = chamada.get("function", {})
            nome = funcao.get("name")
            try:
                argumentos = json.loads(funcao.get("arguments", "{}"))
                if not isinstance(argumentos, dict):
                    raise ValueError
                resultado = executar(nome, argumentos)
            except (TypeError, ValueError):
                resultado = {"ok": False, "erro": "Argumentos da ação inválidos."}
            mensagens.append({
                "role": "tool",
                "tool_call_id": chamada_id,
                "name": nome,
                "content": json.dumps(resultado, ensure_ascii=False),
            })
        payload = _payload(mensagens)
        payload["tools"] = ferramentas
        payload["tool_choice"] = "auto"
    raise GroqError("A Luna não conseguiu concluir a ação. Tente novamente.")


def gerar_json(instrucoes):
    mensagens = [
        {
            "role": "system",
            "content": (
                "Gere conteúdo educacional correto em português brasileiro. "
                "Responda somente com um objeto JSON válido, sem Markdown."
            ),
        },
        {"role": "user", "content": instrucoes[:8000]},
    ]
    payload = _payload(mensagens, max_completion_tokens=4000)
    payload["response_format"] = {"type": "json_object"}
    resposta = _texto_assistente(_mensagem_assistente(_enviar(payload)))
    try:
        dados = json.loads(resposta)
    except json.JSONDecodeError:
        raise GroqError("A Groq gerou um conteúdo inválido. Tente novamente.") from None
    if not isinstance(dados, dict):
        raise GroqError("A Groq gerou um conteúdo inválido. Tente novamente.")
    return dados
