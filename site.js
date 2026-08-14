document.addEventListener('DOMContentLoaded',()=>{
  document.body.classList.add('discord-ready');
  const style=document.createElement('style');
  style.textContent=`
    body.discord-ready::before,body.discord-ready::after,body.discord-ready>header::after{display:none!important}
    .site-store-link{position:fixed;z-index:10000;top:18px;right:190px;display:inline-flex;align-items:center;min-height:44px;padding:0 16px;border:1px solid #70513f;border-radius:8px;background:#211813;color:#f2d0b6!important;font-size:.76rem;font-weight:900;letter-spacing:.08em;text-transform:uppercase;box-shadow:0 8px 28px rgba(0,0,0,.38);transition:transform .15s ease,background .15s ease}.site-store-link:hover{transform:translateY(-2px);background:#2b1d16}.site-discord-link{position:fixed;z-index:10000;top:18px;right:20px;display:inline-flex;align-items:center;gap:9px;min-height:44px;padding:0 16px;border:1px solid #7b83ff;border-radius:8px;background:#5865F2;color:#fff!important;font-size:.76rem;font-weight:900;letter-spacing:.08em;text-transform:uppercase;box-shadow:0 8px 28px rgba(0,0,0,.38);transition:transform .15s ease,background .15s ease}
    .site-discord-link:hover{transform:translateY(-2px);background:#6571f5}
    .site-discord-link svg{width:22px;height:22px;fill:currentColor;flex:none}
    .trader-group .card[href="./linda/"] img,.search-grid .card[href="./linda/"] img{object-position:65% center!important}
    @media(max-width:760px){.site-store-link{top:12px;right:137px;min-height:40px;padding:0 10px;font-size:.6rem}.site-discord-link{top:12px;right:12px;min-height:40px;padding:0 12px;font-size:.65rem}.site-discord-link svg{width:19px;height:19px}}
  `;
  document.head.appendChild(style);
  if(!document.querySelector('.site-store-link')){
    const a=document.createElement('a');
    a.className='site-store-link';
    a.href='https://beneaththeashedayz.tip4serv.com/';
    a.target='_blank';
    a.rel='noopener noreferrer';
    a.setAttribute('aria-label','Open the Beneath the Ashes store');
    a.textContent='Store';
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