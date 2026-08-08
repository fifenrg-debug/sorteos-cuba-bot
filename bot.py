import telebot
import time
import random
import sqlite3
from database import (
    init_db, 
    guardar_monto, 
    actualizar_numero, 
    actualizar_comprobante, 
    cambiar_estado_jugada,
    obtener_reporte_sorteo,
    obtener_participantes_sorteo,
    obtener_numeros_ocupados,
    guardar_datos_retiro
)
from handlers import (
    menu_principal, 
    texto_datos_pago, 
    botones_admin,
    menu_cerrar_sorteo,
    boton_girar_ruleta,
    boton_retirar_premio,
    menu_encuesta
)

TOKEN = "8517181201:AAFOKXvdF4kf5duav5jFxPzSYAmutl8kTG4"
ADMIN_ID = 8478276387

bot = telebot.TeleBot(TOKEN)
init_db()

# Diccionario temporal para saber si un usuario está escribiendo sus datos de retiro
usuarios_retirando = set()

@bot.message_handler(commands=['start'])
def enviar_bienvenida(message):
    texto = (
        "¡Bienvenido a Sorteos en Cuba! 🍀\n"
        "Tu oportunidad de ganar premios en CUP.\n\n"
        "💰 Selecciona el monto del sorteo en el que deseas participar:"
    )
    bot.send_message(message.chat.id, texto, reply_markup=menu_principal())

@bot.callback_query_handler(func=lambda call: call.data.startswith("sorteo_"))
def callback_sorteo(call):
    monto = call.data.split("_")[1]
    guardar_monto(call.message.chat.id, monto)
    
    bot.answer_callback_query(call.id, text=f"Has seleccionado el sorteo de {monto} CUP")
    
    # Mostrar qué números ya están ocupados para ayudar al usuario
    ocupados = obtener_numeros_ocupados(monto)
    texto_ocupados = f"\n\n🚫 *Números ya ocupados:* `{', '.join(ocupados) if ocupados else 'Ninguno todavía'}`" if len(ocupados) > 0 else "\n\n🟢 *¡Todos los números del 00 al 99 están disponibles!*"
    
    texto_numero = (
        f"🎟️ **Has elegido el Sorteo de {monto} CUP**\n\n"
        "🔢 Por favor, **escribe el número de 2 dígitos (00 al 99)** con el que deseas jugar:"
        f"{texto_ocupados}"
    )
    bot.send_message(call.message.chat.id, texto_numero, parse_mode="Markdown")

# === PANEL DE ADMINISTRACIÓN / CIERRE COLOCADO ANTES DEL TEXTO GENERAL ===
@bot.message_handler(commands=['cierre', 'admin'])
def panel_cierre(message):
    if message.chat.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ No tienes permisos para acceder a esta sección.")
        return
    
    bot.send_message(
        message.chat.id, 
        "🛠️ **Panel de Administración - Cierre de Sorteos**\n\n"
        "Selecciona de qué monto deseas cerrar el sorteo y ver el listado final de participantes:",
        reply_markup=menu_cerrar_sorteo(),
        parse_mode="Markdown"
    )

@bot.message_handler(func=lambda message: True, content_types=['text'])
def recibir_texto_general(message):
    user_id = message.chat.id
    texto_usuario = message.text.strip()
    
    # Si el usuario está en proceso de enviar sus datos de retiro de premio
    if user_id in usuarios_retirando:
        guardar_datos_retiro(user_id, texto_usuario)
        usuarios_retirando.remove(user_id)
        
        bot.send_message(
            user_id, 
            "✅ **¡Datos de retiro recibidos con éxito!**\n"
            "El administrador procesará tu transferencia en breve.\n\n"
            "🌟 *Para ayudarnos a mejorar, por favor valora la fiabilidad de nuestra aplicación:*",
            reply_markup=menu_encuesta(),
            parse_mode="Markdown"
        )
        
        # Notificar al administrador sobre el retiro solicitado
        aviso_admin = (
            f"🚨 **¡SOLICITUD DE RETIRO DE PREMIO!** 🚨\n\n"
            f"👤 **Usuario ID:** `{user_id}`\n"
            f"💳 **Datos de cobro proporcionados:**\n`{texto_usuario}`"
        )
        bot.send_message(ADMIN_ID, aviso_admin, parse_mode="Markdown")
        return

    # Validar si es un número válido para el sorteo (00 al 99)
    if texto_usuario.isdigit() and 0 <= int(texto_usuario) <= 99:
        if len(texto_usuario) == 1:
            texto_usuario = "0" + texto_usuario
            
        conn = sqlite3.connect('sorteos.db')
        cursor = conn.cursor()
        # Buscamos primero en estado 'seleccionando', de lo contrario rescatamos la última jugada activa del usuario
        cursor.execute('SELECT monto FROM jugadas WHERE user_id = ? AND estado = "seleccionando" ORDER BY id DESC LIMIT 1', (user_id,))
        res = cursor.fetchone()
        
        if not res:
            cursor.execute('SELECT monto FROM jugadas WHERE user_id = ? ORDER BY id DESC LIMIT 1', (user_id,))
            res = cursor.fetchone()
            
        conn.close()
        
        if not res:
            bot.send_message(user_id, "⚠️ Por favor, selecciona primero un sorteo usando /start")
            return
            
        monto_actual = res[0]
        
        # Validar si el número ya está ocupado
        if not verificar_numero_disponible_local(monto_actual, texto_usuario):
            bot.send_message(
                user_id, 
                f"❌ El número **{texto_usuario}** ya se encuentra ocupado o reservado en este sorteo.\n"
                "Por favor, elige otro número diferente que esté libre.",
                parse_mode="Markdown"
            )
            return
            
        actualizar_numero(user_id, texto_usuario)
        bot.send_message(user_id, texto_datos_pago(monto_actual, texto_usuario), parse_mode="Markdown")

