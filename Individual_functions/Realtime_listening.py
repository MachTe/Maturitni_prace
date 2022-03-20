import sounddevice as sd
import math

default_samplerate = 44100
carrier_frequency = 20700
impulse_lenght = 49

def audio_callback(indata, frames, time, status):
  # Listens to a impulse_lenght of samples and then looks for the target frequency.
  
   Sigma = 0
   freq = frames / default_samplerate * carrier_frequency
   for sample in range(len(indata)):
      Sigma += indata[sample][0] * math.e ** (-2 * freq * math.pi * sample / len(indata) * 1j)
   print(str(abs(Sigma)) + " is the amplitude of " + str(carrier_frequency) + "Hz frequency.")


stream = sd.InputStream(callback=audio_callback, samplerate=default_samplerate, blocksize=impulse_lenght)

with stream:
  # Allows the listening to last for 1 second.
   sd.sleep(1000)
