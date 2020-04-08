import asyncio
from asyncio import transports
from typing import Optional


class ServerProtocol(asyncio.Protocol):
    login: str = None
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server

    def data_received(self, data: bytes):
        print(data)

        decoded = data.decode()

        if self.login is not None:
            if len(decoded.replace("\r\n", "")) > 0:
                self.send_message(decoded)
        else:
            if decoded.startswith("login:"):
                login = decoded.replace("login:", "").replace("\r\n", "")
                client_exists = False
                for new_client in self.server.clients:
                    if new_client.login == login:
                        client_exists = True
                if client_exists is True:
                    print("duplicate")
                    self.transport.write("login already in use".encode())
                    self.transport.close()
                else:
                    self.login = login
                    self.transport.write(f"Hi,{self.login}!\n".encode())
                    self.send_history()
            else:
                self.transport.write("Wrong login\n".encode())

    def connection_made(self, transport: transports.Transport):
        self.server.clients.append(self)
        self.transport = transport

        print("New client")

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print("client exit")

    def send_message(self, content: str):
        message=f"{self.login}:{content}\n"
        self.server.add_to_history(message)

        for user in self.server.clients:
            user.transport.write(message.encode())

    def send_history(self):
        if len(self.server.message_history) > 0:
            for message in self.server.message_history:
                self.transport.write(message.encode())


class Server:
    clients: list
    message_history: list

    def __init__(self):
        self.clients = []
        self.message_history = []

    def build_protocol(self):
        return ServerProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.build_protocol,
            '127.0.0.1',
            8888
        )
        print("Server is running")
        await coroutine.serve_forever()

    def add_to_history(self, message: str):
        if len(self.message_history) == 10:
            to_remove = self.message_history.pop(0)
        self.message_history.append(message)


process = Server()
try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Server stop by admin")