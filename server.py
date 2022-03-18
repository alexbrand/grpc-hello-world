import asyncio
import collections
import logging
import random
import os
import grpc
import time

helloworld_pb2, helloworld_pb2_grpc = grpc.protos_and_services(
    "helloworld.proto")

class Greeter(helloworld_pb2_grpc.GreeterServicer):

    def __init__(self):
        self._counter = collections.defaultdict(int)

    async def SayHello(
            self, request: helloworld_pb2.HelloRequest,
            context: grpc.aio.ServicerContext) -> helloworld_pb2.HelloReply:

        logging.info(f'Successfully responding to RPC from {request.name} @ {context.peer()}')
        return helloworld_pb2.HelloReply(message='Hello, %s!' % request.name)


async def serve(listen_addr) -> None:
    server = grpc.aio.server()
    helloworld_pb2_grpc.add_GreeterServicer_to_server(Greeter(),
                                                      server)
    server.add_insecure_port(listen_addr)
    logging.info("Starting server on %s", listen_addr)
    await server.start()
    await server.wait_for_termination()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,format="timestamp=%(asctime)s level=%(levelname)s threadName=%(threadName)s msg=%(message)s", datefmt="%m/%d/%Y %I:%M:%S %p %Z")
    logging.Formatter.converter = time.gmtime
    listen_addr = os.getenv("LISTEN_ADDRESS", "localhost:8081")
    asyncio.run(serve(listen_addr))