def verificar_numero_disponible_local(monto, numero):
    ocupados = obtener_numeros_ocupados(monto)
    return numero not in ocupados

@bot.message_handler(content_types=['photo'])
def recibir_comprobante(message):
    user_id = message.chat.id
    file_id = message.photo[-1].file_id
    
    actualizar_comprobante(user_id, file_id)
    bot.reply_to(message, "⏳ Comprobante recibido con éxito. Está pendiente de revisión por el administrador.")
    
    info_admin = (
        f"🔔 **¡Nuevo Comprobante Recibido!**\n\n"
        f"👤 **Usuario ID:** `{user_id}`\n"
        f"Verifica la transferencia confirmando al 52728871."
    )
    bot.send_photo(ADMIN_ID, file_id, caption=info_admin, parse_mode="Markdown", reply_markup=botones_admin(user_id))

@bot.callback_query_handler(func=lambda call: call.data.startswith("aprobar_") or call.data.startswith("rechazar_"))
def callback_admin_accion(call):
    accion, user_id_str = call.data.split("_")
    user_id = int(user_id_str)
    
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "No tienes permisos para hacer esto.", show_alert=True)
        return
    
    if accion == "aprobar":
        cambiar_estado_jugada(user_id, "aprobado")
        bot.answer_callback_query(call.id, "¡Pago aprobado!")
        
        texto_aprobacion = (
            "🎉🎊 **¡Felicidades! ¡Pago Aceptado!** 🎊🎉\n\n"
            "✨ *Tu transacción ha sido verificada y tu dinero ya está asentado para el sorteo.*\n\n"
            "🍀 **¡Ya estás oficialmente participando y dentro de la lista de ganadores!** Mucha suerte con tu número. 🎟️"
        )
        bot.send_message(user_id, texto_aprobacion, parse_mode="Markdown")
        bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id, caption=call.message.caption + "\n\n✅ **ESTADO: APROBADO Y REGISTRADO**", parse_mode="Markdown")
    
    elif accion == "rechazar":
        cambiar_estado_jugada(user_id, "rechazado")
        bot.answer_callback_query(call.id, "Pago rechazado.")
        bot.send_message(user_id, "❌ Lo sentimos, tu comprobante de pago no pudo ser verificado. Por favor, contacta al soporte o intenta nuevamente.")
        bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id, caption=call.message.caption + "\n\n❌ **ESTADO: RECHAZADO**", parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("cerrar_"))
def callback_cerrar_sorteo(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "No autorizado.", show_alert=True)
        return
        
    monto = call.data.split("_")[1]
    participantes, total_bruto, total_neto = obtener_reporte_sorteo(monto)
    
    lista_texto = ""
    if participantes:
        for idx, (uid, num) in enumerate(participantes, 1):
            lista_texto += f"{idx}. ID: `{uid}` — Número: **{num}**\n"
    else:
        lista_texto = "⚠️ *Aún no hay ningún usuario aprobado para este sorteo.*"
        
    reporte = (
        f"📊 **REPORTE DE CIERRE - SORTEO {monto} CUP** 📊\n\n"
        f"💰 **Dinero Bruto Recaudado:** `{total_bruto} CUP`\n"
        f"📉 **Descuento (20%):** `{total_bruto * 0.20:.2f} CUP`\n"
        f"💵 **Total Neto (Menos el 20%):** `*{total_neto:.2f} CUP*`\n"
        f"🎟️ **Total de Jugadas Aprobadas:** `{len(participantes)}`\n\n"
        f"📋 **Listado de Participantes:**\n"
        f"{lista_texto}"
    )
    
    bot.answer_callback_query(call.id, f"Sorteo de {monto} CUP procesado")
    bot.send_message(call.message.chat.id, reporte, parse_mode="Markdown", reply_markup=boton_girar_ruleta(monto))

