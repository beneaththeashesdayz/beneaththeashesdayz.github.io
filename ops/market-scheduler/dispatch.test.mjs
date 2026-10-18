import {test} from 'node:test';
import assert from 'node:assert/strict';
import {dispatch} from './dispatch.mjs';

test('dispatches only the fixed market workflow on main', async()=>{
  const calls=[];
  const result=await dispatch({token:'test-only',log:()=>{},request:async(url,opts)=>{
    calls.push({url,opts});
    return calls.length===1 ? {ok:true,json:async()=>({workflow_runs:[{status:'completed'}]})} : {status:204};
  }});
  assert.equal(result.status,'dispatched');
  assert.equal(calls[1].url,'https://api.github.com/repos/beneaththeashesdayz/beneaththeashesdayz.github.io/actions/workflows/sync-gtx-market.yml/dispatches');
  assert.deepEqual(JSON.parse(calls[1].opts.body),{ref:'main'});
});
test('does not queue another run while one is active',async()=>{
  let calls=0;
  const result=await dispatch({token:'test-only',log:()=>{},request:async()=>{calls++;return {ok:true,json:async()=>({workflow_runs:[{status:'queued',id:1}]})};}});
  assert.equal(result.status,'active');assert.equal(calls,1);
});
test('fails closed on missing token, unreadable state, and dispatch rejection',async()=>{
  await assert.rejects(dispatch({}),/MARKET_ACTIONS_TOKEN/);
  await assert.rejects(dispatch({token:'test-only',request:async()=>({ok:false,status:401})}),/HTTP 401/);
  let calls=0;
  await assert.rejects(dispatch({token:'test-only',request:async()=>++calls===1?{ok:true,json:async()=>({workflow_runs:[]})}:{status:403}}),/HTTP 403/);
});
test('ambiguous dispatch failure is not blindly retried',async()=>{
  let calls=0;
  await assert.rejects(dispatch({token:'test-only',request:async()=>{if(++calls===1)return {ok:true,json:async()=>({workflow_runs:[]})};throw new Error('connection lost');}}),/connection lost/);
  assert.equal(calls,2);
});
