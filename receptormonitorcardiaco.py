from machine import Pin, SPI, I2C
from nrf24l01 import NRF24L01
import struct
import utime
from ssd1306 import SSD1306_I2C

# Configuración de la pantalla OLED
WIDTH = 128
HEIGHT = 64
i2c = I2C(0, scl=Pin(1), sda=Pin(0), freq=400000)
oled = SSD1306_I2C(WIDTH, HEIGHT, i2c)

# Mostrar mensaje de verificación en la pantalla OLED
oled.fill(0)  # Limpiar la pantalla
oled.text("Pantalla OLED", 0, 0)
oled.text("Conectada", 0, 10)
oled.show()  # Mostrar el mensaje
utime.sleep(1)  # Mantener el mensaje en la pantalla durante 1 segundo

# Configuración de pines para NRF24L01
csn = Pin(15, mode=Pin.OUT, value=1)  # Chip select not
ce = Pin(14, mode=Pin.OUT, value=0)   # Chip enable

# Configuración de las direcciones
pipes = (b"\xa5\xf0\xf0\xf0\xf0", b"\xa5\xf0\xf0\xf0\xf0")

# Configuración del NRF24L01
def setup_nrf():
    print("Configurando NRF24L01...")
    nrf = NRF24L01(SPI(0), csn, ce, channel=76, payload_size=8)  # 8 bytes: 4 para temp y 4 para BPM
    nrf.reg_write(0x06, 0b00100110)  # 250 kbps
    nrf.open_rx_pipe(1, pipes[0])  # Dirección del receptor
    nrf.start_listening()
    return nrf

nrf = setup_nrf()

# Función para recibir y mostrar datos
def receive_and_display():
    while True:
        if nrf.any():  # Verifica si hay datos disponibles
            try:
                buffer = nrf.recv()  # Recibe el paquete
                temp, bpm = struct.unpack("fi", buffer)  # Desempaqueta los datos

                print(f"Received Temp: {temp:.2f} °C, BPM: {bpm}")
               
                # Limpiar la pantalla antes de mostrar nuevos datos
                oled.fill(0)

                # Mostrar la temperatura y BPM
                oled.text("Temp:", 0, 0)
                oled.text(f"{temp:.2f} C", 60, 0)
                oled.text("BPM:", 0, 16)
                oled.text(f"{bpm}", 60, 16)

                # Verificar si el BPM está dentro del rango normal (60-90)
                if 60 <= bpm <= 150:
                    oled.text("En buen estado!", 0, 32)
                    oled.text("    ** **  ", 0, 40)
                    oled.text("   *******  ", 0, 44)
                    oled.text("   ******* ", 0, 48)
                    oled.text("    *****  ", 0, 52)
                    oled.text("     ***   ", 0, 56)
                    oled.text("      *    ", 0, 60)
                else:
                    # Si el BPM no está en el rango, mostrar alerta
                    oled.text("¡ALERTA!",f"{bpm}", 0, 32)

                oled.show()  # Actualizar la pantalla con los nuevos datos
            except Exception as e:
                print(f"Error receiving data: {e}")
        else:
            # Esperar si no se reciben datos
            print("Esperando datos...")
        utime.sleep(0.5)  # Intervalo corto para evitar bloquear la ejecución

# Iniciar recepción y despliegue
receive_and_display()