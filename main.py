from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import json

app = FastAPI()


class ConnectionManager:
    """
    Gestiona las conexiones WebSocket agrupadas por canal.
    Cada canal (identificado por un entero) mantiene una lista de conexiones activas.
    """
    def __init__(self):
        self.active_connections: dict[int, list[WebSocket]] = {}

    async def connect(self, channel: int, websocket: WebSocket):
        """Acepta la conexión y la registra en el canal correspondiente."""
        await websocket.accept()
        if channel not in self.active_connections:
            self.active_connections[channel] = []
        self.active_connections[channel].append(websocket)

    def disconnect(self, channel: int, websocket: WebSocket):
        """Elimina la conexión del canal indicado; si el canal queda vacío, se elimina la clave."""
        if channel in self.active_connections:
            self.active_connections[channel].remove(websocket)
            if not self.active_connections[channel]:
                del self.active_connections[channel]

    async def broadcast(self, channel: int, message: str):
        """Envía un mensaje de texto a todas las conexiones activas del canal."""
        if channel in self.active_connections:
            for connection in self.active_connections[channel]:
                await connection.send_text(message)


# Instancia del gestor de conexiones
manager = ConnectionManager()


@app.websocket("/ws/{channel}")
async def websocket_endpoint(websocket: WebSocket, channel: int):
    """
    Endpoint WebSocket:
    - El parámetro 'channel' identifica el canal de conexión (debe ser un número entero).
    - Al recibir un mensaje del cliente, se reenvía a todos los clientes conectados en ese mismo canal.
    """
    await manager.connect(channel, websocket)
    try:
        while True:
            # Recibe mensajes del cliente
            data = await websocket.receive_text()
            print(f"Mensaje recibido en el canal {channel}: {data}")
            # Se retransmite el mensaje a todos los clientes conectados al canal
            await manager.broadcast(channel, data)
    except WebSocketDisconnect:
        manager.disconnect(channel, websocket)
        print(f"Cliente desconectado del canal {channel}")
