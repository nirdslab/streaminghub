from random import randint
from threading import Thread
from time import sleep

import empatica_e4.connector as conn


def data_thread(name, freq, channels):
    i = 0
    while True:
        conn.process_data_stream(f"{name} {' '.join(map(str, [i, *[randint(1, 5) for x in range(channels)]]))}")
        sleep(1 / freq)
        i += 1


if __name__ == '__main__':
    conn.DEVICE_ID = 'test'
    threads = [
        Thread(target=data_thread, args=('E4_Acc', 32, 3)),
        Thread(target=data_thread, args=('E4_Bvp', 64, 1)),
        Thread(target=data_thread, args=('E4_Gsr', 1, 1)),
        Thread(target=data_thread, args=('E4_Ibi', 1, 1)),
        Thread(target=data_thread, args=('E4_Hr', 1, 1)),
        Thread(target=data_thread, args=('E4_Temperature', 0.5, 1)),
        Thread(target=data_thread, args=('E4_Battery', 0.1, 1)),
        Thread(target=data_thread, args=('E4_Tag', 0.1, 0)),
    ]
    for thread in threads:
        thread.start()
    print('streaming started...')
    threads[0].join()
