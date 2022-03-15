import asyncio
import json
import logging
import os
import grpc
import time

helloworld_pb2, helloworld_pb2_grpc = grpc.protos_and_services(
    "helloworld.proto")

async def sayHello(stub, req):
    response = await stub.SayHello(req)
    print("Greeter client received: " + response.message)

async def worker(stub, name, queue):
    while True:
        req = await queue.get()
        response = await sayHello(stub, req)
        if isinstance(response, grpc.aio.AioRpcError):
            print(r.debug_error_string())
        queue.task_done()

async def main():
    logging.basicConfig()
    server_url = os.getenv("SERVER_URL", "localhost:8081")
    ssl_credentials = grpc.ssl_channel_credentials()
    channel = grpc.aio.secure_channel(server_url, ssl_credentials) 
    stub = helloworld_pb2_grpc.GreeterStub(channel)

    queue = asyncio.Queue()

    for i in range(10000):
        req = helloworld_pb2.HelloRequest(name=f"you #{i}")
        queue.put_nowait(req)

    tasks = []
    for i in range(200):
        task = asyncio.create_task(worker(stub, f'worker-{i}', queue))
        tasks.append(task)

    # Wait until the queue is fully processed.
    started_at = time.monotonic()
    await queue.join()
    total_time = time.monotonic() - started_at

        # Cancel our worker tasks.
    for task in tasks:
        task.cancel()
    # Wait until all worker tasks are cancelled.
    await asyncio.gather(*tasks, return_exceptions=True)

    print('====')
    print(f'3 workers drained the queue in {total_time:.2f} seconds')

if __name__ == '__main__':
    asyncio.run(main())
