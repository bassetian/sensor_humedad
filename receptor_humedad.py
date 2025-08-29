import network
import espnow
import select
import time
from machine import Pin, I2C
import sh1106

# Configuración del I2C y OLED SH1106
i2c = I2C(0, scl=Pin(22), sda=Pin(23))
oled = sh1106.SH1106_I2C(128, 64, i2c)

oled.fill(0)
oled.text("Receptor listo", 0, 0)
oled.text("Esperando msg...", 0, 16)
oled.show()

# Configuración de ESP-NOW
sta = network.WLAN(network.WLAN.IF_STA)  # Or network.WLAN.IF_AP
sta.active(True)
e = espnow.ESPNow()
e.active(True)  

print("Receptor listo. Esperando mensajes por ESP-NOW...\n")

poll = select.poll()
poll.register(e, select.POLLIN)

ultimo_msg = None  # timestamp del último mensaje

while True:
    events = poll.poll(1000) 
    if events:
        try:
            mac, msg = e.irecv(0) 
            if mac:
                # Guardar tiempo del último mensaje
                ultimo_msg = time.time()
                print("Mensaje recibido. Guardando timestamp...")
                linea=msg
                #Convertir a string
                linea_str = linea.decode()
                #Separar por comas
                valores = linea_str.split(',')
                # Tomar el tercer valor (índice 2)
                valor = valores[2]

        except Exception as err:
            print("Error en irecv():", err)

    # Mostrar en OLED cada ciclo
    oled.fill(0)
    if ultimo_msg is None:
        oled.text("Sin mensajes", 0, 0)
    else:
        diff = int(time.time() - ultimo_msg)
        minutos = diff // 60
        segundos = diff % 60
        oled.text("Ult. msg hace:", 0, 0)
        oled.text("{} min {} s".format(minutos, segundos), 0, 10)
        oled.text("Ultimo valor:",0,30)
        oled.text(valor,0,40)
    oled.show()
