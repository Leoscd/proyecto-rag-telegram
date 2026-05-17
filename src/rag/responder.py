"""Respondedor: llama a MiniMax API."""
import httpx
from ..config import get_settings_lazy


def responder(
    prompt: str,
    contexto_pobre: bool = False,
) -> str:
    """
    Llama MiniMax API y retorna la respuesta.
    Si contexto_pobre=True, usa temperatura más baja.
    """
    settings = get_settings_lazy()

    # Temperature más baja si contexto pobre (más conservador)
    temperature = 0.2 if contexto_pobre else 0.3

    url = "https://api.minimax.chat/v1/text/chatcompletion_v2"
    headers = {
        "Authorization": f"Bearer {settings.minimax_api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": "MiniMax-Text-01",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": 1024,
    }

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, headers=headers, json=body)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        raise RuntimeError(f"Error al llamar MiniMax: {e}")