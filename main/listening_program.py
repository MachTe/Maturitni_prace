import sounddevice as sd
import math

default_samplerate = 44100
target_frequency_a = 21006
target_frequency_b = 19800
buffer_lenght = 80

rolling_average_a = [0] * buffer_lenght
rolling_average_b = [0] * buffer_lenght

silent_average_a = 0
silent_average_b = 0

count = 0

calibrated = False


def find_frequency(indata, target_frequency)
   Sigma = 0
   freq = len(indata) / default_samplerate * target_frequency
   for sample in range(len(indata)):
      Sigma += indata[sample][0] * math.e ** (-2 * freq * math.pi * sample / len(indata) * 1j)
      
   return abs(Sigma)

def audio_callback(indata, frames, time, status):
  # Listens to a buffer_lenght of samples and then looks for the target frequency.
   if (not calibrated):
      if count < 10:
         silent_average_a += (find_frequency(indata[buffer_lenght:], target_frequency_a) + find_frequency(indata[:buffer_lenght], target_frequency_a)) / 20
         silent_average_b += (find_frequency(indata[buffer_lenght:], target_frequency_b) + find_frequency(indata[:buffer_lenght], target_frequency_b)) / 20
         count += 1
      elif: count == 10:
         # WHAT HAPPENS WHEN THE FIRST IMPULSE COMES


   Sigma2 = 0
   freq = frames / default_samplerate * target_frequency2
   for sample in range(len(indata)):
      Sigma2 += indata[sample][0] * math.e ** (-2 * freq * math.pi * sample / len(indata) * 1j)
      


stream = sd.InputStream(callback=audio_callback, samplerate=default_samplerate, blocksize=(buffer_lenght * 2))

with stream:
  # Allows the listening to last for 1 second.
   sd.sleep(3000)
