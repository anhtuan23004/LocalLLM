import argparse
import os
from huggingface_hub import snapshot_download

def download_model(model_id, local_dir, token=None):
    """
    Downloads a model from Hugging Face Hub using snapshot_download.
    """
    
    # Check if the local directory exists; if not, create it (including parent folders)
    if not os.path.exists(local_dir):
        print(f"[*] Creating directory: {local_dir}")
        os.makedirs(local_dir, exist_ok=True)

    print(f"[*] Starting download for: {model_id}")
    try:
        # Perform the download and return the local path
        download_path = snapshot_download(
            repo_id=model_id,
            local_dir=local_dir,
            local_dir_use_symlinks=False,  # Set to False to copy files directly
            revision="main",
            token=token,
            # Exclude non-essential file formats to save space/time
            ignore_patterns=["*.msgpack", "*.h5", "*.ot"] 
        )
        print(f"[+] Model downloaded successfully to: {download_path}")
    except Exception as e:
        print(f"[-] Error downloading model: {e}")

if __name__ == "__main__":
    # Initialize argument parser for command-line usage
    parser = argparse.ArgumentParser(description="Download models from Hugging Face")
    parser.add_argument("model_id", type=str, help="HF model ID (e.g., Qwen/Qwen2.5-VL-7B-Instruct)")
    parser.add_argument("--dir", type=str, default="models", help="Base directory for all models")
    parser.add_argument("--token", type=str, default=None, help="HF Access Token for gated models")

    args = parser.parse_args()

    # --- AUTO-FOLDER LOGIC ---
    # Extract the model name from the ID (e.g., 'Qwen/Qwen2.5-7B' -> 'Qwen2.5-7B')
    model_folder_name = args.model_id.split("/")[-1]
    
    # Combine the base directory with the model name to create the final path
    # Result: 'models/Qwen2.5-7B'
    final_dir = os.path.join(args.dir, model_folder_name)

    # Execute the download process
    download_model(args.model_id, final_dir, args.token)
