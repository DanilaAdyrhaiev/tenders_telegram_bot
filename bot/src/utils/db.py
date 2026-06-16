from tinydb import TinyDB
from tinydb import Query
import asyncio
from src.models.user import User
from src.models.tender import Tender, Proposal
from datetime import datetime

db = TinyDB(
    "database.json",
    indent=4, 
    ensure_ascii=False
)

users = db.table("users")
tenders = db.table("tenders")

UserQ = Query()
TenderQ = Query()

user_lock = asyncio.Lock()
tender_lock = asyncio.Lock()

#User repository
async def get_user(user_id: int) -> User | None:
    def _read():
        data = users.get(UserQ.telegram_id == user_id)

        if not data:
            return None

        try:
            return User(**data)
        except Exception:
            return None

    return await asyncio.to_thread(_read)

async def get_users() -> list[User]:
    def _read():
        try:
            return [
                User(**user_data)
                for user_data in users.all()
            ]
        except Exception:
            return []

    return await asyncio.to_thread(_read)

async def get_users_count() -> int:
    def _count():
        return len(users.all())
    return await asyncio.to_thread(_count)


async def save_user(user: User):
    async with user_lock:
        def _write():
            user.updated_at = datetime.now().isoformat() # <-- Обновляем время
            users.upsert(
                user.model_dump(),
                UserQ.telegram_id == user.telegram_id
            )
        await asyncio.to_thread(_write)

#Tender repository
async def get_active_tenders() -> list[Tender]:
    def _read():
        try:
            data = tenders.search(TenderQ.is_active == True)
            return [Tender(**t) for t in data]
        except Exception:
            return []

    return await asyncio.to_thread(_read)

async def get_all_tenders() -> list[Tender]:
    def _read():
        try:
            return [Tender(**t) for t in tenders.all()]
        except Exception:
            return []

    return await asyncio.to_thread(_read)


async def get_tender(tender_id: int) -> Tender | None:
    def _read():
        data = tenders.get(TenderQ.tender_id == tender_id)

        if not data:
            return None

        try:
            return Tender(**data)
        except Exception:
            return None

    return await asyncio.to_thread(_read)

async def save_tender(tender: Tender):
    async with tender_lock:
        def _write():
            tender.updated_at = datetime.now().isoformat() # <-- Обновляем время
            tenders.upsert(
                tender.model_dump(),
                TenderQ.tender_id == tender.tender_id
            )
        await asyncio.to_thread(_write)


async def close_tender(tender_id: int):
    async with tender_lock:
        def _write():
            tenders.update(
                {"is_active": False},
                TenderQ.tender_id == tender_id
            )

        await asyncio.to_thread(_write)


async def add_proposal(tender_id: int, proposal: Proposal):
    async with tender_lock:
        def _write():
            tender = tenders.get(TenderQ.tender_id == tender_id)
            if not tender:
                return
            try:
                tender_obj = Tender(**tender)
                existing_prop = next((p for p in tender_obj.proposals if p.user_id == proposal.user_id), None)
                if existing_prop:
                    existing_prop.text = proposal.text
                else:
                    tender_obj.proposals.append(proposal)
                    
                tenders.update(
                    tender_obj.model_dump(),
                    TenderQ.tender_id == tender_id
                )

            except Exception:
                return

        await asyncio.to_thread(_write)

async def get_tenders_count() -> int:
    def _count():
        return len(tenders.all())

    return await asyncio.to_thread(_count)