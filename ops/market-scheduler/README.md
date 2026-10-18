# Chernarus trader refresh scheduler

Railway runs this short task hourly at minute 17 UTC (also minute 17 Eastern). It requests the existing `Sync GTX Market` GitHub workflow on `main`, then exits. It does not connect to GTX, change game data, or store GTX credentials.

Deploy this directory as a separate Railway cron service. Set Root Directory to `/ops/market-scheduler` with Dockerfile builder, cron schedule `17 * * * *`, restart policy Never, and watch path `/ops/market-scheduler/**`. Configure these in the Railway dashboard; new services cannot opt into the deprecated Config as Code system. No public domain or volume is needed.

Set private `MARKET_ACTIONS_TOKEN` to a fine-grained GitHub token restricted to `beneaththeashesdayz.github.io`, with Actions read/write and default Metadata read. Do not grant Contents write or access to other repositories. Set an expiry and renew it before expiration. Never commit the token.

Run `node --test dispatch.test.mjs` to test locally. Run the Railway task once after setting the token and verify the GitHub workflow and subsequent Pages deployment succeed. Only then remove the native GitHub `schedule` trigger; retain `workflow_dispatch` and existing push triggers. Until that handoff is verified, GitHub scheduling remains the active fallback.

Overlapping GitHub runs are skipped. HTTP errors fail visibly in Railway. A request timeout is not blindly retried because GitHub might already have accepted it. Inspect Actions before manual retries. A successful dispatch means queued, not published. Hosting outages and GitHub execution/Pages queues can still delay publication; this replaces the observed multi-hour schedule-trigger delays, not all possible service delays.
