import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

_SESSION_TTL_MINUTES = 30

_sessions: dict[str, "_HitlSession"] = {}
_lock = threading.Lock()


@dataclass
class _HitlSession:
    session_id: str
    requirement_text: str
    top_k: int
    ambiguities: list[dict]
    created_at: datetime
    expires_at: datetime
    consumed: bool = False


def create_session(
    session_id: str,
    requirement_text: str,
    top_k: int,
    ambiguities: list[dict],
) -> _HitlSession:
    now = datetime.now()
    session = _HitlSession(
        session_id=session_id,
        requirement_text=requirement_text,
        top_k=top_k,
        ambiguities=ambiguities,
        created_at=now,
        expires_at=now + timedelta(minutes=_SESSION_TTL_MINUTES),
    )
    with _lock:
        _purge_expired_unsafe()
        _sessions[session_id] = session
    return session


def get_session(session_id: str) -> Optional[_HitlSession]:
    with _lock:
        session = _sessions.get(session_id)
        if session is None or session.consumed or datetime.now() > session.expires_at:
            return None
        return session


def consume_session(session_id: str) -> Optional[_HitlSession]:
    """Marca la sesión como consumida y la retorna. Operación atómica.

    Si la sesión ya fue consumida, expiró o no existe, retorna None.
    Previene que dos llamadas concurrentes de Fase 2 con el mismo
    session_id ambas procedan.
    """
    with _lock:
        session = _sessions.get(session_id)
        if session is None or session.consumed or datetime.now() > session.expires_at:
            return None
        session.consumed = True
        return session


def _purge_expired_unsafe() -> int:
    """Elimina sesiones expiradas. Debe llamarse con _lock ya adquirido."""
    now = datetime.now()
    expired = [sid for sid, s in _sessions.items() if now > s.expires_at]
    for sid in expired:
        del _sessions[sid]
    return len(expired)
