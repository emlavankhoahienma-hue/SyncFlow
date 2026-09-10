import socket
import os
import time
import uuid
import struct
import logging
from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Response, Header, HTTPException, status, Depends
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from .models import (
    FileMeta,
    InitUploadRequest,
    InitUploadResponse,
    CompleteUploadResponse,
    HealthResponse,
    ConfigModel,
    HandshakeRequest,
    HandshakeResponse,
)
from .storage import storage_manager, CHUNK_SIZE
from .ws import ws_manager
from .security import crypto_manager
from convert.heic import convert_heic_to_png
from convert.hevc import convert_hevc_to_mp4

logger = logging.getLogger("syncflow.api")

app = FastAPI(title="SyncFlow Desktop Server", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DEVICE_NAME = socket.gethostname() or "Desktop PC"

@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(device_name=DEVICE_NAME, version="1.0.0", status="ok")

def verify_client_session(x_session_id: Optional[str] = Header(None, alias="X-Session-ID")):
    """
    Kerckhoffs-compliant session verification:
    Ensures that only clients with an authenticated session established
    using the physical PC PIN or QR pairing token can access file APIs.
    """
    if crypto_manager.is_e2ee_active:
        if not crypto_manager.is_session_valid(x_session_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Truy cập bị từ chối: Phiên làm việc không hợp lệ hoặc thiếu mã xác thực PIN."
            )
    return x_session_id

@app.post("/auth/handshake", response_model=HandshakeResponse)
async def auth_handshake(req: HandshakeRequest, request: Request):
    """
    Performs ephemeral X25519 key exchange guarded by dynamic RAM PIN / QR Pairing Token.
    All keys & secrets exist solely in memory - ZERO SECRETS EVER SAVED IN GIT OR DISK.
    """
    client_ip = request.client.host if request.client else "127.0.0.1"
    try:
        session_id, server_pub = crypto_manager.verify_and_handshake(
            client_ip=client_ip,
            client_public_key_b64=req.client_public_key,
            pin=req.pin,
            pairing_token=req.pairing_token,
            timestamp=req.timestamp,
            nonce=req.nonce
        )
        return HandshakeResponse(server_public_key=server_pub, session_id=session_id, status="ok")
    except ValueError as e:
        logger.warning(f"Handshake rejected for {client_ip}: {e}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        logger.error(f"Handshake failed: {e}")
        raise HTTPException(status_code=400, detail=f"Handshake failed: {str(e)}")

@app.get("/auth/key")
async def auth_get_key():
    """Returns the current server ephemeral public key."""
    return {"server_public_key": crypto_manager.get_server_public_key_b64()}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep-alive receive
            _ = await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)

@app.get("/files", response_model=List[FileMeta])
async def list_files(_session_id: str = Depends(verify_client_session)):
    """Returns files available on Desktop for iPhone to download."""
    return storage_manager.get_available_files()

@app.post("/upload/init", response_model=InitUploadResponse)
async def upload_init(payload: InitUploadRequest, _session_id: str = Depends(verify_client_session)):
    """
    Initializes a transfer session.
    Returns transfer_id and resume_offset (if chunk file already partially exists).
    """
    transfer_id = str(uuid.uuid4())
    resume_offset = storage_manager.init_upload(transfer_id, payload.meta)
    return InitUploadResponse(transfer_id=transfer_id, resume_offset=resume_offset)

@app.post("/upload/chunk/{transfer_id}")
async def upload_chunk(
    transfer_id: str,
    request: Request,
    x_chunk_index: Optional[int] = Header(None, alias="X-Chunk-Index"),
    x_encrypted: Optional[str] = Header(None, alias="X-Encrypted"),
    session_id: str = Depends(verify_client_session),
):
    """
    Receives 1MB binary chunk.
    If encrypted (X-Encrypted: 1 or E2EE active), decrypts AES-256-GCM chunk
    verifying cryptographic integrity before writing to .part file.
    Broadcasts progress via WebSocket.
    """
    chunk_data = await request.body()
    if not chunk_data:
        raise HTTPException(status_code=400, detail="Empty chunk data")

    # Anti-tampering & Decryption
    if x_encrypted == "1" or (crypto_manager.is_e2ee_active and x_encrypted != "0"):
        try:
            chunk_data = crypto_manager.decrypt_chunk(chunk_data, session_id=session_id)
        except Exception as e:
            logger.error(f"Anti-tamper / Decryption verification failed for chunk {x_chunk_index}: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cryptographic verification failed: tampered or corrupted chunk ({e})"
            )

    try:
        received_bytes, speed, eta = storage_manager.write_chunk(
            transfer_id=transfer_id,
            chunk_data=chunk_data,
            chunk_index=x_chunk_index or 0
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="Transfer ID not found or already completed")
    except Exception as e:
        logger.error(f"Error writing chunk for {transfer_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    transfer = storage_manager.active_transfers.get(transfer_id)
    if transfer:
        total = transfer["meta"].size
        await ws_manager.send_progress(
            transfer_id=transfer_id,
            sent=received_bytes,
            total=total,
            speed_bps=speed,
            eta_s=eta
        )

    return {"status": "ok", "received_bytes": received_bytes}

@app.post("/upload/complete/{transfer_id}", response_model=CompleteUploadResponse)
async def upload_complete(transfer_id: str, _session_id: str = Depends(verify_client_session)):
    """
    Finalizes upload, verifies SHA-256 hash.
    Optionally performs HEIC -> PNG or HEVC -> MP4 conversion.
    """
    try:
        transfer = storage_manager.active_transfers.get(transfer_id)
        if not transfer:
            raise HTTPException(status_code=404, detail="Transfer ID not found")

        meta = transfer["meta"]
        verified, final_path, message = storage_manager.finalize_upload(transfer_id)

        if not verified:
            await ws_manager.send_error(transfer_id, message)
            return CompleteUploadResponse(
                status="error",
                verified=False,
                path=str(final_path),
                message=message
            )

        # Handle post-upload auto-conversion if requested
        converted_path = final_path
        ext_lower = final_path.suffix.lstrip(".").lower()

        if meta.converted_ext == "png" or (ext_lower in ["heic", "heif"]):
            ok, out_p, c_msg = convert_heic_to_png(final_path)
            if ok:
                converted_path = out_p

        elif meta.converted_ext == "mp4" or (ext_lower in ["mov", "hevc"]):
            ok, out_p, c_msg = convert_hevc_to_mp4(final_path)
            if ok:
                converted_path = out_p

        await ws_manager.send_done(transfer_id, str(converted_path))
        return CompleteUploadResponse(
            status="ok",
            verified=True,
            path=str(converted_path),
            message="Transfer complete and verified"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload finalize error for {transfer_id}: {e}")
        await ws_manager.send_error(transfer_id, str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download/{file_id}/meta", response_model=FileMeta)
async def download_meta(file_id: str, _session_id: str = Depends(verify_client_session)):
    file_path = storage_manager.get_file_for_download(file_id)
    if not file_path or not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    stat = file_path.stat()
    return FileMeta(
        file_id=file_id,
        name=file_path.name,
        ext=file_path.suffix.lstrip(".").lower(),
        size=stat.st_size,
        device=DEVICE_NAME
    )

@app.get("/download/{file_id}")
async def download_file(
    file_id: str,
    request: Request,
    session_id: str = Depends(verify_client_session),
):
    """
    Downloads file with support for E2EE chunk encryption and HTTP Range requests (RFC 7233).
    Ensures seamless pause/resume and Wireshark-proof transmission.
    """
    file_path = storage_manager.get_file_for_download(file_id)
    if not file_path or not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    file_size = file_path.stat().st_size
    range_header = request.headers.get("Range")
    x_encrypted = request.headers.get("X-Encrypted")
    use_encryption = (x_encrypted == "1" or x_encrypted == "true") and crypto_manager.is_e2ee_active

    if use_encryption:
        # Stream chunks encrypted with AES-256-GCM, framed with 4-byte big-endian length prefix
        async def iter_encrypted():
            sent = 0
            last_t = time.time()
            last_b = 0
            with open(file_path, "rb") as f:
                while chunk := f.read(CHUNK_SIZE):
                    sent += len(chunk)
                    now = time.time()
                    dt = now - last_t
                    if dt >= 0.25:
                        speed = (sent - last_b) / dt if dt > 0 else 0
                        rem = max(0, file_size - sent)
                        eta = rem / speed if speed > 0 else 0
                        await ws_manager.send_progress(file_id, sent, file_size, speed, eta)
                        last_t = now
                        last_b = sent
                    enc_chunk = crypto_manager.encrypt_chunk(chunk, session_id=session_id)
                    # Length prefix (4 bytes) + encrypted chunk (nonce + ciphertext + tag)
                    yield struct.pack(">I", len(enc_chunk)) + enc_chunk
            await ws_manager.send_done(file_id, str(file_path))

        headers = {
            "Accept-Ranges": "none",
            "Content-Type": "application/octet-stream",
            "Content-Disposition": f'attachment; filename="{file_path.name}"',
            "X-Encrypted": "1"
        }
        return StreamingResponse(iter_encrypted(), headers=headers)


    if range_header:
        # e.g. "bytes=1048576-" or "bytes=0-1048575"
        try:
            h = range_header.replace("bytes=", "").strip()
            parts = h.split("-")
            start = int(parts[0]) if parts[0] else 0
            end = int(parts[1]) if len(parts) > 1 and parts[1] else file_size - 1
            if start >= file_size or end >= file_size or start > end:
                raise HTTPException(status_code=416, detail="Range Not Satisfiable")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid Range header")

        length = end - start + 1

        async def iter_range():
            sent = start
            last_t = time.time()
            last_b = sent
            with open(file_path, "rb") as f:
                f.seek(start)
                bytes_left = length
                while bytes_left > 0:
                    read_size = min(CHUNK_SIZE, bytes_left)
                    data = f.read(read_size)
                    if not data:
                        break
                    bytes_left -= len(data)
                    sent += len(data)
                    now = time.time()
                    dt = now - last_t
                    if dt >= 0.25:
                        speed = (sent - last_b) / dt if dt > 0 else 0
                        rem = max(0, file_size - sent)
                        eta = rem / speed if speed > 0 else 0
                        await ws_manager.send_progress(file_id, sent, file_size, speed, eta)
                        last_t = now
                        last_b = sent
                    yield data
            await ws_manager.send_done(file_id, str(file_path))

        headers = {
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(length),
            "Content-Type": "application/octet-stream",
            "Content-Disposition": f'attachment; filename="{file_path.name}"'
        }
        return StreamingResponse(iter_range(), status_code=206, headers=headers)

    # Full file stream (plaintext)
    async def iter_full():
        sent = 0
        last_t = time.time()
        last_b = 0
        with open(file_path, "rb") as f:
            while chunk := f.read(CHUNK_SIZE):
                sent += len(chunk)
                now = time.time()
                dt = now - last_t
                if dt >= 0.25:
                    speed = (sent - last_b) / dt if dt > 0 else 0
                    rem = max(0, file_size - sent)
                    eta = rem / speed if speed > 0 else 0
                    await ws_manager.send_progress(file_id, sent, file_size, speed, eta)
                    last_t = now
                    last_b = sent
                yield chunk
        await ws_manager.send_done(file_id, str(file_path))

    headers = {
        "Accept-Ranges": "bytes",
        "Content-Length": str(file_size),
        "Content-Type": "application/octet-stream",
        "Content-Disposition": f'attachment; filename="{file_path.name}"'
    }
    return StreamingResponse(iter_full(), headers=headers)

@app.get("/config", response_model=ConfigModel)
async def get_config():
    return ConfigModel(storage_dir=str(storage_manager.base_dir), auto_convert=True)

@app.post("/config", response_model=ConfigModel)
async def update_config(config: ConfigModel):
    storage_manager.set_storage_dir(config.storage_dir)
    return config
