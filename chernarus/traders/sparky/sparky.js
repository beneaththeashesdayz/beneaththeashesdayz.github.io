(() => {
  const root = document.querySelector('[data-sparky]');
  if (!root) return;

  const money = value => Number(value) < 0
    ? 'Unavailable'
    : new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        maximumFractionDigits: 0
      }).format(value);
  const clean = value => String(value || '')
    .replace(/[_-]+/g, ' ')
    .replace(/([a-z])([A-Z])/g, '$1 $2');
  let payload;

  function priceRange(variants, field) {
    const prices = variants
      .map(variant => Number(variant[field]))
      .filter(price => Number.isFinite(price) && price >= 0)
      .sort((a, b) => a - b);
    if (!prices.length) return 'Unavailable';
    if (prices[0] === prices[prices.length - 1]) return money(prices[0]);
    return `${money(prices[0])} - ${money(prices[prices.length - 1])}`;
  }

  function groupVehicles(vehicles) {
    const groups = new Map();
    vehicles.forEach(vehicle => {
      const groupName = vehicle.groupName || vehicle.name || vehicle.itemname || 'Unknown Vehicle';
      const key = String(groupName).trim().toLowerCase();
      if (!groups.has(key)) {
        groups.set(key, {
          name: vehicle.name || clean(groupName),
          variants: []
        });
      }
      groups.get(key).variants.push(vehicle);
    });
    return [...groups.values()]
      .map(group => ({
        ...group,
        variants: group.variants.sort((a, b) =>
          String(a.color || '').localeCompare(String(b.color || '')))
      }))
      .sort((a, b) => a.name.localeCompare(b.name));
  }

  function addPriceRows(list, rows) {
    rows.forEach(([label, value]) => {
      const dt = document.createElement('dt');
      const dd = document.createElement('dd');
      dt.textContent = label;
      dd.textContent = value;
      list.append(dt, dd);
    });
  }

  function includedItems(variants) {
    const values = variants.flatMap(vehicle => [
      ...(vehicle.attachmentItems || []).map(item => item.itemname),
      ...(vehicle.additionalCargoItems || []),
      ...(payload.cargoItemsWhenBuyingVehicle || [])
    ]).filter(Boolean);
    return [...new Set(values)];
  }

  function variantPanel(vehicle) {
    const panel = document.createElement('div');
    panel.className = 'sparky-variant';
    const color = document.createElement('h4');
    color.textContent = vehicle.color || 'Default finish';
    const className = document.createElement('div');
    className.className = 'sparky-class';
    className.textContent = vehicle.itemname || '';
    const prices = document.createElement('dl');
    prices.className = 'sparky-variant-prices';
    addPriceRows(prices, [
      ['Purchase', money(vehicle.buyCost)],
      ['Sell body', money(vehicle.sellPrice)],
      ['Insurance', money(vehicle.insuranceCost)],
      ['Repaint', money(vehicle.repaintCost)]
    ]);
    panel.append(color, className, prices);
    return panel;
  }

  function vehicleCard(group) {
    const card = document.createElement('article');
    card.className = 'sparky-card';
    const title = document.createElement('h3');
    title.textContent = group.name;
    const variantCount = document.createElement('div');
    variantCount.className = 'sparky-variant-count';
    variantCount.textContent = `${group.variants.length} color option${group.variants.length === 1 ? '' : 's'}`;
    const prices = document.createElement('dl');
    prices.className = 'sparky-price-summary';
    addPriceRows(prices, [
      ['Purchase', priceRange(group.variants, 'buyCost')],
      ['Sell body', priceRange(group.variants, 'sellPrice')],
      ['Insurance', priceRange(group.variants, 'insuranceCost')],
      ['Repaint', priceRange(group.variants, 'repaintCost')]
    ]);
    card.append(title, variantCount, prices);

    const included = includedItems(group.variants);
    if (included.length) {
      const line = document.createElement('p');
      line.textContent = `Included: ${included.map(clean).join(', ')}`;
      card.append(line);
    }

    if (group.variants.length === 1) {
      const color = document.createElement('div');
      color.className = 'sparky-single-color';
      color.textContent = group.variants[0].color || 'Default finish';
      card.append(color);
    } else {
      const details = document.createElement('details');
      details.className = 'sparky-variants';
      const summary = document.createElement('summary');
      summary.textContent = `View ${group.variants.length} color variants and prices`;
      const grid = document.createElement('div');
      grid.className = 'sparky-variant-grid';
      grid.replaceChildren(...group.variants.map(variantPanel));
      details.append(summary, grid);
      card.append(details);
    }
    return card;
  }

  function render() {
    const query = root.querySelector('[data-search]').value.trim().toLowerCase();
    const groups = groupVehicles(payload.vehicles);
    const visible = groups.filter(group => !query || group.variants.some(vehicle =>
      [group.name, vehicle.groupName, vehicle.itemname, vehicle.color]
        .join(' ')
        .toLowerCase()
        .includes(query)
    ));
    root.querySelector('[data-count]').textContent =
      `${visible.length} of ${groups.length} vehicle models | ${payload.vehicleCount} total color options`;
    root.querySelector('[data-list]').replaceChildren(...visible.map(vehicleCard));
  }

  fetch(`../../../data/live-market/sparky.json?v=${Date.now()}`, { cache: 'no-store' })
    .then(response => {
      if (!response.ok) throw Error(response.status);
      return response.json();
    })
    .then(data => {
      payload = data;
      const modelCount = groupVehicles(data.vehicles).length;
      root.querySelector('[data-status]').textContent =
        `Live configuration | ${modelCount} vehicle models | ${data.vehicleCount} color options`;
      const networks = root.querySelector('[data-networks]');
      networks.replaceChildren(...data.garageGroups.map(group => {
        const item = document.createElement('li');
        const services = [
          group.canRepaintVehicles && 'repainting',
          group.canRepairVehicle && 'engine repair',
          group.canRepairVehicleAttachments && 'parts repair',
          group.canRefuelVehicle && 'fuel/coolant'
        ].filter(Boolean);
        item.textContent = `${group.name}: deposit ${money(group.costDeposit)}, withdraw ${money(group.costWithdraw)}` +
          (services.length ? ` | ${services.join(', ')}` : '');
        return item;
      }));
      root.querySelector('[data-insurance]').textContent = data.impound?.impoundRuinedVehicles
        ? (data.impound.ruinedVehiclesRequireVehicleInsurance
            ? 'Insurance is required for ruined-vehicle recovery.'
            : 'Ruined-vehicle recovery is enabled; insurance requirements vary.')
        : 'Ruined-vehicle insurance recovery is disabled.';
      root.querySelector('[data-search]').addEventListener('input', render);
      render();
    })
    .catch(() => {
      root.querySelector('[data-status]').textContent =
        'Live Sparky configuration is temporarily unavailable.';
    });
})();

