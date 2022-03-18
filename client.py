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

NUM_REQUESTS=10_000

async def say_hello(stub, count):
    response = await stub.SayHello(helloworld_pb2.HelloRequest(name=f"you #{count}"))
    print("Greeter client received: " + response.message)

async def gather_with_concurrency(n, *tasks):
    semaphore = asyncio.Semaphore(n)

    async def sem_task(task):
        async with semaphore:
            return await task
    return await asyncio.gather(*(sem_task(task) for task in tasks), return_exceptions=True)

async def test_semaphores(stub, count):
    tasks = [say_hello(stub, i) for i in range(NUM_REQUESTS)]
    return await gather_with_concurrency(count, *tasks)

async def worker(stub, name, queue):
    while True:
        requestNumber = await queue.get()
        try:
            response = await say_hello(stub, requestNumber)
        finally:
            queue.task_done()

async def test_queue(stub, numWorkers):
    queue = asyncio.Queue()
    for i in range(NUM_REQUESTS):
        queue.put_nowait(i)

    tasks = []
    for i in range(numWorkers):
        task = asyncio.create_task(worker(stub, f'worker-{i}', queue))
        tasks.append(task)

    await queue.join()
    # Cancel our worker tasks.
    for task in tasks:
        task.cancel()
    # Wait until all worker tasks are cancelled.
    return await asyncio.gather(*tasks, return_exceptions=True)

async def say_hello_with_retries(stub, count):
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

async def test_retries(stub):
    tasks = [say_hello_with_retries(stub, i) for i in range(0, NUM_REQUESTS)]
    return await asyncio.gather(*tasks, return_exceptions=True)

async def main():
    logging.basicConfig()
    server_url = os.getenv("SERVER_URL", "localhost:8081")
    ssl_credentials = grpc.ssl_channel_credentials()
    channel = grpc.aio.secure_channel(server_url, ssl_credentials) 
    stub = helloworld_pb2_grpc.GreeterStub(channel)

    #res = await test_semaphores(stub, count=100)
    #res = await test_retries(stub)
    res = await test_queue(stub, numWorkers=100)
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
