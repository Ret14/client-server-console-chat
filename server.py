import signal
import socket
import threading  # Импорт библиотек

from SQL_orm.models.model import Users, Messages, PrivateMessages
from SQL_orm.mysql_orm.client import MysqlORMClient

host = '127.0.0.1'  # Локальный хост компьютера
port = 4001  # Выбор незарезервированного порта

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Инициализация сокета
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind((host, port))  # Назначение хоста и порта к сокету
server.listen()

db_client = MysqlORMClient()
db_client.connect()
clients = []
active_users = []


class ServerTerminationError(Exception):
    db_client.connection.close()


def exit_gracefully(signum, frame):
    raise ServerTerminationError()


# gracefully exit on -2
signal.signal(signal.SIGINT, exit_gracefully)
# gracefully exit on -15
signal.signal(signal.SIGTERM, exit_gracefully)


def close():
    db_client.connection.close()
    server.shutdown(socket.SHUT_RDWR)
    server.close()
    print("closed")


def broadcast(message, sender_username):  # Функция связи
    sender_client = clients[active_users.index(sender_username)]
    for client in clients:
        if client != sender_client:
            client.send(f'{sender_username}: {message}'.encode('utf-8'))


def send_private_message(sender_username, target_username, message):
    sender_client = clients[active_users.index(sender_username)]
    if target_username not in active_users:
        sender_client.send('* Error! User offline or deleted *'.encode('utf-8'))
    else:
        target_client = clients[active_users.index(target_username)]
        target_client.send(f'(private) {sender_username}: {message}'.encode('utf-8'))


def command_interface():
    while True:
        print('Ready for commands!')
        full_command = input().strip()
        if full_command.startswith('-'):
            if ' ' in full_command:
                command, username = full_command.split(' ')
                if command == '-messages':
                    print(get_user_messages(username))
                elif command == '-delete':
                    disconnect_and_delete_user(username)
            else:
                if full_command == '-active':
                    print(active_users)
                elif full_command == '-all':
                    print(get_all_usernames())
                elif full_command == '-exit':
                    close()
        else:
            print('Command doesn\'t exist')


def get_user_messages(username):
    user_id = get_user_id(username)
    raw_messages = db_client.session.query(Messages).filter(Messages.user_id == user_id).all()
    private_raw_messages = db_client.session.query(Users.username, PrivateMessages).join(
        Users, PrivateMessages.target_id == Users.id).filter(PrivateMessages.sender_id == user_id).all()
    private_raw_sent_to_user = db_client.session.query(Users.username, PrivateMessages).join(
        Users, PrivateMessages.sender_id == Users.id).filter(PrivateMessages.target_id == user_id).all()

    from_list = list(map(lambda x: f'*from {x[0]}* {x[1].text}', private_raw_sent_to_user))
    while '' in from_list:
        from_list.remove('')
    all_messages = list(map(lambda x: x.text, raw_messages))
    while '' in all_messages:
        all_messages.remove('')
    to_messages = list(map(lambda x: f'*to {x[0]}* {x[1].text}', private_raw_messages))
    while '' in to_messages:
        to_messages.remove('')

    # print(private_raw_messages)
    return all_messages + to_messages + from_list



def get_all_usernames():
    raw_user_data = db_client.session.query(Users).all()
    return list(map(lambda x: x.username, raw_user_data))


def handle(client, username):
    while True:
        try:  # Получение сообщений от клиента
            message = client.recv(1024).decode('utf-8').strip()
            if message.startswith('-to') and ' ' in message:
                target_username = message.split('-to')[-1].split(' ')[0]
                index_after_space = message.find(' ') + 1
                private_message = message[index_after_space:]
                send_private_message(username, target_username, private_message)
                add_private_message_to_db(
                    get_user_id(username),
                    get_user_id(target_username),
                    private_message)
            else:
                broadcast(message, username)
                add_message_to_db(get_user_id(username), message)

        except KeyboardInterrupt:
            print("[!] Keyboard Interrupted!")
            close()
            break
        except:  # Удаление клиентов
            if username not in active_users:
                break
            index = clients.index(client)
            clients.remove(client)
            client.close()
            nickname_left = active_users[index]
            broadcast(f'User {nickname_left} left the chatroom', username)
            active_users.remove(nickname_left)
            break


def check_credentials(credentials: str):
    username, password = credentials.split(" ")
    db_client.session.commit()
    return bool(db_client.session.query(Users).filter(
        Users.username == username,
        Users.password == password
    ).all())


def disconnect_and_delete_user(username):
    disconnect_user(username)

    if check_username_in_db(username):
        remove_user_from_db(username)


def disconnect_user(username):
    if username in active_users:
        index = active_users.index(username)
        active_users.remove(username)
        client_disconnected = clients[index]
        client_disconnected.send('You were disconnected from the server!'.encode('utf-8'))
        client_disconnected.close()
        clients.remove(client_disconnected)
        broadcast(f'User {username} left the chatroom', username)


def add_new_user(credentials: str):
    username, password = credentials.split(" ")
    db_client.session.commit()
    new_user = Users(username=username,
                     password=password
                     )
    db_client.session.add(new_user)
    db_client.session.commit()


def remove_user_from_db(username):
    db_client.session.query(Users).filter(Users.username == username).delete()
    db_client.session.commit()


def add_message_to_db(user_id, message):
    db_client.session.commit()
    new_message = Messages(user_id=user_id,
                           text=message
                           )
    db_client.session.add(new_message)
    db_client.session.commit()


def add_private_message_to_db(sender_id, target_id, message):
    db_client.session.commit()
    new_private_message = PrivateMessages(sender_id=sender_id,
                                          target_id=target_id,
                                          text=message
                                          )
    db_client.session.add(new_private_message)
    db_client.session.commit()


def get_user_id(username):
    return db_client.session.query(Users).filter(Users.username == username).one().id


def check_username_in_db(username):
    return bool(db_client.session.query(Users).filter(Users.username == username).all())


def receive():  # Подключение нескольких клиентов
    while True:
        cmd_thread = threading.Thread(target=command_interface)
        cmd_thread.start()
        client, address = server.accept()
        print("Connected with {}".format(str(address)))
        client.send('Sign in / Sign up \n (0 / 1)'.encode('utf-8'))
        chosen_option = client.recv(1).decode('utf-8').strip()
        while chosen_option != '0' and chosen_option != '1':
            print(f'`{chosen_option}`')
            chosen_option = client.recv(1).decode('utf-8').strip()
        client.send('Enter credentials like: {login} {password}'.encode('utf-8'))
        credentials = client.recv(100).decode('utf-8').strip()
        if chosen_option == '0':
            while not check_credentials(credentials) or credentials.split(' ')[0] in active_users:
                client.send('Not found. Try again'.encode('utf-8'))
                credentials = client.recv(100).decode('utf-8').strip()
        else:
            while " " not in credentials:
                client.send('Incorrect input. Try again'.encode('utf-8'))
                credentials = client.recv(100).decode('utf-8').strip()
            add_new_user(credentials)

        username = credentials.split(" ")[0]

        active_users.append(username)
        clients.append(client)
        print(f'{username} connected successfully\n')
        broadcast(f'user {username} joined the chatroom\n', username)
        client.send('You are connected. Start chatting!'.encode('utf-8'))
        thread = threading.Thread(target=handle, args=(client, username))
        thread.start()


receive()

