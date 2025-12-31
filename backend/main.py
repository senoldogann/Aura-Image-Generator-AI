import os
import time
import json
import asyncio
import zipfile
import io

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from fastapi.concurrency import run_in_threadpool

# Internal modules
from config import settings
from schemas import (
    GenerateRequest, GenerateResponse, 
    UpscaleRequest, UpscaleResponse, 
    WatermarkRequest, WatermarkResponse
)
from utils import enhance_prompt, auto_detect_aspect_ratio, detect_prompt_category
from sd_engine import StableDiffusionEngine

# 1. Initialize FastAPI App
app = FastAPI(title=settings.API_TITLE, version=settings.API_VERSION)

# 2. CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Static Files
app.mount("/artifacts", StaticFiles(directory=settings.ARTIFACTS_DIR), name="artifacts")

# 4. Engine & Concurrency
_sd_engine = None
GPU_SEMAPHORE = asyncio.Semaphore(settings.MAX_QUEUE_SIZE)

def get_engine() -> StableDiffusionEngine:
    global _sd_engine
    if _sd_engine is None:
        _sd_engine = StableDiffusionEngine()
    return _sd_engine

# --- Background Ephemeral Cleaner ---
async def ephemeral_cleaner_task():
    """Background task to delete files older than TTL."""
    print(f"[CleanUp] ephemeral_cleaner_task started (TTL: {settings.EPHEMERAL_TTL}s).")
    while True:
        try:
            now = time.time()
            count = 0
            for f in os.listdir(settings.ARTIFACTS_DIR):
                file_path = os.path.join(settings.ARTIFACTS_DIR, f)
                if os.path.isfile(file_path):
                    if now - os.path.getmtime(file_path) > settings.EPHEMERAL_TTL:
                        try:
                            os.remove(file_path)
                            count += 1
                        except Exception as e:
                            print(f"[CleanUp] Failed to remove {f}: {e}")
            if count > 0:
                print(f"[CleanUp] Removed {count} expired files.")
        except Exception as e:
            print(f"[CleanUp] Error during scan: {e}")
        
        await asyncio.sleep(600) # Run every 10 minutes

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(ephemeral_cleaner_task())

# --- Routes ---

@app.get("/health")
async def health():
    return {"status": "ok", "version": settings.API_VERSION}

@app.get("/images")
async def list_images():
    """List all generated images in artifacts directory."""
    try:
        files = []
        for f in os.listdir(settings.ARTIFACTS_DIR):
            if f.endswith(".png") and not f.endswith("_upscaled.png"):
                file_path = os.path.join(settings.ARTIFACTS_DIR, f)
                mtime = os.path.getmtime(file_path)
                files.append({
                    "filename": f,
                    "url": f"/artifacts/{f}",
                    "created_at": mtime
                })
        files.sort(key=lambda x: x["created_at"], reverse=True)
        return {"images": files}
    except Exception as e:
        print(f"[API] Error listing images: {e}")
        return {"images": [], "error": str(e)}

