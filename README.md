# Film studio

One repo. Three jobs.

- `apps/studio` is the app you open. It came from Nautilus.
- `packages/plan` writes the shot plan. It came from CineCrew. It does not make video.
- `packages/flow` makes the clips, the voice, the cut, and the upload. It came from Ai-flow.
  - Video machine: `packages/flow/src/gpu_backend`
  - Cut and upload: `packages/flow/src/flow/postproduction.py` and `publisher.py`

## Rules

- One plan. The video machine gets one shot, not the whole script.
- You lock the hero before a clip is made.
- Upload only after you keep a take.
- The plan button uses CineCrew only when `STUDIO_PLAN_WRITER=cinecrew`.
  Leave it as `studio` until that package is installed. The app still opens.

## Run the app

```bash
cd apps/studio
python -m venv .venv
pip install -e ".[dev]"
npm --prefix web ci
npm --prefix web run build
nautilus-studio --host 127.0.0.1 --port 7860
```

## Licenses

Nautilus and CineCrew are Apache-2.0. Ai-flow is MIT. Notices stay in each folder.
CineCrew is the ECCV 2026 paper by Jiaben Chen, Sixun Dong, and co-authors.
