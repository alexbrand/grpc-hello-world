import asyncio
import json
import logging
import os
import grpc
from tenacity import AsyncRetrying, RetryError, stop_after_attempt
from tenacity.wait import wait_random_exponential
import time
import random

helloworld_pb2, helloworld_pb2_grpc = grpc.protos_and_services(
    "helloworld.proto")

async def sayHello(stub, count):
    try:
        async for attempt in AsyncRetrying(stop=stop_after_attempt(5), wait=wait_random_exponential(multiplier=0.2, max=1)):
            with attempt:
                response = await stub.SayHello(helloworld_pb2.HelloRequest(name=f"you #{count}"))
                print("Greeter client received: " + response.message)
                return response
    except Exception as ex:
        print(f"{ex}")
        pass

async def main():
    logging.basicConfig()
    server_url = os.getenv("SERVER_URL", "localhost:8081")
    ssl_credentials = grpc.ssl_channel_credentials()
    channel = grpc.aio.secure_channel(server_url, ssl_credentials) 
    stub = helloworld_pb2_grpc.GreeterStub(channel)

    tasks = [sayHello(stub, i) for i in range(0, 10000)]
    await asyncio.gather(*tasks, return_exceptions=True)

if __name__ == '__main__':
    asyncio.run(main())
