import os
import torch
from diffusers import StableDiffusionPipeline, DPMSolverMultistepScheduler
from PIL import Image
from dotenv import load_dotenv
import time
import gc
from typing import Optional, Dict, Tuple
import requests

class StableDiffusionEngine:
    """
    Refined Stable Diffusion engine focused exclusively on Classic (v1.5)
    for maximum stability and artistic quality on Mac.
    """
    
    MODELS = {
        "classic": "runwayml/stable-diffusion-v1-5",
        "realistic": "SG161222/Realistic_Vision_V5.1_noVAE"
    }

    # Presets for aspect ratios (Targeting ~262k pixels for SD1.5, ~1M for SDXL)
    RATIOS = {
        "1:1": (1.0, 1.0),
        "16:9": (1.33, 0.75),
        "9:16": (0.75, 1.33),
        "4:3": (1.15, 0.86),
        "3:4": (0.86, 1.15),
    }
    
    def __init__(self):
        self.device = self._get_device()
        self.pipe = None
        self.current_model_id = None
        self.current_step = 0
        self.total_steps = 0
        print(f"[SD Engine] Initialized on device: {self.device}")

    def _progress_callback(self, step: int, timestep: int, latents: torch.FloatTensor):
        self.current_step = step
        # print(f"Step: {step}/{self.total_steps}") # Debug

    def _check_and_download_weights(self, model_name: str, url: str) -> str:
        weights_dir = os.path.join(os.path.dirname(__file__), "weights")
        os.makedirs(weights_dir, exist_ok=True)
        
        file_path = os.path.join(weights_dir, f"{model_name}.pth")
        
        if not os.path.exists(file_path):
            print(f"[SD Engine] Downloading {model_name} weights to {file_path}...")
            try:
                response = requests.get(url, stream=True)
                response.raise_for_status()
                with open(file_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                print("[SD Engine] Download complete.")
            except Exception as e:
                print(f"[SD Engine] Failed to download weights: {e}")
                return None
                
        return file_path

    def _get_device(self) -> str:
        if torch.backends.mps.is_available():
            return "mps"
        elif torch.cuda.is_available():
            return "cuda"
        return "cpu"

    def add_watermark(self, image_path: str, text: str = "AURA") -> str:
        """Add semi-transparent watermark to bottom-right corner."""
        from PIL import Image, ImageDraw, ImageFont
        
        try:
            img = Image.open(image_path).convert("RGBA")
            
            # Create watermark layer
            watermark = Image.new("RGBA", img.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(watermark)
            
            # Try to use a nice font, fallback to default
            font_size = max(20, img.width // 25)
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
            except:
                font = ImageFont.load_default()
            
            # Calculate position (bottom-right with padding)
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            padding = 20
            x = img.width - text_width - padding
            y = img.height - text_height - padding
            
            # Draw text with semi-transparency
            draw.text((x, y), text, font=font, fill=(255, 255, 255, 100))
            
            # Composite and save
            watermarked = Image.alpha_composite(img, watermark).convert("RGB")
            output_path = image_path.replace(".png", "_watermarked.png")
            watermarked.save(output_path)
            
            print(f"[SD Engine] Watermark added: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"[SD Engine] Watermark error: {e}")
            return image_path  # Return original if watermark fails

    # ... (Keep existing methods like _get_dimensions, load_model, generate) ...

    # We need to target the upscale_image method below, so I'll skip to that part in a second replacement call if needed, 
    # but since this tool replaces a block, I should target specific blocks. 
    # Let me cancel this and do it in two focused edits.
    
    def _get_dimensions(self, ratio_key: str) -> Tuple[int, int]:
        """Calculate dimensions for Classic v1.5 (Optimized for 512px)."""
        base_size = 512
        rx, ry = self.RATIOS.get(ratio_key, (1.0, 1.0))
        
        if rx >= 1.0:
            w = base_size
            h = int(base_size / rx)
        else:
            h = base_size
            w = int(base_size * rx)
            
        w = (w // 8) * 8
        h = (h // 8) * 8
        return w, h

    def load_model(self, model_key: str = "realistic"):
        """Load or switch model."""
        target_model_id = self.MODELS.get(model_key, self.MODELS["realistic"])
        
        if self.pipe is not None:
            return
        
        # Aggressive memory cleanup (removed as we no longer switch models)
        
        print(f"[SD Engine] Loading Aura Classic: {target_model_id}")
        start = time.time()
        
        dtype = torch.float32 if self.device == "mps" else torch.float16
        
        try:
            self.pipe = StableDiffusionPipeline.from_pretrained(
                target_model_id,
                dtype=dtype, # Fixed deprecation warning (torch_dtype -> dtype)
                variant="fp16" if self.device != "mps" else None,
                use_safetensors=True
            )
            
            # High-quality scheduler for Classic - explicitly configured to avoid 'final_sigmas_type' error
            self.pipe.scheduler = DPMSolverMultistepScheduler.from_config(
                self.pipe.scheduler.config,
                use_karras_sigmas=True,
                algorithm_type="sde-dpmsolver++"
            )
            
            self.pipe = self.pipe.to(self.device)
            self.pipe.enable_attention_slicing()
            # VAE slicing removed as it's not always available and not strictly needed for classic
            
            self.current_model_id = target_model_id
            print(f"[SD Engine] Classic loaded in {time.time() - start:.1f}s")
        except Exception as e:
            print(f"[SD Engine] Failed to load Classic: {e}")
            raise

    def generate(
        self,
        prompt: str,
        model_key: str = "realistic",
        aspect_ratio: str = "1:1",
        negative_prompt: str = "blur, blurry, out of focus, hazy, soft edges, distorted, low quality, grainy, digital noise, watermark, lowres, ugly, deformed",
        num_inference_steps: int = 30, # Increased for maximum detail as requested
        guidance_scale: float = 9.0,   # Increased for higher contrast and sharpness
        seed: Optional[int] = None
    ) -> Image.Image:
        
        self.load_model(model_key)
        width, height = self._get_dimensions(aspect_ratio)
        
        print(f"[SD Engine] Generating Ultimate Quality ({width}x{height}, steps={num_inference_steps})")
        
        generator = None
        if seed is not None:
            generator = torch.Generator(device=self.device).manual_seed(seed)
        
        # Performance tip: Ensure prompt is stripped and lowercase
        clean_prompt = prompt.strip()

        # Initialize progress tracking
        self.total_steps = num_inference_steps
        self.current_step = 0

        with torch.inference_mode():
            result = self.pipe(
                prompt=clean_prompt,
                negative_prompt=negative_prompt,
                width=width,
                height=height,
                num_inference_steps=num_inference_steps,
                guidance_scale=guidance_scale,
                generator=generator,
                callback=self._progress_callback,
                callback_steps=1
            )
            
        return result.images[0]


    def generate_and_save(self, prompt: str, output_path: str, **kwargs) -> bool:
        try:
            image = self.generate(prompt, **kwargs)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            image.save(output_path)
            print(f"[SD Engine] Saved to {output_path}")
            return True
        except Exception as e:
            print(f"[SD Engine] Error: {e}")
            return False

    def upscale_image(self, image_path: str, prompt: str) -> Optional[str]:
        """
        Upscale image 4x using RealESRGAN (GAN-based).
        Extremely fast (seconds) and sharp compared to Latent Upscalers.
        """
        print(f"[SD Engine] Starting Upscale Process for {image_path}")
        
        # 1. Unload SD Model to free VRAM
        if self.pipe:
            print("[SD Engine] Unloading Text2Image model...")
            del self.pipe
            self.pipe = None
            gc.collect()
            if self.device == "mps":
                if hasattr(torch.mps, 'empty_cache'):
                     torch.mps.empty_cache()

        # 2. Load RealESRGAN
        try:
            from basicsr.archs.rrdbnet_arch import RRDBNet
            from realesrgan import RealESRGANer
            import numpy as np
        except ImportError as e:
            print(f"[SD Engine] RealESRGAN libraries not found. Error: {e}")
            print("Please run: pip install realesrgan basicsr")
            return None
        except Exception as e:
             print(f"[SD Engine] Unexpected dependency error: {e}")
             return None

        try:
            # 2. Check/Download Weights
            model_name = 'RealESRGAN_x4plus'
            weight_url = 'https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth'
            model_path = self._check_and_download_weights(model_name, weight_url)
            
            if not model_path:
                print("[SD Engine] Error: Could not find or download model weights.")
                return None

            model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64, num_block=23, num_grow_ch=32, scale=4)
            
            upscaler = RealESRGANer(
                scale=4,
                model_path=model_path,
                model=model,
                tile=0, # 0 for no tile during testing
                tile_pad=10,
                pre_pad=0,
                half=False, # MPS doesn't support half well
                device='cpu' # Force CPU for safety
            )
            
            # 3. Process
            import cv2
            img = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
            if img is None:
                print(f"[SD Engine] Error reading image {image_path}")
                return None

            print("[SD Engine] Enhancing (RealESRGAN)...")
            
            # Fake Progress for UI
            self.current_step = 1
            self.total_steps = 3  # Updated for GFPGAN step
            self._progress_callback(1, 0, None)
            
            output, _ = upscaler.enhance(img, outscale=4)
            
            self.current_step = 2
            self._progress_callback(2, 0, None)
            
            # 5. GFPGAN Face Restoration (Optional but enabled by default for quality)
            try:
                from gfpgan import GFPGANer
                
                print("[SD Engine] Applying GFPGAN Face Restoration...")
                gfpgan_model_path = self._check_and_download_weights(
                    "GFPGANv1.4",
                    "https://github.com/TencentARC/GFPGAN/releases/download/v1.3.4/GFPGANv1.4.pth"
                )
                
                if gfpgan_model_path:
                    face_enhancer = GFPGANer(
                        model_path=gfpgan_model_path,
                        upscale=1,  # Don't upscale again, just enhance
                        arch='clean',
                        channel_multiplier=2,
                        bg_upsampler=None,
                        device='cpu'
                    )
                    
                    # GFPGAN expects BGR format from cv2
                    _, _, output = face_enhancer.enhance(
                        output,
                        has_aligned=False,
                        only_center_face=False,
                        paste_back=True
                    )
                    print("[SD Engine] Face restoration complete.")
                else:
                    print("[SD Engine] GFPGAN weights not available, skipping face restoration.")
                    
            except ImportError:
                print("[SD Engine] GFPGAN not installed, skipping face restoration.")
            except Exception as face_err:
                print(f"[SD Engine] GFPGAN error (non-fatal): {face_err}")
            
            # 6. Save
            save_path = image_path.replace(".png", "_upscaled.png")
            cv2.imwrite(save_path, output)
            
            self.current_step = 3
            self._progress_callback(3, 0, None)
            
            print(f"[SD Engine] Upscale saved to {save_path}")
            return save_path

        except Exception as e:
            print(f"[SD Engine] RealESRGAN Error: {e}")
            return None

_sd_engine = None

def get_sd_engine() -> StableDiffusionEngine:
    global _sd_engine
    if _sd_engine is None:
        _sd_engine = StableDiffusionEngine()
    return _sd_engine

