"""Bot de Telegram para RAG-Obras."""
import os
import httpx
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

from ..config import get_settings_lazy


API_URL = os.environ.get("API_URL", "http://localhost:8000")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ Handler /start."""
    await update.message.reply_text(
        "🏗️ *RAG-Obras Bot*\n\n"
        "Consulta el manual de obra desde campo.\n"
        "Enviame tu pregunta en lenguaje natural.\n\n"
        "Ej: Como se hace el revoque exterior?",
        parse_mode="Markdown"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ Handler /help."""
    await update.message.reply_text(
        "📖 *Ayuda*\n\n"
        "Enviame cualquier pregunta sobre el proyecto.\n"
        "Te respondo con información de los documentos.\n\n"
        "/start - Iniciar\n"
        "/logs - Ver últimas consultas",
        parse_mode="Markdown"
    )


async def logs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler /logs - mostrar últimas consultas."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{API_URL}/logs", params={"limit": 5})
            if response.status_code == 200:
                data = response.json()
                if not data:
                    await update.message.reply_text("No hay consultas registradas.")
                    return
                
                msg = "📋 *Últimas consultas:*\n\n"
                for item in data:
                    msg += f"• {item['mensaje_original'][:50]}...\n"
                    msg += f"  Score: {item['score_maximo']:.2f}\n\n"
                
                await update.message.reply_text(msg, parse_mode="Markdown")
            else:
                await update.message.reply_text("Error al obtener logs.")
    except Exception as e:
        await update.message.reply_text(f"Error: {e}")


async def handle_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ Handler mensajes - consulta a la API."""
    mensaje = update.message.text
    user = update.message.from_user.username or update.message.from_user.first_name or "unknown"

    # Confirmar que recibió el mensaje
    await update.message.reply_text("🔎 Buscando en los documentos...")

    try:
        # Llamar a la API
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{API_URL}/query",
                json={
                    "proyecto_id": 1,  # Por ahora hardcodeado
                    "mensaje": mensaje,
                    "usuario_telegram": user,
                }
            )

            if response.status_code != 200:
                await update.message.reply_text("❌ Error al procesar consulta. Intenta más tarde.")
                return

            data = response.json()

            # Responder con el texto
            respuesta = data.get("respuesta", "No encontré información.")
            await update.message.reply_text(respuesta)

            # Si tiene imagen, enviar como foto
            if data.get("tiene_imagen") and data.get("ruta_imagen"):
                try:
                    # Obtener URL pública de la imagen
                    img_response = await client.get(
                        f"{API_URL}/storage/documentos/{data['ruta_imagen']}"
                    )
                    if img_response.status_code == 200:
                        await update.message.reply_photo(img_response.content)
                except:
                    pass  # Si falla, no es crítico

    except httpx.TimeoutException:
        await update.message.reply_text("⏱️ Tiempo de espera agotado. Intenta más tarde.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)[:100]}")


def main():
    """ Iniciar el bot."""
    settings = get_settings_lazy()
    
    app = Application.builder().token(settings.telegram_bot_token).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("logs", logs_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_query))

    # Polling
    print("🤖 Bot arrancado...")
    app.run_polling()