document.addEventListener('DOMContentLoaded',()=>{
  document.body.classList.add('discord-ready');
  if(document.body.classList.contains('home-page')||document.querySelector('.world-tag:not(.frozen)')){
    const emberStyle=document.createElement('style');
    emberStyle.textContent='.ember-field{position:fixed;inset:0;z-index:1;pointer-events:none;overflow:hidden}.ember-field i{position:absolute;bottom:-10px;width:3px;height:3px;border-radius:50%;background:#f3a15b;box-shadow:0 0 7px 2px rgba(235,126,55,.8);animation:ember-float linear infinite;opacity:0}@keyframes ember-float{0%{transform:translate3d(0,0,0) scale(.6);opacity:0}12%{opacity:.85}80%{opacity:.45}100%{transform:translate3d(var(--drift),-110vh,0) scale(1);opacity:0}}@media(prefers-reduced-motion:reduce){.ember-field i{animation:none;opacity:.2}}';
    document.head.appendChild(emberStyle);
    const windStyle=document.createElement('style');windStyle.textContent='.ember-field i{width:4px!important;height:4px!important;box-shadow:0 0 9px 3px rgba(235,126,55,.9)}@keyframes ember-float{0%{transform:translate3d(0,0,0) scale(.55);opacity:0}12%{opacity:.9}32%{transform:translate3d(calc(var(--drift)*-.35),-28vh,0) scale(1.05)}52%{transform:translate3d(calc(var(--drift)*.65),-52vh,0) scale(.9)}74%{transform:translate3d(calc(var(--drift)*-.2),-79vh,0) scale(1.15)}100%{transform:translate3d(var(--drift),-110vh,0) scale(.8);opacity:0}}';document.head.appendChild(windStyle);
    const swayStyle=document.createElement('style');swayStyle.textContent='@keyframes ember-float{0%{transform:translateY(0) scale(.55);margin-left:0;opacity:0}12%{opacity:.9}30%{transform:translateY(-28vh) scale(1.05);margin-left:-34px}48%{transform:translateY(-50vh) scale(.9);margin-left:28px}67%{transform:translateY(-73vh) scale(1.12);margin-left:-22px}84%{transform:translateY(-92vh) scale(.95);margin-left:38px}100%{transform:translateY(-110vh) scale(.8);margin-left:0;opacity:0}}';document.head.appendChild(swayStyle);
    const field=document.createElement('div');field.className='ember-field';field.setAttribute('aria-hidden','true');
    for(let i=0;i<18;i++){const ember=document.createElement('i');ember.style.left=`${(i*37)%100}%`;ember.style.setProperty('--drift',`${((i%5)-2)*22}px`);ember.style.animationDuration=`${13+(i%7)*2}s`;ember.style.animationDelay=`-${(i*1.7)%18}s`;ember.style.width=ember.style.height=`${2+(i%3)}px`;field.appendChild(ember)}
    document.body.appendChild(field);
  }
  const style=document.createElement('style');
  style.textContent=`
    body.discord-ready::before,body.discord-ready::after,body.discord-ready>header::after{display:none!important}
    .site-server-link{position:fixed;z-index:10000;top:18px;right:360px;display:inline-flex;align-items:center;justify-content:center;flex-wrap:nowrap;gap:9px;width:154px;min-height:44px;white-space:nowrap;padding:0 16px;border:1px solid #8f6c3c;border-radius:8px;background:#6f542d;color:#fff!important;font-size:.76rem;font-weight:900;letter-spacing:.08em;text-transform:uppercase;box-shadow:0 8px 28px rgba(0,0,0,.38);transition:transform .15s ease,background .15s ease}.site-server-link:hover{transform:translateY(-2px);background:#816238}.site-server-link.namalsk{border:1px solid #a9cad8!important;background:#a9cad8!important;color:#131a1d!important}.site-server-link.chernarus{border-color:#deb899;background:#deb899;color:#1c1714!important}.site-server-link.chernarus:hover{background:#c9a27f;border-color:#c9a27f}.site-server-link.namalsk:hover{background:#1b2930}.site-server-link .server-icon{width:20px;height:20px;display:inline-flex;align-items:center}.site-server-link .server-icon svg{width:20px;height:20px;fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}.site-store-link{position:fixed;z-index:10000;top:18px;right:190px;display:inline-flex;align-items:center;justify-content:center;gap:9px;width:154px;min-height:44px;padding:0 16px;border:1px solid #e17a3a;border-radius:8px;background:#c9672d;color:#fff!important;font-size:.76rem;font-weight:900;letter-spacing:.08em;text-transform:uppercase;box-shadow:0 8px 28px rgba(0,0,0,.38);transition:transform .15s ease,background .15s ease}.site-store-link:hover{transform:translateY(-2px);background:#db7334}.site-store-link span{white-space:nowrap}.site-store-link .store-flame{width:20px;height:22px;display:inline-flex;align-items:center}.site-store-link .store-flame svg{width:20px;height:22px;fill:currentColor}.site-discord-link{position:fixed;flex-wrap:nowrap;z-index:10000;top:18px;right:20px;display:inline-flex;align-items:center;gap:9px;width:154px;min-height:44px;padding:0 16px;border:1px solid #7b83ff;border-radius:8px;background:#5865F2;color:#fff!important;font-size:.76rem;font-weight:900;letter-spacing:.08em;text-transform:uppercase;box-shadow:0 8px 28px rgba(0,0,0,.38);transition:transform .15s ease,background .15s ease}
    .site-discord-link:hover{transform:translateY(-2px);background:#6571f5}.site-discord-link span{white-space:nowrap}
    .site-discord-link svg{width:22px;height:22px;fill:currentColor;flex:none}
    .trader-group .card[href="./linda/"] img,.search-grid .card[href="./linda/"] img{object-position:65% center!important}
    @media(max-width:760px){.site-server-link{top:12px;right:284px;width:120px;min-height:40px;padding:0 8px;font-size:.58rem;white-space:nowrap}.site-support-link{top:12px;right:284px;width:120px;min-height:40px;padding:0 8px;font-size:.55rem;white-space:nowrap}.site-store-link{top:12px;right:148px;width:120px;min-height:40px;padding:0 8px;font-size:.55rem;white-space:nowrap}.site-discord-link{top:12px;right:12px;width:120px;min-height:40px;padding:0 8px;font-size:.55rem;white-space:nowrap}.site-discord-link svg{width:19px;height:19px}}
  `;
  document.head.appendChild(style);
  document.querySelectorAll('.launcher-select').forEach(select=>select.addEventListener('change',()=>{const urls={steam:'https://store.steampowered.com/app/221100/DayZ/',dzsa:'https://dayzsalauncher.com/',beans:'https://dayzbeanslauncher.com/',titan:'https://dayz-launcher.com/?lang=en'};const url=urls[select.value];if(url){window.open(url,'_blank','noopener,noreferrer');select.selectedIndex=0}}));
  document.querySelectorAll('.server-info').forEach(panel=>{const button=panel.querySelector('.copy-server');button?.addEventListener('click',async()=>{const value=panel.dataset.serverIp+':'+panel.dataset.serverPort;let copied=false;try{if(navigator.clipboard&&window.isSecureContext){await navigator.clipboard.writeText(value);copied=true}}catch(e){}if(!copied){const area=document.createElement('textarea');area.value=value;area.setAttribute('readonly','');area.style.position='fixed';area.style.opacity='0';document.body.appendChild(area);area.select();try{copied=document.execCommand('copy')}catch(e){}area.remove()}if(copied){button.textContent='Copied';button.classList.add('copied');setTimeout(()=>{button.textContent='Copy Connection Info';button.classList.remove('copied')},1800)}else{window.prompt('Copy connection info:',value)}})});
  if(!document.querySelector('.site-support-link')){
    const a=document.createElement('a');
    a.className='site-support-link';
    a.href='https://discord.com/channels/1278830251383721984/1402637759990202368';
    a.target='_blank';
    a.rel='noopener noreferrer';
    a.setAttribute('aria-label','Open Beneath the Ashes support tickets');
    a.textContent='Support';
    document.body.appendChild(a);
  }
  if(!document.querySelector('.site-store-link')){
    const a=document.createElement('a');
    a.className='site-store-link';
    a.href='https://beneaththeashedayz.tip4serv.com/';
    a.target='_blank';
    a.rel='noopener noreferrer';
    a.setAttribute('aria-label','Open the Beneath the Ashes store');
    a.innerHTML='<span>Store Front</span>';
    document.body.appendChild(a);
  }
  if(!document.querySelector('.site-discord-link')){
    const a=document.createElement('a');
    a.className='site-discord-link';
    a.href='https://discord.gg/NpwumFFzFy';
    a.target='_blank';
    a.rel='noopener noreferrer';
    a.setAttribute('aria-label','Join Beneath the Ashes on Discord');
    a.innerHTML='<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20.32 4.37A19.8 19.8 0 0 0 15.44 3l-.24.49a18.3 18.3 0 0 1 4.43 1.66 15.6 15.6 0 0 0-15.26 0A18.1 18.1 0 0 1 8.8 3.49L8.56 3a19.8 19.8 0 0 0-4.88 1.37C.59 8.97-.25 13.45.17 17.87a19.9 19.9 0 0 0 5.99 3.02l1.45-1.98a12.6 12.6 0 0 1-2.27-1.09l.56-.42c4.39 2.03 9.12 2.03 13.45 0l.56.42c-.73.43-1.49.8-2.27 1.09l1.45 1.98a19.7 19.7 0 0 0 5.98-3.02c.5-5.13-.87-9.58-3.95-13.5ZM8.66 15.16c-1.31 0-2.38-1.2-2.38-2.68 0-1.47 1.05-2.68 2.38-2.68s2.4 1.21 2.38 2.68c0 1.48-1.05 2.68-2.38 2.68Zm8.66 0c-1.31 0-2.38-1.2-2.38-2.68 0-1.47 1.05-2.68 2.38-2.68s2.4 1.21 2.38 2.68c0 1.48-1.05 2.68-2.38 2.68Z"/></svg><span>Join Discord</span>';
    document.body.appendChild(a);
  }
});
