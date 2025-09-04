from machine import ADC, Pin
import time
from time import sleep
import machine
import os
import network
import espnow
import ntptime

sleep(3)

# Encender LED
led = Pin(13, Pin.OUT)
led.value(1)

# Detectar causa de reinicio
re = machine.reset_cause()
print("Causa de reinicio:", re)

rtc = machine.RTC()
wlan = network.WLAN(network.STA_IF)

if re == 5:   # (no deep sleep)
    print("Inicio... Conectando WiFi para configurar hora")

    # Conexión WiFi para NTP
    red = "Atmosfera"
    contraseña = "53gur1d4d4tm"
    wlan.active(True)
    wlan.connect(red, contraseña)
    c = 10
    while not wlan.isconnected() and c>=0:
        time.sleep(1)
        c+=1
    print("Conexión Wi-Fi:", wlan.ifconfig())

    # Obtener hora desde NTP
    try:
        print("Obteniendo hora de internet...")
        ntptime.host = "pool.ntp.org"
        ntptime.settime()   # Ajusta RTC en UTC
        print("Hora UTC sincronizada:", rtc.datetime())

        # Ajustar a hora local (UTC-6, CDMX)
        #año, mes, dia, dia_semana, hora, minuto, segundo, subseg = rtc.datetime()
        #hora_local = (hora - 6) % 24
        #rtc.datetime((año, mes, dia, dia_semana, hora_local, minuto, segundo, subseg))
        #print("Hora local ajustada:", rtc.datetime())
    except Exception as e:
        print("Error al sincronizar NTP:", e)
        #rtc.datetime((2025, 6, 13, 0, 18, 0, 0, 0))

    # Desconectar de la red, pero dejar STA activo para ESP-NOW
    if wlan.isconnected():
        wlan.disconnect()
    print("WiFi desconectado pero interfaz activa para ESP-NOW")

else:
    print("Despertó del modo deep sleep, usando hora de RTC")
    wlan.active(True)  # Para ESP-NOW

# Obtener timestamp
fecha_hora = rtc.datetime()
timestamp = "{:04d}-{:02d}-{:02d},".format(*fecha_hora[:3])
timestamp += "{:02d}:{:02d}:{:02d}".format(*fecha_hora[4:7])

# Montar SD
sd = machine.SDCard(slot=2, freq=1000000)
os.mount(sd, '/sd')

# Configurar ADCs
adc1 = ADC(Pin(32))
adc1.atten(ADC.ATTN_11DB)   
adc2 = ADC(Pin(12))
adc2.atten(ADC.ATTN_11DB)

val1 = adc1.read_u16()
val2 = adc2.read_u16()

# Convertir a milivoltios y voltios
mV = val1 * (2450 - 150) / 2**16
mV2 = val2 * (2450 - 150) / 2**16
V = mV / 1000
V2 = mV2 / 1000

# Calcular H y H2
H = 2.589e-10 * mV**4 - 5.010e-7 * mV**3 + 3.523e-4 * mV**2 - 9.135e-2 * mV + 7.457
H2 = mV * (1250 - 300) / 0.69
H22 = 2.589e-10 * mV2**4 - 5.010e-7 * mV2**3 + 3.523e-4 * mV2**2 - 9.135e-2 * mV2 + 7.457

# Formar línea de registro
r = f"{timestamp},{val1},{V},{H},{H2},{val2},{V2},{H22}\n"

# Escribir en SD
with open('/sd/registro.txt', 'a') as f:
    f.write(r)
    print("Guardado en SD:", r)

# ENVIAR POR ESP-NOW
e = espnow.ESPNow()
e.active(True)

# Dirección MAC del receptor (broadcast)
peer = b'\xff\xff\xff\xff\xff\xff'
e.add_peer(peer)

print("Enviando por ESP-NOW:", r)
e.send(peer, r.encode())

# Esperar un poco para asegurar envío
sleep(0.5)
wlan.active(False)  # Para ESP-NOW

# Apagar todo antes de deep sleep
os.umount('/sd')
led.value(0)

tsleep = 3
print("Entrando en modo deep sleep por {} minutos...".format(tsleep))
machine.deepsleep(60000*tsleep)
