"""Respostas do assistente durante onboarding (projeto sem contexto mínimo)."""

from __future__ import annotations

import os
from typing import Any

_STATIC_OPENING = """## Onboarding do projeto

Percebi que este projeto ainda **não tem contexto mínimo** registado em `.squad/context.md` (ou o ficheiro é demasiado curto / falta `backlog.json`).

Quer:

1. **Enviar ficheiros ou textos** para eu analisar (cole aqui o conteúdo relevante); ou  
2. **Construir o contexto comigo** por perguntas guiadas?

Responda com **1** ou **2**. Quando tiver informação suficiente, peça para **gerar o contexto** (ou use o botão na interface, se existir) para gravar `.squad/context.md` no disco do projeto.

_Enquanto o contexto não estiver completo, o meta-orquestrador técnico (`run_squad.py`) não corre — mas pode continuar a conversar aqui._
"""


def _format_transcript(messages: list[dict[str, Any]], max_chars: int = 24_000) -> str:
    parts: list[str] = []
    n = 0
    for m in messages:
        role = str(m.get("role") or "")
        content = str(m.get("content") or "").strip()
        if not content:
            continue
        parts.append(f"{role}: {content}")
        n += len(content)
        if n > max_chars:
            parts.append("\n_[histórico truncado]_")
            break
    return "\n\n".join(parts)


def generate_bootstrap_assistant_reply(
    *,
    project_name: str,
    project_slug: str,
    local_path: str,
    messages: list[dict[str, Any]],
    latest_user_message: str,
    chat_id: int | None = None,
) -> str:
    """
    Produz resposta do assistente para o modo onboarding.

    Com `OPENAI_API_KEY`, usa um modelo leve; caso contrário, devolve texto estático seguro.
    """
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    transcript = _format_transcript(messages)

    attachment_note = ""
    if chat_id is not None:
        from core.chats import chat_attachment_service

        names = chat_attachment_service.list_attachment_file_names(chat_id)
        if names:
            attachment_note = (
                "\n\nAnexos visuais já guardados neste chat (em `.squad/attachments/` no disco do "
                "projeto; nesta fase **não** são analisados automaticamente pelo modelo): "
                + ", ".join(names)
            )

    if not api_key:
        return _STATIC_OPENING + attachment_note

    try:
        from openai import OpenAI
    except ImportError:
        return _STATIC_OPENING + attachment_note

    model = os.getenv("SQUAD_BOOTSTRAP_MODEL", "gpt-4o-mini").strip() or "gpt-4o-mini"
    client = OpenAI(api_key=api_key)
    system = (
        "És o assistente de onboarding do produto squad-agentes. Respondes em **português europeu** "
        "(pt-PT), tom profissional e conciso. O utilizador está a configurar o contexto do projeto "
        f"no disco local (`{local_path}`). Slug: `{project_slug}`. Nome: {project_name}.\n\n"
        "Objetivos:\n"
        "- Se ainda não escolheu modo, oferece claramente as opções 1 (colar textos/ficheiros como texto) "
        "e 2 (perguntas guiadas).\n"
        "- Se escolheu 2, faz **uma** pergunta de cada vez (objetivo, problema, público, escopo, restrições).\n"
        "- Se escolheu 1, pede para colar o material e resume o que entendeste.\n"
        "- Nunca afirmas que executaste o meta-orquestrador nem a squad completa.\n"
        "- No fim de cada turno, lembra que pode pedir para **gerar o contexto** quando quiser gravar no disco.\n"
    )
    user = (
        f"Última mensagem do utilizador:\n{latest_user_message.strip()}\n\n"
        f"Histórico recente (papel a papel):\n{transcript}"
        f"{attachment_note}"
    )
    try:
        resp = client.chat.completions.create(
            model=model,
            temperature=0.4,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        choice = resp.choices[0].message.content
        text = (choice or "").strip()
        return text if text else _STATIC_OPENING + attachment_note
    except Exception:
        return _STATIC_OPENING + attachment_note
