from typing import List

# --- Smart Prompt Enhancement System ---
CATEGORY_ENHANCERS = {
    "portrait": {
        "keywords": ["person", "portrait", "man", "woman", "face", "headshot", "model", "human", "girl", "boy", "lady", "gentleman", "selfie", "people"],
        "enhancers": "realistic skin texture, visible pores, asymmetric facial features, subsurface scattering, natural skin imperfections, detailed iris texture, realistic eye reflections, micro expressions"
    },
    "landscape": {
        "keywords": ["landscape", "nature", "mountain", "forest", "ocean", "sunset", "sunrise", "beach", "sky", "clouds", "valley", "river", "lake"],
        "enhancers": "atmospheric perspective, volumetric lighting, god rays, natural color grading, golden hour, dynamic range, depth of field"
    },
    "architecture": {
        "keywords": ["building", "architecture", "interior", "room", "house", "city", "street", "urban", "skyscraper", "cathedral", "temple"],
        "enhancers": "architectural photography, clean lines, ambient occlusion, realistic materials, perspective correction, structural details"
    },
    "product": {
        "keywords": ["product", "bottle", "watch", "phone", "jewelry", "car", "vehicle", "gadget", "electronics", "fashion", "clothing"],
        "enhancers": "studio lighting, soft shadows, commercial photography, clean background, reflective surfaces, product showcase"
    },
    "fantasy": {
        "keywords": ["dragon", "magic", "fantasy", "sci-fi", "alien", "wizard", "fairy", "mythical", "creature", "monster", "superhero", "robot"],
        "enhancers": "concept art, digital painting, dramatic lighting, cinematic composition, epic scale, otherworldly atmosphere"
    },
    "food": {
        "keywords": ["food", "dish", "meal", "cuisine", "restaurant", "cooking", "baking", "dessert", "drink", "coffee", "burger", "pizza", "sushi", "cake", "ice cream"],
        "enhancers": "food photography, appetizing, warm lighting, shallow depth of field, steam effects, fresh ingredients"
    }
}

UNIVERSAL_QUALITY = "masterpiece, best quality, highly detailed, sharp focus, professional photography, 8k uhd"

# --- Auto Aspect Ratio Detection ---
ASPECT_RATIO_RULES = {
    "portrait": "3:4",      # Portrait/headshot - vertical
    "landscape": "16:9",    # Wide scenic views
    "architecture": "16:9", # Architectural shots often wide
    "product": "1:1",       # Product photography - square
    "food": "1:1",          # Food photography - square (Instagram style)
    "fantasy": "16:9",      # Epic cinematic scenes
}

def detect_prompt_category(prompt: str) -> List[str]:
    """Detect categories from prompt keywords."""
    prompt_lower = prompt.lower()
    detected = []
    for category, data in CATEGORY_ENHANCERS.items():
        for keyword in data["keywords"]:
            if keyword in prompt_lower:
                detected.append(category)
                break
    return detected if detected else ["general"]

def enhance_prompt(prompt: str, model_key: str) -> str:
    """Apply smart category-based prompt enhancement."""
    categories = detect_prompt_category(prompt)
    
    # Base enhancement based on model
    if model_key == "classic":
        base = f"{prompt}, {UNIVERSAL_QUALITY}, celestial, dreamy, artstation"
    else:
        base = f"{prompt}, {UNIVERSAL_QUALITY}, raw photo, dslr, soft lighting, film grain, Fujifilm XT4"
    
    # Add category-specific enhancers
    category_terms = []
    for cat in categories:
        if cat in CATEGORY_ENHANCERS:
            category_terms.append(CATEGORY_ENHANCERS[cat]["enhancers"])
    
    if category_terms:
        return f"{base}, {', '.join(category_terms)}"
    return base

def auto_detect_aspect_ratio(prompt: str) -> str:
    """Auto-detect optimal aspect ratio based on prompt content."""
    categories = detect_prompt_category(prompt)
    
    # Priority order for aspect ratio selection
    for cat in categories:
        if cat in ASPECT_RATIO_RULES:
            return ASPECT_RATIO_RULES[cat]
    
    # Default to square if no specific category
    return "1:1"
