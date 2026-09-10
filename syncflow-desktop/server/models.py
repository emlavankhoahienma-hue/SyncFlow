from typing import Optional
from pydantic import BaseModel, Field
import uuid

class FileMeta(BaseModel):
    file_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    ext: str
    mime: str = "application/octet-stream"
    size: int
    sha256: Optional[str] = None
    converted_ext: Optional[str] = None
    device: Optional[str] = "Desktop"

class InitUploadRequest(BaseModel):
    meta: FileMeta

class InitUploadResponse(BaseModel):
    transfer_id: str
    resume_offset: int

class CompleteUploadResponse(BaseModel):
    status: str
    verified: bool
    path: str
    message: Optional[str] = None

class TransferProgress(BaseModel):
    type: str = "progress"
    transfer_id: str
    sent: int
    total: int
    speed_bps: float
    eta_s: float

class HealthResponse(BaseModel):
    device_name: str
    version: str = "1.0.0"
    status: str = "ok"

class ConfigModel(BaseModel):
    storage_dir: str
    auto_convert: bool = True

class HandshakeRequest(BaseModel):
    client_public_key: str  # Base64 encoded 32-byte raw public key
    pin: Optional[str] = None  # 6-digit pairing PIN displayed on PC screen
    pairing_token: Optional[str] = None  # 128-bit pairing token embedded in QR
    timestamp: Optional[int] = None  # Unix timestamp in seconds (anti-replay)
    nonce: Optional[str] = None  # Unique random request nonce (anti-replay)

class HandshakeResponse(BaseModel):
    server_public_key: str  # Base64 encoded 32-byte raw public key
    session_id: str  # Authenticated session token for X-Session-ID
    status: str = "ok"

