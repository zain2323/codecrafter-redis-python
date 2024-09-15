import socket  # noqa: F401
from threading import Thread

server_socket: socket.socket = socket.create_server(("127.0.0.1", 6379), reuse_port=True)

COMMANDS = "PING ECHO".split()

def extract_command_type(arg: str) -> str:
    if arg[0] == '*':
        return 'arrays'
    return 'unknown'

def extract_command_args(args: list[str], start: int) -> list[str]:
    command_args: list[str] = []
    for i in range(start, len(args)):
        if args[i].startswith('$'):
            continue
        if args[i].upper() not in COMMANDS:
            command_args.append(args[i])
    return command_args

def decode_resp(request: str) -> dict[str]:
    args: list[str] = request.strip().split('\\r\\n')
    data_type = ''
    commands: dict[str] = {}
    for i, arg in enumerate(args):
        if arg == '':
            break
        # skipping length
        if arg.startswith('$'):
            continue
        if i == 0:
            data_type = extract_command_type(arg)
        if arg.upper() in COMMANDS:
            command = arg.upper()
            if command:
                command_args: list[str] = extract_command_args(args, i+1)
                if not commands.get(command):
                    commands[command] = {
                        'count': 1,
                        'args': command_args
                    }
                else:
                    existing = commands.get(command)
                    existing['count'] += 1
                    commands[command] = existing
    return commands

def encode_resp(to_send: str) -> str:
    encoded_str = ''
    for element in to_send:
        if element == '':
            continue
        encoded_str += f'${len(element)}\r\n{element}\r\n'
    return encoded_str.encode('utf-8')

def handler(sock: socket.socket, addr: int) -> None:

    while True:
        request:str = sock.recv(1024).decode("utf-8")
        commands: dict['str'] = decode_resp(request)
        to_send: list[str] = []
        for command in commands:
            if command == 'PING':
                to_send = ('+PONG' * commands[command]['count']).split('+')
            if command == 'ECHO':
                to_send = commands[command]['args']
            encoded_respose: str = encode_resp(to_send)
        sock.sendall(encoded_respose)
    sock.close()
    server_socket.close()

 
def main() -> None:
    while True:
        sock, addr = server_socket.accept() # wait for client
        thread: Thread = Thread(target=handler, args=(sock, addr))
        thread.start()


if __name__ == "__main__":
    main()
