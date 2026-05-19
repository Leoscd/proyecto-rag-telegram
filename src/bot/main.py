"""Bot de Telegram para RAG-Obras."""
import os
import httpx
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from ..config import get_settings_lazy


API_URL = os.environ.get("API_URL", "http://localhost:8000")

# Proyectos activos por usuario: {user_id: proyecto_id}
proyectos_activos: dict[int, int] = {}

# Historial conversacional por usuario: {user_id: [{"pregunta": str, "respuesta": str}, ...]}
historial: dict[int, list[dict]] = {}
MAX_RONDAS = 5


def get_proyecto(user_id: int) -> int:
    """Obtiene el proyecto activo de un usuario."""
    return proyectos_activos.get(user_id, 1)


def set_proyecto(user_id: int, proyecto_id: int):
    """Cambia el proyecto activo de un usuario."""
    proyectos_activos[user_id] = proyecto_id


def get_historial(user_id: int) -> list[dict]:
    """Obtiene el historial de un usuario."""
    return historial.get(user_id, [])


def push_ronda(user_id: int, pregunta: str, respuesta: str) -> None:
    """Agrega una ronda al historial y recorta a MAX_RONDAS."""
    if user_id not in historial:
        historial[user_id] = []
    historial[user_id].append({"pregunta": pregunta, "respuesta": respuesta})
    # Recortar a MAX_RONDAS (FIFO)
    if len(historial[user_id]) > MAX_RONDAS:
        historial[user_id] = historial[user_id][-MAX_RONDAS:]


def reset_historial(user_id: int) -> None:
    """Limpia el historial de un usuario."""
    if user_id in historial:
        historial[user_id] = []


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler /start."""
    await update.message.reply_text(
        "🏗️ *RAG-Obras Bot*\n\n"
        "Consulta el manual de obra desde campo.\n"
        "Enviame tu pregunta en lenguaje natural.\n\n"
        "Comandos:\n"
        "/start - Iniciar\n"
        "/proyecto <id> - Cambiar proyecto\n"
        "/proyecto - Ver proyecto actual\n"
        "/ayuda - Ayuda\n\n"
        "Ej: Como se hace el revoque exterior?",
        parse_mode="Markdown"
    )


async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler /ayuda."""
    await update.message.reply_text(
        "📖 *Ayuda*\n\n"
        "Enviame tu pregunta sobre el proyecto.\n"
        "Te respondo con información de los documentos.\n\n"
        "*Comandos:*\n"
        "/start - Bienvenida\n"
        "/proyecto <id> - Cambiar proyecto\n"
        "/proyecto - Ver proyecto actual",
        parse_mode="Markdown"
    )


async def proyecto_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler /proyecto - ver o cambiar proyecto."""
    user_id = update.message.from_user.id
    args = context.args

    if args:
        # Cambiar proyecto
        try:
            proyecto_id = int(args[0])
            set_proyecto(user_id, proyecto_id)
            reset_historial(user_id)  # Limpiar historial al cambiar de proyecto
            await update.message.reply_text(f"✅ Proyecto cambiado a {proyecto_id}")
        except ValueError:
            await update.message.reply_text("❌ ID de proyecto inválido. Uso: /proyecto <id>")
    else:
        # Mostrar proyecto actual
        actual = get_proyecto(user_id)
        await update.message.reply_text(f"📁 Proyecto activo: {actual}")


async def handle_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler mensajes - consulta a la API."""
    mensaje = update.message.text
    user = update.message.from_user
    user_id = user.id
    username = user.username or user.first_name or "unknown"

    proyecto_id = get_proyecto(user_id)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # 1. Consultar API
            response = await client.post(
                f"{API_URL}/query",
                json={
                    "proyecto_id": proyecto_id,
                    "mensaje": mensaje,
                    "usuario_telegram": username,
                    "historial": get_historial(user_id),
                }
            )

            if response.status_code != 200:
                await update.message.reply_text("❌ Error al procesar. Intenta más tarde.")
                return

            data = response.json()
            respuesta = data.get("respuesta", "No encontré información.")
            score = data.get("score_maximo", 0.0)

            # --- NUEVO: formato conversacional ---
            if score < 0.4:
                respuesta = "⚠️ No encontré documentación sobre esto en los documentos cargados. Intentá reformular la pregunta."
                await update.message.reply_text(respuesta)
                return

            # 2. Si tiene imagen, obtener URL firmada y descargar
            img_bytes = None
            tiene_imagen = data.get("tiene_imagen") and data.get("ruta_imagen")
            if tiene_imagen:
                try:
                    url_resp = await client.get(
                        f"{API_URL}/storage/url",
                        params={"path": data["ruta_imagen"]}
                    )
                    if url_resp.status_code == 200:
                        signed_url = url_resp.json().get("url")
                        if signed_url:
                            img_download = await client.get(signed_url)
                            if img_download.status_code == 200:
                                img_bytes = img_download.content
                except Exception as e:
                    print(f"Error descargando imagen: {e}")

            # 3. Enviar respuesta (un solo mensaje: foto+caption o solo texto)
            if img_bytes:
                # Telegram limita caption a ~1024 caracteres
                if len(respuesta) > 1024:
                    await update.message.reply_text(respuesta)
                    await update.message.reply_photo(photo=img_bytes)
                else:
                    await update.message.reply_photo(photo=img_bytes, caption=respuesta)
            else:
                await update.message.reply_text(respuesta)

            # Guardar ronda en historial (solo si hubo contexto util)
            push_ronda(user_id, mensaje, respuesta)

    except httpx.TimeoutException:
        await update.message.reply_text("⏱️ Tiempo de espera agotado. Intenta más tarde.")
    except Exception as e:
        print(f"ERROR en handle_query: {e}")
        await update.message.reply_text("❌ Error al procesar consulta. Intenta más tarde.")


def main():
    """Iniciar el bot."""
    settings = get_settings_lazy()

    if not settings.telegram_bot_token:
        print("ERROR: TELEGRAM_BOT_TOKEN no configurado")
        return

    app = Application.builder().token(settings.telegram_bot_token).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ayuda", ayuda))
    app.add_handler(CommandHandler("proyecto", proyecto_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_query))

    print("🤖 Bot arrancado...")
    app.run_polling()


if __name__ == "__main__":
    main()