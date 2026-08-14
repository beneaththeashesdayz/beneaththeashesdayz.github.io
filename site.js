document.addEventListener('DOMContentLoaded',()=>{
  document.body.classList.add('discord-ready');
  const style=document.createElement('style');
  style.textContent=`
    body.discord-ready::before,body.discord-ready::after,body.discord-ready>header::after{display:none!important}
    .site-server-link{position:fixed;z-index:10000;top:18px;right:360px;display:inline-flex;align-items:center;justify-content:center;flex-wrap:nowrap;gap:9px;width:154px;min-height:44px;white-space:nowrap;padding:0 16px;border:1px solid #8f6c3c;border-radius:8px;background:#6f542d;color:#fff!important;font-size:.76rem;font-weight:900;letter-spacing:.08em;text-transform:uppercase;box-shadow:0 8px 28px rgba(0,0,0,.38);transition:transform .15s ease,background .15s ease}.site-server-link:hover{transform:translateY(-2px);background:#816238}.site-server-link.namalsk{border-color:#40545f;background:#131a1d;color:#a9cad8!important}.site-server-link.chernarus{border-color:#5a4638;background:#1c1714;color:#deb899!important}.site-server-link.chernarus:hover{background:#281f1a}.site-server-link.namalsk:hover{background:#1b2930}.site-server-link .server-icon{width:20px;height:20px;display:inline-flex;align-items:center}.site-server-link .server-icon svg{width:20px;height:20px;fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}.site-store-link{position:fixed;z-index:10000;top:18px;right:190px;display:inline-flex;align-items:center;justify-content:center;gap:9px;width:154px;min-height:44px;padding:0 16px;border:1px solid #e17a3a;border-radius:8px;background:#c9672d;color:#fff!important;font-size:.76rem;font-weight:900;letter-spacing:.08em;text-transform:uppercase;box-shadow:0 8px 28px rgba(0,0,0,.38);transition:transform .15s ease,background .15s ease}.site-store-link:hover{transform:translateY(-2px);background:#db7334}.site-store-link span{white-space:nowrap}.site-store-link .store-flame{width:20px;height:22px;display:inline-flex;align-items:center}.site-store-link .store-flame svg{width:20px;height:22px;fill:currentColor}.site-discord-link{position:fixed;flex-wrap:nowrap;z-index:10000;top:18px;right:20px;display:inline-flex;align-items:center;gap:9px;width:154px;min-height:44px;padding:0 16px;border:1px solid #7b83ff;border-radius:8px;background:#5865F2;color:#fff!important;font-size:.76rem;font-weight:900;letter-spacing:.08em;text-transform:uppercase;box-shadow:0 8px 28px rgba(0,0,0,.38);transition:transform .15s ease,background .15s ease}
    .site-discord-link:hover{transform:translateY(-2px);background:#6571f5}.site-discord-link span{white-space:nowrap}
    .site-discord-link svg{width:22px;height:22px;fill:currentColor;flex:none}
    .trader-group .card[href="./linda/"] img,.search-grid .card[href="./linda/"] img{object-position:65% center!important}
    @media(max-width:760px){.site-server-link{top:12px;right:284px;width:120px;min-height:40px;padding:0 8px;font-size:.58rem;white-space:nowrap}.site-store-link{top:12px;right:148px;width:120px;min-height:40px;padding:0 8px;font-size:.55rem;white-space:nowrap}.site-discord-link{top:12px;right:12px;width:120px;min-height:40px;padding:0 8px;font-size:.55rem;white-space:nowrap}.site-discord-link svg{width:19px;height:19px}}
  `;
  document.head.appendChild(style);
  if(!document.querySelector('.site-server-link')){
    const a=document.createElement('a');
    const isNamalsk=window.location.pathname.toLowerCase().includes('/namalsk/');
    const endpoint=isNamalsk?'205.209.105.251:2680':'69.10.59.28:2302';
    const world=isNamalsk?'Namalsk':'Chernarus';
    a.className='site-server-link '+(isNamalsk?'namalsk':'chernarus');
    a.href='steam://connect/'+endpoint;
    a.setAttribute('aria-label','Join the Beneath the Ashes '+world+' DayZ server');
    a.innerHTML='<span class="server-icon" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M9 7V4m6 3V4M7 7h10v5a5 5 0 0 1-10 0V7Z"/><path d="M12 17v3m-3 0h6M15 12h7m-3-3 3 3-3 3"/></svg></span><span>Play '+world+'</span>';
    document.body.appendChild(a);
  }
  if(!document.querySelector('.site-store-link')){
    const a=document.createElement('a');
    a.className='site-store-link';
    a.href='https://beneaththeashedayz.tip4serv.com/';
    a.target='_blank';
    a.rel='noopener noreferrer';
    a.setAttribute('aria-label','Open the Beneath the Ashes store');
    a.innerHTML='<span class="store-flame" aria-hidden="true"><svg viewBox="0 0 24 28"><path d="M13.7 0c.3 5.4-2.8 7.2-4.7 10.1-1.2 1.8-1.4 3.5-.5 5.1-2.1-1.1-3.1-3.1-2.8-5.8C2.1 12.7 0 16.7 0 20.3 0 24.6 5.4 28 12 28s12-3.4 12-7.7c0-5.1-3.4-9.2-6.2-12.2-.2 2.5-1.1 4.5-2.8 5.9.4-4.8-.1-8.9-3.3-14ZM12 25.5c-2.8 0-5-1.5-5-3.5 0-1.8 1-3.1 2.6-4.8-.1 1.8.6 3 1.6 3.6-.3-2.2.8-3.5 2.1-5.2 1.4 1.7 3.7 3.7 3.7 6.4 0 2-2.2 3.5-5 3.5Z"/></svg></span><span>Store Front</span>';
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