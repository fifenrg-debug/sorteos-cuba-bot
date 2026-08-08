import sqlite3
import random

def init_db():
    conn = sqlite3.connect('sorteos.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS jugadas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            monto TEXT,
            numero TEXT,
            estado TEXT DEFAULT 'pendiente',
            foto_id TEXT,
            datos_retiro TEXT
        )
    ''')
    conn.commit()
    conn.close()

def guardar_monto(user_id, monto):
    conn = sqlite3.connect('sorteos.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO jugadas (user_id, monto, estado) VALUES (?, ?, "seleccionando")', (user_id, monto))
    conn.commit()
    conn.close()

def obtener_numeros_ocupados(monto_sorteo):
    conn = sqlite3.connect('sorteos.db')
    cursor = conn.cursor()
    # Consideramos ocupados los aprobados, pendientes o esperando comprobante
    cursor.execute('''
        SELECT numero FROM jugadas 
        WHERE monto = ? AND estado IN ('aprobado', 'pendiente', 'esperando_comprobante') AND numero IS NOT NULL
    ''', (str(monto_sorteo),))
    ocupados = [row[0] for row in cursor.fetchall()]
    conn.close()
    return ocupados

def actualizar_numero(user_id, numero):
    conn = sqlite3.connect('sorteos.db')
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE jugadas 
        SET numero = ?, estado = 'esperando_comprobante' 
        WHERE user_id = ? AND estado = 'seleccionando'
    ''', (numero, user_id))
    conn.commit()
    conn.close()

def actualizar_comprobante(user_id, foto_id):
    conn = sqlite3.connect('sorteos.db')
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE jugadas 
        SET foto_id = ?, estado = 'pendiente' 
        WHERE user_id = ? AND estado = 'esperando_comprobante'
    ''', (foto_id, user_id))
    conn.commit()
    conn.close()

def cambiar_estado_jugada(user_id, nuevo_estado):
    conn = sqlite3.connect('sorteos.db')
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE jugadas 
        SET estado = ? 
        WHERE user_id = ? AND estado = 'pendiente'
    ''', (nuevo_estado, user_id))
    conn.commit()
    conn.close()

def guardar_datos_retiro(user_id, datos):
    conn = sqlite3.connect('sorteos.db')
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE jugadas 
        SET datos_retiro = ? 
        WHERE user_id = ? AND estado = 'aprobado'
    ''', (datos, user_id))
    conn.commit()
    conn.close()

def obtener_reporte_sorteo(monto_sorteo):
    conn = sqlite3.connect('sorteos.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT user_id, numero FROM jugadas 
        WHERE monto = ? AND estado = 'aprobado'
    ''', (str(monto_sorteo),))
    participantes = cursor.fetchall()
    
    total_bruto = len(participantes) * int(monto_sorteo)
    comision_20 = total_bruto * 0.20
    total_neto = total_bruto - comision_20
    
    conn.close()
    return participantes, total_bruto, total_neto

def obtener_participantes_sorteo(monto_sorteo):
    conn = sqlite3.connect('sorteos.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT user_id, numero FROM jugadas 
        WHERE monto = ? AND estado = 'aprobado'
    ''', (str(monto_sorteo),))
    participantes = cursor.fetchall()
    conn.close()
    return participantes

def limpiar_sorteo(monto_sorteo):
    conn = sqlite3.connect('sorteos.db')
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE jugadas 
        SET estado = 'finalizado' 
        WHERE monto = ? AND estado = 'aprobado'
    ''', (str(monto_sorteo),))
    conn.commit()
    conn.close()
