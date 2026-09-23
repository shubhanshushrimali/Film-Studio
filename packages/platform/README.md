# Production spine

This is the missing middle. It does not replace the app.

**Who stores what**
- Postgres: projects, jobs, credits, the script text, the chunks
- pgvector inside Postgres: search over those chunks
- Neo4j: who is in which shot, after you lock it
- Redis: the queue. Slow work waits here. The page does not freeze
- Object store, later: pictures and clips. Not in this compose file yet

**Rules**
- Chunk by scene heading. Do not chop the script into random tokens.
- Search returns a few chunks. The video model never gets the whole script.
- A job stops for you before a clip, and again before upload.
- Three failed tries stop. You decide.
- Face check uses the character-continuity skill: one approved face, then every shot is compared to it.

**Not running yet**
- The Plan button does not call this graph yet.
- No face model is installed.
- No payments, no login, no traces.

Start the databases when you want them:

```bash
docker compose -f packages/platform/docker-compose.yml up -d
```
