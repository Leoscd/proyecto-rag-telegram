"""Respondedor: llama a OpenAI API."""
import httpx
from ..config import get_settings_lazy


def responder(
    prompt: str,
    contexto_pobre: bool = False,
) -> str:
    """
    Llama OpenAI API y retorna la respuesta.
    Si contexto_pobre=True, usa temperatura más baja.
    """
    settings = get_settings_lazy()

    # Temperature más baja si contexto pobre (más conservador)
    temperature = 0.2 if contexto_pobre else 0.3

    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": 1024,
    }

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, headers=headers, json=body)
            data = response.json()
            if "choices" not in data:
                raise RuntimeError(f"Respuesta inesperada de OpenAI: {data}")
            return data["choices"][0]["message"]["content"]
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"Error al llamar OpenAI: {e}")