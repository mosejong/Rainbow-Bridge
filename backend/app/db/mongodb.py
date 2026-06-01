"""MongoDB 연결 관리 (Motor 비동기 드라이버)."""
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings


class _MongoDB:
    client: AsyncIOMotorClient | None = None

    def connect(self) -> None:
        self.client = AsyncIOMotorClient(settings.MONGO_URI)

    def close(self) -> None:
        if self.client:
            self.client.close()

    @property
    def db(self):
        if not self.client:
            raise RuntimeError("MongoDB가 연결되지 않았습니다. connect()를 먼저 호출하세요.")
        return self.client[settings.MONGO_DB_NAME]


mongodb = _MongoDB()
