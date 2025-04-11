from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel
import json

app = FastAPI()

# Modelo para la notificación entrante
class Notification(BaseModel):
    target_channel: str
    mensaje: dict

# Clase que gestiona las conexiones WebSocket agrupadas por "channel" (sede)
class ConnectionManager:
    def __init__(self):
        # Diccionario que guarda listas de conexiones para cada channel
        self.active_connections: dict[int, list[WebSocket]] = {}
    
    async def connect(self, channel: int, websocket: WebSocket):
        await websocket.accept()
        if channel not in self.active_connections:
            self.active_connections[channel] = []
        self.active_connections[channel].append(websocket)
    
    def disconnect(self, channel: int, websocket: WebSocket):
        if channel in self.active_connections:
            self.active_connections[channel].remove(websocket)
            if not self.active_connections[channel]:
                del self.active_connections[channel]
    
    async def broadcast(self, channel: int, message: str):
        if channel in self.active_connections:
            for connection in self.active_connections[channel]:
                await connection.send_text(message)

# Instancia del gestor de conexiones
manager = ConnectionManager()

# Endpoint WebSocket. La ruta incluye el parámetro "channel" para identificar la sede
@app.websocket("/ws/{channel}")
async def websocket_endpoint(websocket: WebSocket, channel: str):
    await manager.connect(channel, websocket)
    try:
        while True:
            # Se pueden recibir mensajes del cliente (opcional, en este ejemplo solo se registra)
            data = await websocket.receive_text()
            print(f"Mensaje recibido de la sede {channel}: {data}")
    except WebSocketDisconnect:
        manager.disconnect(channel, websocket)
        print(f"Cliente desconectado de la sede {channel}")


# Endpoint para enviar notificaciones. Recibe un JSON con la notificación y la transmite
@app.post("/notify/")
async def notify(notification: Notification):
    # Verificar que el tipo de notificación es el esperado
   
    message_text = notification.json()
    # Enviar el mensaje a todos los clientes conectados en la sede objetivo
    await manager.broadcast(notification.target_channel, message_text)
    return {"status": "Notificación enviada"}
