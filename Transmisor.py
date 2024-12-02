from machine import Pin, SPI, I2C, ADC
from nrf24l01 import NRF24L01
import struct
import utime

# Clase para el sensor MLX90614
class MLX90614:
    def __init__(self, i2c, address=0x5A):
        self.i2c = i2c
        self.address = address

    def read_register(self, register):
        data = self.i2c.readfrom_mem(self.address, register, 3)
        lsb, msb, pec = struct.unpack("<BBb", data)
        temp = (msb << 8) | lsb
        return temp * 0.02 - 273.15  # Convertir a grados Celsius

    def read_object_temp(self):
        return self.read_register(0x07)

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
    nrf.open_tx_pipe(pipes[0])  # Dirección del transmisor
    return nrf

# Configuración del sensor y el módulo
i2c = I2C(0, scl=Pin(1), sda=Pin(0), freq=100000)
sensor = MLX90614(i2c)
ecg_adc = ADC(Pin(26))  # Pin ADC para el sensor AD8232
nrf = setup_nrf()

# Variables para cálculo de BPM
threshold = 50000  # Umbral para detectar picos (ajustar según el sensor)
last_peak_time = 0
peak_count = 0
measurement_interval = 2  # Intervalo en segundos para calcular BPM (más rápido ahora)
start_time = utime.ticks_ms()

# Función de transmisión continua
def transmit_data():
    global last_peak_time, peak_count, start_time

    while True:
        try:
            # Leer temperatura
            temp = sensor.read_object_temp()

            # Leer señal del ECG
            ecg_value = ecg_adc.read_u16()  # Valor ADC (0 a 65535)
            current_time = utime.ticks_ms()

            # Detectar picos para calcular BPM
            if ecg_value > threshold and (current_time - last_peak_time) > 300:  # Evitar múltiples detecciones del mismo pico
                last_peak_time = current_time
                peak_count += 1

            # Calcular BPM cada intervalo definido
            elapsed_time = (utime.ticks_ms() - start_time) / 1000
            if elapsed_time >= measurement_interval:
                bpm = (peak_count / elapsed_time) * 60  # BPM extrapolado
                peak_count = 0  # Reiniciar contador
                start_time = utime.ticks_ms()  # Reiniciar tiempo

                print(f"Transmitting Temp: {temp:.2f} °C, BPM: {int(bpm)}")
                
                # Empaquetar datos y transmitir
                data = struct.pack("fi", temp, int(bpm))
                nrf.stop_listening()
                nrf.send(data)

        except OSError:
            print("Transmission failed")  
        
        utime.sleep(0.01)  # Intervalo de muestreo (10 ms) para mejorar la velocidad

# Iniciar transmisión
transmit_data()
