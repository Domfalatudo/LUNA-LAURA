"""Integração da Luna com a API compatível com OpenAI do DeepSeek."""
import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


API_URL = "https://api.deepseek.com/chat/completions"
DEFAULT_MODEL = "deepseek-flash"


class DeepSeekError(RuntimeError):
    """Erro seguro para exibição quando a API do DeepSeek não responde."""


def deepseek_configurada():
    return bool(os.environ.get("DEEPSEEK_API_KEY", "").strip())


def responder(mensagem, historico=None, materia_contexto=None):
    api_key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if not api_key:
        raise DeepSeekError(
            "A chave da API do DeepSeek não está configurada. "
            "Adicione DEEPSEEK_API_KEY ao arquivo .env e reinicie o app."
        )

    materia = f" A matéria em foco é {materia_contexto}." if materia_contexto else ""
    mensagens = [{
        "role": "system",
        "content": (
            "Você é Luna, uma assistente de estudos paciente e didática. "
            "Responda em português brasileiro, com explicações corretas e adequadas "
            "a estudantes. Explique conceitos passo a passo e dê exemplos cotidianos. "
            "Se a pergunta for ambígua, faça uma pergunta curta para esclarecer. "
            "Não invente fatos; admita quando não souber. "
            "Use Markdown simples, sem HTML."
            f"{materia}"
        ),
    }]
    for item in (historico or [])[-12:]:
        if not isinstance(item, dict):
            continue
        role = "user" if item.get("tipo") == "aluno" else "assistant"
        content = item.get("texto")
        if isinstance(content, str) and content.strip():
            mensagens.append({"role": role, "content": content[:4000]})
    mensagens.append({"role": "user", "content": mensagem[:4000]})

    payload = json.dumps({
        "model": os.environ.get("DEEPSEEK_MODEL", DEFAULT_MODEL),
        "messages": mensagens,
        "stream": False,
    }).encode("utf-8")
    request = Request(
        API_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=45) as response:
            data = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        if error.code == 401:
            raise DeepSeekError(
                "A API do DeepSeek recusou a chave. Confira DEEPSEEK_API_KEY no arquivo .env."
            ) from None
        if error.code == 429:
            raise DeepSeekError(
                "A cota da API do DeepSeek foi atingida. Confira os créditos e limites da sua conta."
            ) from None
        if error.code == 402:
            raise DeepSeekError(
                "A API do DeepSeek recusou a solicitação por saldo ou créditos insuficientes. "
                "Confira o saldo e os limites de uso da sua conta DeepSeek."
            ) from None
        raise DeepSeekError(
            f"A API do DeepSeek retornou um erro (HTTP {error.code}). Tente novamente mais tarde."
        ) from None
    except (TimeoutError, URLError):
        raise DeepSeekError(
            "Não foi possível conectar à API do DeepSeek. Verifique a internet e tente novamente."
        ) from None
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise DeepSeekError(
            "A API do DeepSeek retornou uma resposta inválida. Tente novamente."
        ) from None

    try:
        resposta = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        raise DeepSeekError(
            "A API do DeepSeek não retornou uma resposta válida. Tente novamente."
        ) from None
    if not isinstance(resposta, str) or not resposta.strip():
        raise DeepSeekError(
            "A API do DeepSeek retornou uma resposta vazia. Tente novamente."
        )
    return resposta.strip()
