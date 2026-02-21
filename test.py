import asyncio
from typing import Generator

from fastapi import APIRouter
from fastapi import FastAPI
from fastapi.testclient import TestClient


# 하위 async generator (서비스 역할)
async def lower_generator():
    for i in range(3):
        await asyncio.sleep(1)  # 비동기 대기 (예: DB/LLM 처리)
        print(f"[lower] generate: {i}")
        yield f"event-{i}"


# 상위 async generator (중계 역할)
async def event_generator():
    async for event in lower_generator():
        print(f"[upper] forwarding: {event}")
        yield event


# 소비자 (StreamingResponse 역할)
async def consumer():
    async for item in event_generator():
        print(f"[consumer] received: {item}")

# 실행
asyncio.run(consumer())

print("-------------------------")

def outer(message):
    message2 = message

    def inner():
        print(message2)   # 바깥 변수 사용
    return inner

f = outer("outer_closure_test")   # outer 실행 끝남
f()           # inner 실행, outer의 message 참조


class DocumentListItem:
    def __init__(self, id, title):
        self.id = id
        self.title = title
    

    
documents = [
    {"id":1, "title":"Python"},
    {"id":2, "title":"FastAPI"}
]    
    

items = [DocumentListItem(**doc) for doc in documents]
print(items)
