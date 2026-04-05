# HF Spaces Deployment Guide

## Status: Ready for Push ✓

All project files are committed and ready:
- ✓ Dockerfile with port 7860 exposed
- ✓ requirements.txt with all dependencies
- ✓ openenv.yaml with task definitions
- ✓ app/ package with FastAPI endpoints
- ✓ inference.py and validate.py validators
- ✓ HF CLI skills installed globally and locally
- ✓ Git commits: 2 commits ahead of remote

## Step 1: Authenticate with Hugging Face

Get your HF token from: https://huggingface.co/settings/tokens
(Create new token with "Write" access to Spaces if needed)

```bash
# Switch to project directory
cd /Users/lakshyagupta/Desktop/sst

# Authenticate using hf CLI
hf auth login
# Paste your token when prompted

# Verify authentication
hf auth whoami
```

## Step 2: Push to HF Spaces

```bash
git push origin main
```

The Docker build will start automatically. Wait 5-10 minutes for completion.

## Step 3: Verify Deployment

Once the Space is live at https://huggingface.co/spaces/Lucifer4142T/sst

### Test health endpoint
```bash
curl https://huggingface.co/spaces/Lucifer4142T/sst/health
```

### Run full validation suite
```bash
python validate.py
```

### Test inference (if API credentials are set as Space secrets)
```bash
export API_BASE_URL="https://Lucifer4142T-sst.hf.space"
export HF_TOKEN="<your-hf-token>"
python inference.py
```

## Expected Endpoints

After deployment, these endpoints will be available:

```
GET  /health          - Service health check
GET  /tasks           - List available tasks  
POST /reset           - Reset environment
POST /step            - Execute step in task
GET  /state           - Get current state
```

## Space Configuration

The Space is configured with:
- **Image:** Docker (Python 3.11-slim)
- **Port:** 7860
- **Command:** `uvicorn app.main:app --host 0.0.0.0 --port 7860`

### Optional Space Secrets (for hosted inference)
If you want to use OpenAI-compatible models in the Space, add these secrets in Space settings:
- `API_BASE_URL` - Base URL for your LLM API
- `MODEL_NAME` - Model name to use
- `HF_TOKEN` - Your Hugging Face token

## Git Commits Ready to Push

```
commit 635da53 - Add HF skills and agent customizations
commit <initial> - Initial project setup
```

---

**Next:** Run `hf auth login`, then `git push origin main`
