
import os
import sys
import time
import logging
from llama_cpp import Llama

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("Benchmark")

def run_benchmark():
    print("🚀 Starting BitNet Performance Benchmark")
    print("---------------------------------------")
    
    # Path to model
    model_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
        "satya_data", "models", "bitnet_b1.58_2B_4T", "bitnet_b1_58-large.Q8_0.gguf"
    )
    
    if not os.path.exists(model_path):
        print(f"❌ Model not found: {model_path}")
        return

    configs = [
        {"threads": 2, "n_batch": 256, "n_ctx": 4096}, # Current Default
        {"threads": 4, "n_batch": 512, "n_ctx": 2048}, # Max Threads, Half Context
        {"threads": 1, "n_batch": 128, "n_ctx": 2048}, # Single Thread
    ]
    
    question = "Explain photosynthesis." 
    max_tokens = 20 # Short generation for speed
    
    results = []

    for cfg in configs:
        print(f"\n⚙️ Testing Config: Threads={cfg['threads']}, Batch={cfg['n_batch']}, Ctx={cfg['n_ctx']}")
        
        try:
            # Load
            t_start = time.time()
            llm = Llama(
                model_path=model_path,
                n_threads=cfg['threads'],
                n_batch=cfg['n_batch'],
                n_ctx=cfg['n_ctx'],
                n_gpu_layers=0,
                verbose=False
            )
            load_time = time.time() - t_start
            
            # Warmup
            llm("Hello", max_tokens=1)
            
            # Inference
            t_inf_start = time.time()
            output = llm(
                f"Q: {question}\nA:", 
                max_tokens=max_tokens, 
                stop=["Q:", "\n"], 
                echo=False
            )
            total_inf_time = time.time() - t_inf_start
            
            # Metrics
            tokens_gen = output['usage']['completion_tokens']
            tps = tokens_gen / total_inf_time if total_inf_time > 0 else 0
            
            print(f"   ⏱️ Load Time: {load_time:.2f}s")
            print(f"   ⚡ Speed: {tps:.2f} tokens/sec")
            print(f"   📝 Generated: {tokens_gen} tokens")
            
            results.append({
                "config": cfg,
                "tps": tps,
                "load_time": load_time
            })
            
            # Cleanup to free RAM for next test
            del llm
            
        except Exception as e:
            print(f"   ❌ Failed: {e}")

    # Best Result
    if results:
        best = max(results, key=lambda x: x['tps'])
        print(f"\n🏆 WINNER: Threads={best['config']['threads']}, Ctx={best['config']['n_ctx']}")
        print(f"   Speed: {best['tps']:.2f} t/s")
    else:
        print("\n❌ All benchmarks failed.")

if __name__ == "__main__":
    run_benchmark()
