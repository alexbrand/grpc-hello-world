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
        start = time.monotonic()
        print(f"request={count} start={time.monotonic()}")
        async for attempt in AsyncRetrying(stop=stop_after_attempt(5), wait=wait_random_exponential(multiplier=1, max=10)):
            with attempt:
                response = await stub.SayHello(helloworld_pb2.HelloRequest(name=f"you #{count}"))
                print("Greeter client received: " + response.message)
                print(f"request={count} latency={time.monotonic() - start}")
                return response
    except RetryError as re:
        print(f"request={count} latency={time.monotonic() - start}")
        re.reraise()

async def main():
    logging.basicConfig()
    server_url = os.getenv("SERVER_URL", "localhost:8081")
    ssl_credentials = grpc.ssl_channel_credentials()
    channel = grpc.aio.secure_channel(server_url, ssl_credentials) 
    stub = helloworld_pb2_grpc.GreeterStub(channel)

    tasks = [sayHello(stub, i) for i in range(0, 10_000)]
    res = await asyncio.gather(*tasks, return_exceptions=True)

    summary = {"success":0}
    for r in res:
        if not isinstance(r, grpc.aio.AioRpcError):
            summary["success"] += 1
            continue
        
        d = r.details()
        if d not in summary:
            summary[d] = 1
        else:
            summary[d] += 1

    print(summary)

if __name__ == '__main__':
    asyncio.run(main())