@app.get("/export-zip")
async def export_zip():
    """Export all generated images as a ZIP file."""
    try:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for f in os.listdir(settings.ARTIFACTS_DIR):
                if f.endswith(".png"):
                    file_path = os.path.join(settings.ARTIFACTS_DIR, f)
                    zip_file.write(file_path, arcname=f)
        
        zip_buffer.seek(0)
        filename = f"aura_history_{int(time.time())}.zip"
        
        return StreamingResponse(
            zip_buffer, 
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        print(f"[API] ZIP Export error: {e}")
        return {"error": str(e)}

@app.get("/progress")
async def progress_stream():
    """Stream live progress from SD Engine via SSE."""
    async def event_generator():
        engine = get_engine()
        while True:
            if engine.total_steps > 0:
                percent = int((engine.current_step / engine.total_steps) * 100)
                data = json.dumps({
                    "step": engine.current_step,
                    "total": engine.total_steps,
                    "percentage": percent
                })
                yield f"data: {data}\n\n"
            else:
                 # Sending Keep-Alive/Idle state
                 yield f"data: {json.dumps({'percentage': 0})}\n\n"
            
            await asyncio.sleep(0.5)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@app.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    print(f"[API] Generating: {request.prompt} (Model: {request.model_key})")
    
    engine = get_engine()
    
    # Smart Logic
    enhanced_prompt = enhance_prompt(request.prompt, request.model_key)
    print(f"[API] Enhanced: {enhanced_prompt[:100]}...")
    
    # Aspect Ratio Logic
    final_ratio = auto_detect_aspect_ratio(request.prompt) if request.aspect_ratio == "auto" else request.aspect_ratio

    try:
        timestamp = int(time.time())
        image_filename = f"generated_{timestamp}.png"
        output_path = os.path.join(settings.ARTIFACTS_DIR, image_filename)

        if GPU_SEMAPHORE.locked():
            print(f"[API] Queue busy. Waiting...")

        async with GPU_SEMAPHORE:
            success = await run_in_threadpool(
                engine.generate_and_save,
                prompt=enhanced_prompt,
                model_key=request.model_key,
                output_path=output_path,
                aspect_ratio=final_ratio,
                negative_prompt=request.negative_prompt,
                num_inference_steps=30,
                guidance_scale=9.0
            )
        
        if success and os.path.exists(output_path):
            final_url = f"/artifacts/{image_filename}?t={timestamp}"
            
            # --- Auto-Upscale Logic ---
            if request.auto_upscale:
                print(f"[API] Auto-Upscaling result...")
                try:
                    # Re-acquire lock for upscale (or hold it? holding is better but complex with run_in_threadpool separate calls)
                    # Since we are already in the route, the semaphore is released after the block above.
                    # We need to re-acquire.
                    
                    async with GPU_SEMAPHORE:
                        upscaled_path = await run_in_threadpool(
                            engine.upscale_image,
                            image_path=output_path,
                            prompt=request.prompt
                        )
                    
                    if upscaled_path:
                        upscaled_filename = os.path.basename(upscaled_path)
                        final_url = f"/artifacts/{upscaled_filename}?t={int(time.time())}"
                        print(f"[API] Auto-Upscale Successful: {final_url}")
                except Exception as ue:
                    print(f"[API] Auto-Upscale Failed (Soft Error): {ue}")
                    # We continue with the original image if upscale fails
            
            return GenerateResponse(success=True, image_url=final_url)
        return GenerateResponse(success=False, error="Engine failed to save image.")
            
    except Exception as e:
        print(f"[API] Generation Error: {e}")
        return GenerateResponse(success=False, error=str(e))

@app.post("/upscale", response_model=UpscaleResponse)
async def upscale(request: UpscaleRequest):
    # Sanitize Path logic could be moved to utils, but keeping here for simplicity
    clean_path = request.image_path.replace(f"http://{settings.HOST}:{settings.PORT}/", "").split("?")[0].lstrip("/")
    
    # Security: Ensure we only access artifacts
    if not clean_path.startswith("artifacts/"):
         return UpscaleResponse(success=False, error="Invalid file path")
         
    full_path = os.path.join(settings.BASE_DIR, clean_path)
    
    if not os.path.exists(full_path):
         return UpscaleResponse(success=False, error="File not found")

    engine = get_engine()
    
    try:
        async with GPU_SEMAPHORE:
            output_path = await run_in_threadpool(
                engine.upscale_image,
                image_path=full_path,
                prompt=request.prompt
            )
        
        if output_path:
            filename = os.path.basename(output_path)
            return UpscaleResponse(success=True, upscaled_image_url=f"/artifacts/{filename}?t={int(time.time())}")
        return UpscaleResponse(success=False, error="Upscaling failed")
    except Exception as e:
        print(f"[API] Upscale Error: {e}")
        return UpscaleResponse(success=False, error=str(e))

@app.post("/watermark", response_model=WatermarkResponse)
async def add_watermark(request: WatermarkRequest):
    clean_path = request.image_path.replace(f"http://{settings.HOST}:{settings.PORT}/", "").split("?")[0].lstrip("/")
    full_path = os.path.join(settings.BASE_DIR, clean_path)
    
    if not os.path.exists(full_path):
        return WatermarkResponse(success=False, error="Image not found")
    
    engine = get_engine()
    try:
        output_path = await run_in_threadpool(
            engine.add_watermark,
            image_path=full_path,
            text=request.text
        )
        if output_path:
            filename = os.path.basename(output_path)
            return WatermarkResponse(success=True, watermarked_url=f"/artifacts/{filename}?t={int(time.time())}")
        return WatermarkResponse(success=False, error="Watermark failed")
    except Exception as e:
        return WatermarkResponse(success=False, error=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=True)