@bot.callback_query_handler(func=lambda call: call.data.startswith("ruleta_"))
def callback_girar_ruleta(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "No autorizado.", show_alert=True)
        return
        
    monto = call.data.split("_")[1]
    participantes = obtener_participantes_sorteo(monto)
    
    if not participantes:
        bot.answer_callback_query(call.id, "No hay participantes aprobados.", show_alert=True)
        bot.send_message(call.message.chat.id, f"❌ No se puede girar la ruleta del sorteo de {monto} CUP porque aún no hay participantes aprobados.")
        return

    msg = bot.send_message(
        call.message.chat.id, 
        f"🎰 **RULETA ACTIVA - SORTEO {monto} CUP** 🎰\n\n"
        f"🎟️ Total de fragmentos en juego: `{len(participantes)}`\n\n"
        "🔴 *Preparando la tómbola y mezclando números... [ 🔄 ]*",
        parse_mode="Markdown"
    )
    
    fases_animacion = [
        f"🟡 *La ruleta empieza a girar velozmente... [ 🔄 ]*\nParticipantes en la tómbola: {len(participantes)}",
        f"🟢 *Los números comienzan a pasar rápido... [ ⚡ ]*\n¡La tensión sube en el Sorteo de {monto} CUP!",
        f"🔵 *La velocidad disminuye poco a poco... [ 🌀 ]*\n¿Quién será el afortunado?",
        f"🟣 *El indicador se está deteniendo en un número... [ 🎯 ]*"
    ]
    
    for texto_fase in fases_animacion:
        time.sleep(1.2)
        try:
            bot.edit_message_text(texto_fase, chat_id=call.message.chat.id, message_id=msg.message_id, parse_mode="Markdown")
        except:
            pass

    ganador_elegido = random.choice(participantes)
    user_id_ganador, numero_ganador = ganador_elegido
    
    lista_fragmentada = ""
    for idx, (uid, num) in enumerate(participantes, 1):
        if num == numero_ganador and uid == user_id_ganador:
            lista_fragmentada += f"✨ {idx}. ID: `{uid}` — Número: **{num}** ⬅️ **¡GANADOR!**\n"
        else:
            lista_fragmentada += f"🔸 {idx}. ID: `{uid}` — Número: `{num}`\n"

    resultado_final = (
        f"🎉🎊 **¡RULETA FINALIZADA - SORTEO {monto} CUP!** 🎊🎉\n\n"
        f"🏆 **¡EL NÚMERO GANADOR ES EL {numero_ganador}!** 🏆\n"
        f"👤 **ID del Afortunado:** `{user_id_ganador}`\n\n"
        f"📋 **Desglose de los {len(participantes)} fragmentos participantes:**\n"
        f"{lista_fragmentada}"
    )
    
    time.sleep(1)
    try:
        bot.edit_message_text(resultado_final, chat_id=call.message.chat.id, message_id=msg.message_id, parse_mode="Markdown")
    except Exception as e:
        bot.send_message(call.message.chat.id, resultado_final, parse_mode="Markdown")

    # Notificar al ganador con el botón para retirar su premio
    try:
        mensaje_ganador_privado = (
            f"🎉🎊 **¡FELICIDADES! ¡HAS GANADO EL SORTEO DE {monto} CUP!** 🎊🎉\n\n"
            f"✨ *La ruleta digital ha girado entre todos los participantes y tu número **{numero_ganador}** resultó el gran triunfador.*\n\n"
            f"🏆 Haz clic en el botón de abajo para reclamar tu premio. 💸"
        )
        bot.send_message(user_id_ganador, mensaje_ganador_privado, parse_mode="Markdown", reply_markup=boton_retirar_premio(monto))
    except Exception as e:
        print(f"No se pudo enviar el mensaje privado al ganador: {e}")
        
    bot.answer_callback_query(call.id, "¡Sorteo concluido con éxito!")

# Manejar el clic en "Retirar mi Premio"
@bot.callback_query_handler(func=lambda call: call.data.startswith("retirar_"))
def callback_retirar_premio(call):
    monto = call.data.split("_")[1]
    user_id = call.message.chat.id
    
    usuarios_retirando.add(user_id)
    bot.answer_callback_query(call.id, "¡Iniciando proceso de retiro!")
    bot.send_message(
        user_id,
        "💳 **Retirada de Premio**\n\n"
        f"Por favor, escribe a continuación tu **número de tarjeta o número de teléfono móvil** donde deseas que te realicemos la transferencia del premio neto del sorteo de {monto} CUP:",
        parse_mode="Markdown"
    )

# Manejar la respuesta de la encuesta de satisfacción
@bot.callback_query_handler(func=lambda call: call.data.startswith("eval_"))
def callback_evaluacion(call):
    estrellas = call.data.split("_")[1]
    bot.answer_callback_query(call.id, f"¡Gracias por tu valoración de {estrellas} estrellas!")
    bot.edit_message_text(
        f"🌟 **¡Muchas gracias por tu valoración de {estrellas} estrellas!** ⭐\n\n"
        "Valoramos enormemente tu confianza en **Sorteos en Cuba**. ¡Te esperamos en los próximos sorteos! 🍀",
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        parse_mode="Markdown"
    )

if __name__ == '__main__':
    print("El bot está encendido con arquitectura modular y panel de admin...")
    while True:
        try:
            bot.infinity_polling(timeout=20, long_polling_timeout=10)
        except Exception as e:
            print(f"Reconectando por fallo de red: {e}")
