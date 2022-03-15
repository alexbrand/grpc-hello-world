import asyncio
import json
import logging
import os
import grpc

helloworld_pb2, helloworld_pb2_grpc = grpc.protos_and_services(
    "helloworld.proto")

async def sayHello(stub, count):
    response = await stub.SayHello(helloworld_pb2.HelloRequest(name=f"you #{count}"))
    print("Greeter client received: " + response.message)

async def gather_with_concurrency(n, *tasks):
    semaphore = asyncio.Semaphore(n)

    async def sem_task(task):
        async with semaphore:
            return await task
    return await asyncio.gather(*(sem_task(task) for task in tasks), return_exceptions=True)


async def main():
    logging.basicConfig()
    server_url = os.getenv("SERVER_URL", "localhost:8081")
    ssl_credentials = grpc.ssl_channel_credentials()
    channel = grpc.aio.secure_channel(server_url, ssl_credentials) 
    stub = helloworld_pb2_grpc.GreeterStub(channel)

    tasks = [sayHello(stub, i) for i in range(0, 10000)]
    results = await gather_with_concurrency(100, *tasks)
    for r in results:
        if isinstance(r, grpc.aio.AioRpcError):
            print(r.debug_error_string())

if __name__ == '__main__':
    asyncio.run(main())
