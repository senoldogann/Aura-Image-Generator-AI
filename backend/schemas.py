from pydantic import BaseModel
from typing import Optional

class GenerateRequest(BaseModel):
    prompt: str
    model_key: str = "realistic"
    aspect_ratio: str = "1:1"
    negative_prompt: Optional[str] = None
    auto_upscale: bool = False

class GenerateResponse(BaseModel):
    success: bool
    image_url: Optional[str] = None
    error: Optional[str] = None

class UpscaleRequest(BaseModel):
    image_path: str
    prompt: Optional[str] = ""

class UpscaleResponse(BaseModel):
    success: bool
    upscaled_image_url: Optional[str] = None
    error: Optional[str] = None

class WatermarkRequest(BaseModel):
    image_path: str
    text: str = "AURA"

class WatermarkResponse(BaseModel):
    success: bool
    watermarked_url: Optional[str] = None
    error: Optional[str] = None
