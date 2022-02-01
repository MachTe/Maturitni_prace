import sounddevice as sd
import time as tm
import threading
import math

default_samplerate = 44100
buffer_lenght = 44100
target_frequency_a = 19500
target_frequency_b = 20950
chunk_size = 47
count = 0
exitFlag = 0
running = True
Buffer = []
print(Buffer)
start = tm.time()


class myThread(threading.Thread):
    def __init__(self, counter):
        threading.Thread.__init__(self)
        self.counter = counter

    def run(self):
        listen(1)


def audio_callback(indata, frames, time, status):
    global Buffer
    if exitFlag:
        thread_listening.exit()
    Buffer = Buffer + indata.tolist()


def listen(counter):
    global exitFlag
    stream = sd.InputStream(callback=audio_callback, samplerate=default_samplerate, blocksize=buffer_lenght, channels=1)
    with stream:
        # Allows the listening to last for 1 second.
        sd.sleep(15000)


def find_frequency(indata, target_frequency):
    Sigma = 0
    freq = len(indata) / default_samplerate * target_frequency
    for sample in range(len(indata)):
        Sigma += indata[sample][0] * math.e ** (-2 * freq * math.pi * sample / len(indata) * 1j)

    return abs(Sigma)


def skip(num):
    if num == 1:
        return 1
    else:
        return 0


def signal_processing():
    global running, Buffer, exitFlag
    count = 0
    iteration = 0
    silent_average_a = 0
    loud_average_a = 0
    average_buffer = [0, 0, 0]

    while running:
        if len(Buffer) == 0:
            tm.sleep(0.02)
        else:
            count += 1
            for i in range(skip(count)*int(18000/chunk_size), int(default_samplerate/chunk_size)):
                print(find_frequency(Buffer[i * chunk_size:chunk_size * (1 + i)], target_frequency_a))
                if iteration < 10:
                    silent_average_a += find_frequency(Buffer[i * chunk_size:chunk_size * (1 + i)], target_frequency_a) / 10
                    iteration += 1
                elif iteration == 10:
                    average_buffer[i % 3] = find_frequency(Buffer[i * chunk_size:chunk_size * (1 + i)], target_frequency_a) / 3
                    if sum(average_buffer) > 3 * silent_average_a:
                        iteration += 1
                        print("loud frequency intercepted!!!")
                elif 10 < iteration < 16:
                    loud_average_a += find_frequency(Buffer[i * chunk_size:chunk_size * (1 + i)], target_frequency_a) / 5
                    iteration += 1
                elif iteration == 16:
                    print("Average amplitude of silent frequency is " + str(round(silent_average_a, 8)))
                    print("Average amplitude of loud frequency is " + str(round(loud_average_a, 8)))
                    running = False
                    exitFlag = False
                    break
            Buffer = Buffer[buffer_lenght:]


thread_listening = myThread(0)
thread_listening.start()
signal_processing()

start = tm.time()
print(count)
