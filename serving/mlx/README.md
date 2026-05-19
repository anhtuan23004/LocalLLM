# MLX Serving

MLX-LM runs locally on Apple Silicon through Metal. It is intentionally not a
Docker Compose service because Docker containers do not get native Metal access.

```bash
python3 -m pip install mlx-lm
cp serving/mlx/.env.example serving/mlx/.env
serving/mlx/serve.sh
curl http://localhost:18081/health
```

Set `MLX_MODEL` to a Hugging Face model id or a local MLX-compatible model path.
