
import os
import sys
import logging
import time

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_model.model_utils.bitnet_handler import BitNetHandler

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(name)s - %(message)s')
logger = logging.getLogger("BitNetVerifier")

def verify_bitnet():
    print("🚀 Starting BitNet Verification...")
    
    # Path to model directory (parent of the .gguf file)
    base_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "satya_data", "models", "bitnet_b1.58_2B_4T")
    
    if not os.path.exists(base_dir):
        print(f"❌ Model directory not found: {base_dir}")
        return

    print(f"📂 Model Directory: {base_dir}")
    
    try:
        # Initialize Handler
        print("⚡ Initializing BitNetHandler...")
        handler = BitNetHandler(model_path=base_dir)
        
        # Load Model
        print("📥 Loading Model into Memory...")
        t0 = time.time()
        handler.load_model()
        print(f"✅ Model Loaded in {time.time() - t0:.2f}s")
        
        # Test Inference
        print("\n🧠 Testing Inference...")
        question = "What is photosynthesis?"
        context = "Photosynthesis is the process by which green plants and some other organisms use sunlight to synthesize foods from carbon dioxide and water. Photosynthesis in plants generally involves the green pigment chlorophyll and generates oxygen as a byproduct."
        
        print(f"   Q: {question}")
        print(f"   Context: (Provided {len(context)} chars)")
        
        t1 = time.time()
        answer, confidence = handler.get_answer(question, context, grade=10)
        t2 = time.time()
        
        print(f"\n✅ Answer: {answer}")
        print(f"📊 Confidence: {confidence}")
        print(f"⏱️ Generation Time: {t2 - t1:.2f}s")
        
        if len(answer) > 10:
            print("\n✨ BitNet Verification PASSED!")
        else:
            print("\n⚠️ BitNet Verification Produced Empty/Short Answer.")

    except Exception as e:
        print(f"\n❌ Verification Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_bitnet()
