import socket  # noqa: F401
import threading

server_socket = socket.create_server(("127.0.0.1", 6379), reuse_port=True)

def handler(sock, addr):
    print(f'Connected with client at addr {addr}')

    while True:
        request = sock.recv(1024)
        request = request.decode("utf-8")
        data = request.split('\\n')
        for string in data:
            if string == '':
                break
            sock.send('+PONG\r\n'.encode('utf-8'))
    sock.close()
    server_socket.close()

 
def main():
    print("Logs from your program will appear here!")
    while True:
        sock, addr = server_socket.accept() # wait for client

        thread = threading.Thread(target=handler, args=(sock, addr))
        thread.start()


if __name__ == "__main__":
    main()
