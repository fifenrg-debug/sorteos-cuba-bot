import time
import subprocess

print("🔄 Iniciando supervisor automático del bot...")

while True:
    try:
        # Ejecuta el bot y espera a que termine o falle
        proceso = subprocess.Popen(["python", "bot.py"])
        proceso.wait()
    except Exception as e:
        print(f"⚠️ El bot se detuvo con error: {e}")
    
    print("⏳ Reiniciando el bot en 5 segundos...")
    time.sleep(5)
