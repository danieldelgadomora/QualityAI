import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import TypeAdapter, ValidationError

from app.schemas.pipeline_ws import InboundMessage
from app.services.pipeline_orchestrator import PipelineOrchestrator

router = APIRouter(prefix="/pipeline", tags=["pipeline"])

_inbound_adapter = TypeAdapter(InboundMessage)


@router.websocket("/ws")
async def pipeline_ws(websocket: WebSocket):
    await websocket.accept()
    orch = PipelineOrchestrator()

    async def drain_sender():
        """Drena send_queue → websocket hasta recibir el centinela None."""
        while True:
            msg = await orch.send_queue.get()
            if msg is None:
                break
            try:
                await websocket.send_text(json.dumps(msg, default=str))
            except Exception:
                break

    pipeline_task = asyncio.create_task(orch.run())
    sender_task = asyncio.create_task(drain_sender())

    try:
        async for raw in websocket.iter_text():
            try:
                data = json.loads(raw)
                msg = _inbound_adapter.validate_python(data)
                await orch.recv_queue.put(msg)
            except (json.JSONDecodeError, ValidationError) as exc:
                await websocket.send_text(json.dumps({
                    "type": "pipeline_error",
                    "message": f"Mensaje inválido: {exc}",
                    "phase": "protocol",
                }))
    except WebSocketDisconnect:
        pass
    finally:
        pipeline_task.cancel()
        # Asegura que drain_sender pueda terminar si aún espera en la cola
        await orch.send_queue.put(None)
        await asyncio.gather(pipeline_task, sender_task, return_exceptions=True)
