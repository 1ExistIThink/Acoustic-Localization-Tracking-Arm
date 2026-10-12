import spidev 
import lgpio
import time 

# Compared to ADCV1, this should try to make it sample 200ksps. 


ADC_CVA_CVB = 17 # Sampling Pulse 
ADC_RESET = 21 # GPIO Output for resetting ADC
ADC_BUSY = 20 # Tell Pi when ADC is busy

SPI_BUS = 0 # SPI Controller #0, 
SPI_DEV = 0 # Chip Select / Device Select CE0


CHIP = 4 # Group 4 pins 
h = lgpio.gpiochip_open(CHIP) # Open gpiochip4 so lgpio can use this group 4s pins 

spi = spidev.SpiDev()
spi.open(SPI_BUS, SPI_DEV) # Tells the Pi use SPI0 and CE0

# Enable Pins as output or input
lgpio.gpio_claim_output(h, ADC_CVA_CVB)
lgpio.gpio_claim_output(h, ADC_RESET)
lgpio.gpio_claim_input(h, ADC_BUSY)

lgpio.gpio_write(h, ADC_RESET, 1)
time.sleep(0.01)
lgpio.gpio_write(h, ADC_RESET, 0)

spi.max_speed_hz = 15_000_000 # this is the SPI clock speed the Pi will use. It will request this amount. 

spi.mode = 2 # SPI mode 2. 

# Function returns a list of len() 4, of raw adc values. 
def read_adc():
    lgpio.gpio_write(h, ADC_CVA_CVB, 1) # Tells the ADC to sample 
    time.sleep(1e-6) # Pulse width is 1us 
    lgpio.gpio_write(h, ADC_CVA_CVB, 0)

    while lgpio.gpio_read(h, ADC_BUSY) == 1: # When ADC is busy converting 
        pass

    raw = spi.readbytes(8) # Reads 8 bytes of data from SPI 

    # 8 bit = 1 byte. ADC is 16 bit or 2 byes resolution. We are looking at ch 1-4, so 8 bytes, incrementing 2. 
    values = []
    for i in range(0,8,2): # loop four times, once per ADC channel
        val = (raw[i] << 8 | raw[i + 1])
        if val & 0x8000: # If the value only has the leftmost bit and is equal to 1, then it is negative. 2s comp
            val -= 0x10_000 # Subtracts 65536 to make it into a normal negative number
        values.append(val)
    return values 

while True:
    data = read_adc()
    voltages = []
    for value in data:
        voltages.append(round(value*10/65536,3))
    print(voltages)
    time.sleep(0.01)
