import machine
import struct

class MLX90614:
    def __init__(self, i2c, address=0x5A):
        self.i2c = i2c
        self.address = address

    def read_register(self, register):
        data = self.i2c.readfrom_mem(self.address, register, 3)
        lsb, msb, pec = struct.unpack("<BBb", data)
        temp = (msb << 8) | lsb
        return temp * 0.02 - 273.15  # Convertir a grados Celsius

    def read_ambient_temp(self):
        return self.read_register(0x06)

    def read_object_temp(self):
        return self.read_register(0x07)
