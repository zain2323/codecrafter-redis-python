import socket
from threading import Thread
from enum import Enum
from datetime import datetime, timedelta
import argparse

COMMANDS = [
    'PING', 'ECHO', 'SET', 'GET', 'CONFIG'
]
# On memory dict
ON_MEM_DICT = {}
# stores configuration settings
CONFIG_DICT = {
    'dir': '/tmp/redis-files',
    'dbfilename': 'dump.rdb'
}

class RedisResponse(Enum):
    NIL = -1
    INTEGER = 1
    STRING = 2
    ARRAY = 3
    ERROR = 4

server_socket: socket.socket = socket.create_server(("127.0.0.1", 6379), reuse_port=True)

def extract_command_type(arg: str) -> str:
    if arg[0] == '*':
        return 'arrays'
    return 'unknown'

def extract_command_args(args: list[str], start: int) -> list[str]:
    command_args: list[str] = []
    for i in range(start, len(args)):
        # skipping string len entries
        if args[i].startswith('$'):
            continue
        # slicing : on integer data types
        if args[i].startswith(':'):
            args[i] = args[i][1:]
        command_args.append(args[i])
    return command_args[0:len(command_args)-1]

def decode_resp(request: str) -> dict:
    args: list[str] = request.strip().split('\\r\\n')
    data_type = ''
    commands: dict = {}
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
            break
    return commands

def encode_resp(to_send: str) -> bytes:
    to_send = to_send.split('+')
    encoded_str = ''
    for element in to_send:
        if element == '':
            continue
        if element == RedisResponse.NIL.name:
            length = RedisResponse.NIL.value
            element = ''
        else:
            length = len(element)
        encoded_str += f'${length}\r\n{element}\r\n'
    return encoded_str.encode('utf-8')

def handler(sock: socket.socket, addr: int) -> None:
    print(f"connected with client on address {addr}")
    while True:
        request:str = sock.recv(1024).decode("utf-8")
        commands: dict = decode_resp(request)
        to_send = []
        encoded_response: bytes = b''
        for command in commands:
            if command == 'PING':
                to_send = '+PONG' * commands[command]['count']
                
            if command == 'ECHO':
                to_send = "".join(commands[command]['args'])
                
            if command == 'SET':
                key, value, *extra_args = commands[command]['args']
                # Extract TTL (in milliseconds) if provided
                if 'px' in extra_args:
                    ttl_index = extra_args.index('px') + 1
                    ttl = int(extra_args[ttl_index])
                else:
                    ttl = None
                    
                ON_MEM_DICT[key] = {
                    'value': value,
                    'ttl': ttl,
                    'timestamp': datetime.now()
                    }
                to_send = '+Ok'
                
            if command == 'GET':
                key = commands[command]['args'][0]
                value = ON_MEM_DICT.get(key) or 'NIL'
                ttl = value.get('ttl')
                timestamp = value.get('timestamp')
                if not ttl:
                    to_send = value.get('value')
                else:
                    if datetime.now() > timestamp + timedelta(milliseconds=ttl):
                        del ON_MEM_DICT[key]
                        to_send = 'NIL'
                    else:
                        to_send = value.get('value')
            
            if command == 'CONFIG':
                subcommand, *extra_args = commands[command]['args']
                to_send = ''
                if subcommand.upper() == 'GET':
                    for arg in extra_args:
                        to_send += CONFIG_DICT.get(arg) + ' '
                    
            encoded_response = encode_resp(to_send)
        sock.sendall(encoded_response)
    sock.close()
    server_socket.close()

 
def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--dir', type=str)
    parser.add_argument('--dbfilename', type=str)
    args = parser.parse_args()
    if args.dir:
        CONFIG_DICT['dir'] = args.dir
    if args.dbfilename:
        CONFIG_DICT['dbfilename'] = args.dbfilename
    print("Listening on 127.0.0.1 on port 6379")
    while True:
        sock, addr = server_socket.accept() # wait for client
        thread: Thread = Thread(target=handler, args=(sock, addr))
        thread.start()


if __name__ == "__main__":
    main()
