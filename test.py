import asyncio

async def limited_worker(times):
    for i in range(times):
        print(f"Итерация {i+1}")
        await asyncio.sleep(3)
    print("Готово!")

while True:
    asyncio.run(limited_worker(5))