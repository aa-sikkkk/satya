"""
Offline Model Loader for Satya RAG System

This script loads models from the local bundle for offline use.
"""

import sys
from pathlib import Path

# Model bundle lives in satya_data/models/ relative to the project root
models_dir = Path(__file__).resolve().parents[1] / "satya_data" / "models"


def load_phi_model():
    """Load Phi 1.5 model from local bundle."""
    try:
        from transformers import AutoModel, AutoTokenizer

        phi_dir = models_dir / "phi15"

        if phi_dir.exists():
            print("Loading Phi 1.5 model from local bundle...")
            tokenizer = AutoTokenizer.from_pretrained(str(phi_dir))
            model = AutoModel.from_pretrained(str(phi_dir))
            print("✅ Phi 1.5 model loaded successfully")
            return tokenizer, model
        else:
            print("❌ Phi 1.5 model not found in local bundle")
            return None, None
    except Exception as e:
        print(f"❌ Failed to load Phi 1.5 model: {e}")
        return None, None


def load_clip_model():
    """Load CLIP model (uses torch hub cache)."""
    try:
        import clip

        print("Loading CLIP model from cache...")
        model, preprocess = clip.load("ViT-B/32", device="cpu")
        print("✅ CLIP model loaded successfully")
        return model, preprocess
    except Exception as e:
        print(f"❌ Failed to load CLIP model: {e}")
        return None, None


def test_offline_loading():
    """Test loading all models offline."""
    print("=== Testing Offline Model Loading ===")

    # Load Phi 1.5
    phi_tokenizer, phi_model = load_phi_model()

    # Load CLIP
    clip_model, clip_preprocess = load_clip_model()

    # Summary
    print("\n=== Loading Summary ===")
    if phi_model:
        print("✅ Phi 1.5: Ready for text embeddings")
    else:
        print("❌ Phi 1.5: Failed to load")

    if clip_model:
        print("✅ CLIP: Ready for image embeddings")
    else:
        print("❌ CLIP: Failed to load")

    return phi_model is not None and clip_model is not None


if __name__ == "__main__":
    success = test_offline_loading()

    if success:
        print("\n🎉 All models loaded successfully!")
        print("📦 Ready for offline RAG system!")
    else:
        print("\n❌ Some models failed to load")
        print("🔧 Check model files and dependencies")

    sys.exit(0 if success else 1)
