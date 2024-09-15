import socket  # noqa: F401


def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!")

    # Uncomment this to pass the first stage
    #
    server_socket = socket.create_server(("127.0.0.1", 6379), reuse_port=True)
    sock, addr = server_socket.accept() # wait for client
    print(f'Connected with client at addr {addr}')
    
    while True:
        request = sock.recv(1024)
        request = request.decode("utf-8")
        data = request.split('\\n')
        print(data)
        for string in data:
            if string == '':
                break
            sock.send('+PONG\r\n'.encode('utf-8'))
        
    sock.close()
    server_socket.close()

if __name__ == "__main__":
    main()
