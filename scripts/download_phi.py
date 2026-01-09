import os
import requests
import sys

def download_file(url, local_filename):
    print(f"Starting download from {url}...")
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        total_size = int(r.headers.get('content-length', 0))
        downloaded = 0
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        if downloaded % (10 * 1024 * 1024) == 0:  # Log every 10MB
                            print(f"Downloaded: {downloaded/1024/1024:.1f}MB / {total_size/1024/1024:.1f}MB ({percent:.1f}%)")
    print(f"Download complete! Saved to {local_filename}")

if __name__ == "__main__":
    url = "https://huggingface.co/mav23/phi-1_5-GGUF/resolve/6865c3f822012bdab963b53f5f2b1f1d1d2b3c39/phi-1_5.Q4_K_M.gguf?download=true"
    output_path = "satya_data/models/phi-1_5.Q4_K_M.gguf"
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    try:
        download_file(url, output_path)
    except Exception as e:
        print(f"Error downloading: {e}")
        sys.exit(1)
