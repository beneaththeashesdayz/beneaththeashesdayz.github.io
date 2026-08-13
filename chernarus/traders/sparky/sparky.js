(() => {
  const root = document.querySelector('[data-sparky]');
  if (!root) return;
  const money = n => Number(n) < 0 ? 'Unavailable' : new Intl.NumberFormat('en-US', {style:'currency',currency:'USD',maximumFractionDigits:0}).format(n);
  const clean = value => String(value || '').replace(/[_-]+/g, ' ').replace(/([a-z])([A-Z])/g, '$1 $2');
  let payload;

  function render() {
    const query = root.querySelector('[data-search]').value.trim().toLowerCase();
    const rows = payload.vehicles.filter(v => [v.group,v.className,v.color].join(' ').toLowerCase().includes(query));
    root.querySelector('[data-count]').textContent = `${rows.length} of ${payload.vehicleCount} vehicle options`;
    root.querySelector('[data-list]').replaceChildren(...rows.map(v => {
      const card = document.createElement('article'); card.className = 'sparky-card';
      const title = document.createElement('h3'); title.textContent = clean(v.group);
      const color = document.createElement('div'); color.className='sparky-color'; color.textContent = v.color || 'Default finish';
      const prices = document.createElement('dl');
      [['Purchase',v.buyPrice],['Sell body',v.sellPrice],['Insurance',v.insurancePrice],['Repaint',v.repaintPrice]].forEach(([label,price]) => {
        const dt=document.createElement('dt'); dt.textContent=label; const dd=document.createElement('dd'); dd.textContent=money(price); prices.append(dt,dd);
      });
      card.append(title,color,prices);
      const included=[...(v.includedAttachments||[]),...(v.includedCargo||[])];
      if(included.length){const p=document.createElement('p');p.textContent=`Included: ${included.map(clean).join(', ')}`;card.append(p)}
      return card;
    }));
  }

  fetch(`../../../data/live-market/sparky.json?v=${Date.now()}`, {cache:'no-store'}).then(r => {if(!r.ok) throw Error(r.status);return r.json()}).then(data => {
    payload=data; root.querySelector('[data-status]').textContent=`Live configuration â€¢ ${data.vehicleCount} vehicle options`;
    const networks=root.querySelector('[data-networks]');
    networks.replaceChildren(...data.garageNetworks.map(g=>{const li=document.createElement('li');const services=[g.canRepaint&&'repainting',g.canRepairEngine&&'engine repair',g.canRepairAttachments&&'parts repair',g.canRefuel&&'fuel/coolant'].filter(Boolean);li.textContent=`${g.name}: deposit ${money(g.depositPrice)}, withdraw ${money(g.withdrawPrice)}${services.length ? ` â€¢ ${services.join(', ')}`:''}`;return li}));
    root.querySelector('[data-insurance]').textContent=data.insuranceRecoveryEnabled ? (data.insuranceRequiredForRuinedRecovery ? 'Insurance is required for ruined-vehicle recovery.' : 'Ruined-vehicle recovery is enabled; insurance requirements vary.') : 'Ruined-vehicle insurance recovery is disabled.';
    root.querySelector('[data-search]').addEventListener('input',render); render();
  }).catch(()=>{root.querySelector('[data-status]').textContent='Live Sparky configuration is temporarily unavailable.'});
})();

