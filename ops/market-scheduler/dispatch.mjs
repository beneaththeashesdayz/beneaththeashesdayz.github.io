import {pathToFileURL} from 'node:url';

const target = 'https://api.github.com/repos/beneaththeashesdayz/beneaththeashesdayz.github.io/actions/workflows/sync-gtx-market.yml';
export async function dispatch({token, request=fetch, log=console.log}={}) {
  if (!token?.trim()) throw new Error('Set MARKET_ACTIONS_TOKEN in the private Railway service variables.');
  const headers = {Authorization:`Bearer ${token.trim()}`, Accept:'application/vnd.github+json', 'X-GitHub-Api-Version':'2022-11-28', 'User-Agent':'BTA-Market-Scheduler'};
  const runs = await request(target+'/runs?branch=main&per_page=20', {headers, signal:AbortSignal.timeout(20000)});
  if (!runs.ok) throw new Error(`Cannot check market sync runs (HTTP ${runs.status}).`);
  const data = await runs.json();
  if (!Array.isArray(data.workflow_runs)) throw new Error('Invalid workflow run response.');
  const active = data.workflow_runs.find(r=>r.status !== 'completed');
  if (active) {
    log(`Market sync already ${active.status}: ${active.html_url}. No duplicate queued.`);
    return {status:'active',id:active.id};
  }
  // Do not blindly retry an ambiguous POST: it may already have queued the run.
  const result = await request(target+'/dispatches', {method:'POST', headers:{...headers,'Content-Type':'application/json'}, body:JSON.stringify({ref:'main'}), signal:AbortSignal.timeout(20000)});
  if (![200,204].includes(result.status)) throw new Error(`Market sync dispatch failed (HTTP ${result.status}).`);
  log(`Hourly Chernarus trader sync requested at ${new Date().toISOString()}. Check GitHub Actions for completion and Pages publication.`);
  return {status:'dispatched'};
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  dispatch({token:process.env.MARKET_ACTIONS_TOKEN}).catch(error=>{
    // Avoid logging response bodies, headers, environment, or credentials.
    console.error(error.name==='TimeoutError' ? 'GitHub request timed out; inspect Actions before retrying.' : error.message);
    process.exitCode=1;
  });
}
