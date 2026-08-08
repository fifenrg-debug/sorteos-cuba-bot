from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def menu_principal():
    markup = InlineKeyboardMarkup(row_width=2)
    montos = [10, 20, 50, 100, 500, 1000]
    for m in montos:
        markup.add(InlineKeyboardButton(f"🎟️ Sorteo {m} CUP", callback_data=f"sorteo_{m}"))
    return markup

def texto_datos_pago(monto, numero):
    return (
        f"✅ ¡Número **{numero}** guardado para el sorteo de **{monto} CUP**!\n\n"
        "💳 **Datos de transferencia:**\n"
        "Toca sobre el número para copiarlo:\n\n"
        "Tarjeta: `9224069997944679`\n"
        "Teléfono: `52728871`\n\n"
        "📱 **Instrucciones:**\n"
        "1. Realiza la transferencia.\n"
        "2. **Envía por aquí la foto del comprobante** para verificar tu pago."
    )

def botones_admin(user_id):
    markup = InlineKeyboardMarkup(row_width=2)
    btn_aprobar = InlineKeyboardButton("✅ Aprobar", callback_data=f"aprobar_{user_id}")
    btn_rechazar = InlineKeyboardButton("❌ Rechazar", callback_data=f"rechazar_{user_id}")
    markup.add(btn_aprobar, btn_rechazar)
    return markup

def menu_cerrar_sorteo():
    markup = InlineKeyboardMarkup(row_width=2)
    montos = [10, 20, 50, 100, 500, 1000]
    for m in montos:
        markup.add(InlineKeyboardButton(f"🔒 Cerrar Sorteo {m} CUP", callback_data=f"cerrar_{m}"))
    return markup

def boton_girar_ruleta(monto):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(f"🎲 ¡Girar Ruleta Sorteo {monto} CUP!", callback_data=f"ruleta_{monto}"))
    return markup

def boton_retirar_premio(monto):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("💸 ¡Retirar mi Premio!", callback_data=f"retirar_{monto}"))
    return markup

def menu_encuesta():
    markup = InlineKeyboardMarkup(row_width=5)
    markup.add(
        InlineKeyboardButton("⭐ 1", callback_data="eval_1"),
        InlineKeyboardButton("⭐ 2", callback_data="eval_2"),
        InlineKeyboardButton("⭐ 3", callback_data="eval_3"),
        InlineKeyboardButton("⭐ 4", callback_data="eval_4"),
        InlineKeyboardButton("⭐ 5", callback_data="eval_5")
    )
    return markup
