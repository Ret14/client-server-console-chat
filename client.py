import signal
import socket
import threading

# nickname = input("Выберите имя пользователя: ")

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Инициализация сокета

client.connect(('127.0.0.1', 4001))  # Соединение клиента с сервером


class ServerTerminationError(Exception):
    pass


def exit_gracefully(signum, frame):
    raise ServerTerminationError()


# gracefully exit on -2
signal.signal(signal.SIGINT, exit_gracefully)
# gracefully exit on -15
signal.signal(signal.SIGTERM, exit_gracefully)


def receive():
    while True:  # Подтверждение соединения
        try:
            message = client.recv(1024).decode('utf-8')
            print(message)
        except:  # Если неправильный ip или порт
            print("Error!")
            client.close()
            exit(0)


def write():
    while True:  # Вывод сообщений в чат
        message = input('> ')
        client.send(message.encode('utf-8'))


receive_thread = threading.Thread(target=receive)  # Получение всех сообщений
receive_thread.start()
write_thread = threading.Thread(target=write)  # Отправка всех сообщений
write_thread.start()
