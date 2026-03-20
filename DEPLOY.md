# Free deployment option using Ollama (tunnel from your machine)

This project uses Ollama as the LLM backend. Ollama is typically run locally, which means fully free cloud hosting of the model is usually not possible because models require compute/GPU. A practical free approach is:

1) Run Ollama and the model on your local machine.
2) Expose the local Ollama HTTP API to the internet via a tunnel (Cloudflare Tunnel or ngrok).
3) Deploy the FastAPI app and static frontend to a free container host (or run via Docker) and configure the deployed app to use the public tunnel URL for `OLLAMA_URL`.

Steps (concise):

- On your local machine, install and run Ollama and pull the model `qwen2.5:7b`.
- Start Ollama (default API listens on `http://localhost:11434`).
- Install `cloudflared` (Cloudflare Tunnel) and run:

```bash
# authenticate once with your Cloudflare account
cloudflared tunnel login
# create a tunnel that exposes localhost:11434
cloudflared tunnel --url http://localhost:11434
```

This command will provide a public URL like `https://abc-123.cfargotunnel.com`.

- Deploy the API (Docker) on a free host (Fly.io has a free tier) or any container host. Set the environment variable `OLLAMA_URL` to the tunnel URL above (for example, `https://abc-123.cfargotunnel.com`). The app will then call your local Ollama through the tunnel.

Notes and caveats:
- Your machine must remain online so Ollama is reachable through the tunnel.
- Latency will be higher than a cloud-hosted LLM.
- Tunnel services (ngrok/cloudflared) have free tiers but come with limits.

If you'd like, I can:
- Add a small GitHub Actions workflow to build & push the Docker image to Docker Hub.
- Prepare Fly.io config and `flyctl` deployment files.
- Or, set up a Cloudflare Tunnel guide tailored to your OS.
