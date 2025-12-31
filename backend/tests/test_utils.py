import pytest
from utils import detect_prompt_category, enhance_prompt, auto_detect_aspect_ratio

def test_detect_prompt_category():
    # Test single category
    assert "portrait" in detect_prompt_category("a photo of a man")
    assert "food" in detect_prompt_category("delicious burger")
    
    # Test multiple categories (if applicable, logic returns list)
    cats = detect_prompt_category("a fantasy dragon eating pizza")
    assert "fantasy" in cats
    # "pizza" might not be in keywords, let's check utils.py... 
    # keywords["food"]: ["food", "dish", "meal", ... "dessert", "drink"] -> pizza is NOT there.
    # So it should just be fantasy.
    
    # Test fallback
    assert detect_prompt_category("unknown content") == ["general"]

def test_auto_detect_aspect_ratio():
    # Portrait keywords -> 3:4
    assert auto_detect_aspect_ratio("portrait of a lady") == "3:4"
    
    # Landscape keywords -> 16:9
    assert auto_detect_aspect_ratio("beautiful sunset over mountains") == "16:9"
    
    # Default -> 1:1
    assert auto_detect_aspect_ratio("random noise") == "1:1"

def test_enhance_prompt():
    # Classic Model
    classic_res = enhance_prompt("a cat", "classic")
    assert "celestial" in classic_res
    assert "artstation" in classic_res
    
    # Realistic Model
    real_res = enhance_prompt("a cat", "realistic")
    assert "raw photo" in real_res
    assert "Fujifilm XT4" in real_res
    
    # Category Enhancement
    # "forest" -> landscape -> "atmospheric perspective"
    cat_res = enhance_prompt("dark forest", "realistic")
    assert "atmospheric perspective" in cat_res
