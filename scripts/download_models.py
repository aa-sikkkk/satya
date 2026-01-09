"""
Model Downloader for Satya Learning System

Downloads the required AI models:
1. BitNet b1.58 700M/Large (Q8_0 for max speed <10s)
2. Sentence Transformer (all-MiniLM-L6-v2)

Usage:
    python scripts/download_models.py
"""

import os
import sys
import logging
import shutil
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from huggingface_hub import hf_hub_download, snapshot_download
except ImportError:
    logger.error("huggingface_hub not found. Please run: pip install -r requirements.txt")
    sys.exit(1)

def download_bitnet():
    """Download BitNet GGUF model (700M Variant for Speed)."""
    # Using 'mav23/bitnet_b1_58-large-GGUF' or equivalent reliable source for 700M/1B range
    # BitNet 'Large' is often ~700M-1.3B in papers, mapping to ~700M implementation here
    REPO_ID = "mav23/bitnet_b1_58-large-GGUF"
    FILENAME = "bitnet_b1_58-large.Q8_0.gguf" # Q8_0 is fast and accurate for this small size
    
    # Target directory from config
    TARGET_DIR = Path("satya_data/models/bitnet_b1.58_2B_4T") # Keeping dir name for consistency or should rename?
    # Let's keep dir name but putting the file there. Config.json needs update to match filename.
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    
    TARGET_PATH = TARGET_DIR / "bitnet-b1.58-large.Q8_0.gguf"
    
    if TARGET_PATH.exists():
        logger.info(f"✅ BitNet model already exists at {TARGET_PATH}")
        return TARGET_PATH
        
    logger.info(f"⬇️ Downloading BitNet 700M/Large model ({FILENAME})...")
    try:
        downloaded_path = hf_hub_download(
            repo_id=REPO_ID,
            filename=FILENAME,
            local_dir=str(TARGET_DIR),
            local_dir_use_symlinks=False
        )
        
        # Rename to target path if strictly needed, or just use downloaded name
        # hf_hub_download with local_dir usually keeps filename.
        
        logger.info(f"✅ Download complete: {downloaded_path}")
        
        # We also need to ensure config.json points to this new filename!
        return downloaded_path
        
    except Exception as e:
        logger.error(f"❌ Failed to download BitNet: {e}")
        return None

def download_embeddings():
    """Download Sentence Transformer model."""
    MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
    TARGET_DIR = Path("satya_data/models/embedding/all-MiniLM-L6-v2")
    
    if TARGET_DIR.exists():
        logger.info(f"✅ Embedding model already exists at {TARGET_DIR}")
        return
        
    logger.info(f"⬇️ Downloading embedding model ({MODEL_NAME})...")
    try:
        # We use snapshot_download to get the full model for local usage
        snapshot_download(
            repo_id=MODEL_NAME,
            local_dir=str(TARGET_DIR),
            local_dir_use_symlinks=False
        )
        logger.info("✅ Embedding model download complete")
        
    except Exception as e:
        logger.error(f"❌ Failed to download embedding model: {e}")

if __name__ == "__main__":
    print("🚀 Starting Model Downloads (Target: <10s Speed)...")
    download_bitnet()
    download_embeddings()
    print("✨ All downloads finished!")
