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
  const displayColor = value => clean(value || 'Default finish')
    .replace(/\b\w/g, letter => letter.toUpperCase());
  const categoryOrder = ['ground', 'water', 'air'];
  const categoryLabels = {
    ground: 'Ground Vehicles',
    water: 'Water Vehicles',
    air: 'Air Vehicles'
  };
  let payload;
  let selectedCategory = 'all';

  function priceRange(variants, field, disabledLabel) {
    const prices = variants
      .map(variant => Number(variant[field]))
      .filter(price => Number.isFinite(price) && price >= 0)
      .sort((a, b) => a - b);
    if (!prices.length) return disabledLabel;
    if (prices[0] === prices[prices.length - 1]) return money(prices[0]);
    return `${money(prices[0])} - ${money(prices[prices.length - 1])}`;
  }

  function isListedVehicle(vehicle) {
    return ['buyCost', 'sellPrice', 'repaintCost'].some(field =>
      Number.isFinite(Number(vehicle[field])) && Number(vehicle[field]) >= 0);
  }

  function operationPrice(value, disabledLabel) {
    const price = Number(value);
    return Number.isFinite(price) && price >= 0 ? money(price) : disabledLabel;
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
        category: vehicleCategory(group.variants),
        variants: group.variants.sort((a, b) =>
          String(a.color || '').localeCompare(String(b.color || '')))
      }))
      .sort((a, b) => a.name.localeCompare(b.name));
  }

  function categoryRoots(pattern) {
    return (payload.garageGroups || [])
      .filter(group => pattern.test(String(group.name || '')))
      .flatMap(group => group.vehicleWhitelist || [])
      .map(item => String(item).toLowerCase().replace(/_?base$/, ''));
  }

  function matchesRoots(vehicle, roots) {
    const itemname = String(vehicle.itemname || '').toLowerCase();
    return roots.some(root => itemname.startsWith(root));
  }

  function vehicleCategory(variants) {
    const airRoots = categoryRoots(/heli|air/i);
    const waterRoots = categoryRoots(/boat|water/i);
    if (variants.some(vehicle => matchesRoots(vehicle, airRoots))) return 'air';
    if (variants.some(vehicle => matchesRoots(vehicle, waterRoots))) return 'water';
    return 'ground';
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
    const attachmentMaps = variants.map(vehicle => {
      const items = new Map();
      (vehicle.attachmentItems || []).forEach(item => {
        const key = item.colorGroup || item.itemname;
        if (key && item.itemname && !items.has(key)) items.set(key, item.itemname);
      });
      return items;
    });
    const commonAttachments = attachmentMaps.length
      ? [...attachmentMaps[0].keys()]
          .filter(key => attachmentMaps.every(items => items.has(key)))
          .map(key => attachmentMaps[0].get(key))
      : [];
    const cargoSets = variants.map(vehicle => new Set(vehicle.additionalCargoItems || []));
    const commonCargo = cargoSets.length
      ? [...cargoSets[0]].filter(item => cargoSets.every(items => items.has(item)))
      : [];
    return [...new Set([
      ...commonAttachments,
      ...commonCargo,
      ...(payload.cargoItemsWhenBuyingVehicle || [])
    ].filter(Boolean))];
  }

  function colorList(variants) {
    const list = document.createElement('div');
    list.className = 'sparky-color-list';
    list.replaceChildren(...variants.map(vehicle => {
      const color = document.createElement('span');
      color.className = 'sparky-color-chip';
      color.textContent = displayColor(vehicle.color);
      return color;
    }));
    return list;
  }

  function priceTiers(variants) {
    const tiers = new Map();
    variants.forEach(vehicle => {
      const key = [vehicle.buyCost, vehicle.sellPrice, vehicle.insuranceCost, vehicle.repaintCost].join('|');
      if (!tiers.has(key)) tiers.set(key, { sample: vehicle, variants: [] });
      tiers.get(key).variants.push(vehicle);
    });
    return [...tiers.values()];
  }

  function colorVariantDetails(variants) {
    const details = document.createElement('details');
    details.className = 'sparky-variants';
    const summary = document.createElement('summary');
    const tiers = priceTiers(variants);
    summary.textContent = tiers.length === 1
      ? `View ${variants.length} colors`
      : `View ${variants.length} colors in ${tiers.length} price tiers`;
    details.append(summary);

    if (tiers.length === 1) {
      details.append(colorList(variants));
      return details;
    }

    const tierList = document.createElement('div');
    tierList.className = 'sparky-tier-list';
    tiers.forEach((tier, index) => {
      const section = document.createElement('section');
      section.className = 'sparky-price-tier';
      const label = document.createElement('div');
      label.className = 'sparky-tier-label';
      label.textContent = `Price tier ${index + 1}`;
      const prices = document.createElement('dl');
      prices.className = 'sparky-tier-prices';
      addPriceRows(prices, [
        ['Purchase', operationPrice(tier.sample.buyCost, 'Not sold')],
        ['Sell body', operationPrice(tier.sample.sellPrice, 'Not accepted')],
        ['Insurance', operationPrice(tier.sample.insuranceCost, 'Not offered')],
        ['Repaint', operationPrice(tier.sample.repaintCost, 'Not offered')]
      ]);
      section.append(label, prices, colorList(tier.variants));
      tierList.append(section);
    });
    details.append(tierList);
    return details;
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
      ['Purchase', priceRange(group.variants, 'buyCost', 'Not sold')],
      ['Sell body', priceRange(group.variants, 'sellPrice', 'Not accepted')],
      ['Insurance', priceRange(group.variants, 'insuranceCost', 'Not offered')],
      ['Repaint', priceRange(group.variants, 'repaintCost', 'Not offered')]
    ]);
    card.append(title, variantCount, prices);

    const included = includedItems(group.variants);
    if (included.length) {
      const details = document.createElement('details');
      details.className = 'sparky-included';
      const summary = document.createElement('summary');
      summary.textContent = `Included equipment (${included.length})`;
      const line = document.createElement('p');
      line.textContent = `Included: ${included.map(clean).join(', ')}`;
      details.append(summary, line);
      card.append(details);
    }

    if (group.variants.length === 1) {
      const color = document.createElement('div');
      color.className = 'sparky-single-color';
      color.textContent = displayColor(group.variants[0].color);
      card.append(color);
    } else {
      card.append(colorVariantDetails(group.variants));
    }
    return card;
  }

  function categorySection(category, groups) {
    const section = document.createElement('section');
    section.className = 'sparky-category-section';
    section.dataset.category = category;
    const heading = document.createElement('div');
    heading.className = 'sparky-category-heading';
    const title = document.createElement('h3');
    title.textContent = categoryLabels[category];
    const count = document.createElement('span');
    count.textContent = `${groups.length} model${groups.length === 1 ? '' : 's'}`;
    heading.append(title, count);
    const grid = document.createElement('div');
    grid.className = 'sparky-grid';
    grid.replaceChildren(...groups.map(vehicleCard));
    section.append(heading, grid);
    return section;
  }

  function updateCategoryButtons(groups) {
    const counts = Object.fromEntries(categoryOrder.map(category => [
      category,
      groups.filter(group => group.category === category).length
    ]));
    root.querySelectorAll('[data-category-filter]').forEach(button => {
      const category = button.dataset.categoryFilter;
      const active = category === selectedCategory;
      const count = category === 'all' ? groups.length : counts[category];
      button.classList.toggle('active', active);
      button.setAttribute('aria-pressed', String(active));
      const countEl = button.querySelector('[data-category-count]');
      if (countEl) countEl.textContent = String(count || 0);
    });
  }

  function render() {
    const query = root.querySelector('[data-search]').value.trim().toLowerCase();
    const listedVehicles = payload.vehicles.filter(isListedVehicle);
    const groups = groupVehicles(listedVehicles);
    const searched = groups.filter(group => !query || group.variants.some(vehicle =>
      [group.name, vehicle.groupName, vehicle.itemname, vehicle.color]
        .join(' ')
        .toLowerCase()
        .includes(query)
    ));
    const visible = selectedCategory === 'all'
      ? searched
      : searched.filter(group => group.category === selectedCategory);
    updateCategoryButtons(groups);
    root.querySelector('[data-count]').textContent =
      `${visible.length} of ${groups.length} vehicle models | ${listedVehicles.length} listed color options`;
    const sections = categoryOrder
      .map(category => ({
        category,
        groups: visible.filter(group => group.category === category)
      }))
      .filter(section => section.groups.length)
      .map(section => categorySection(section.category, section.groups));
    if (!sections.length) {
      const empty = document.createElement('p');
      empty.className = 'sparky-empty';
      empty.textContent = 'No vehicles match this search and category.';
      sections.push(empty);
    }
    root.querySelector('[data-list]').replaceChildren(...sections);
  }

  fetch(`../../../data/live-market/sparky.json?v=${Date.now()}`, { cache: 'no-store' })
    .then(response => {
      if (!response.ok) throw Error(response.status);
      return response.json();
    })
    .then(data => {
      payload = data;
      const listedVehicles = data.vehicles.filter(isListedVehicle);
      const modelCount = groupVehicles(listedVehicles).length;
      root.querySelector('[data-status]').textContent =
        `Live configuration | ${modelCount} available vehicle models | ${listedVehicles.length} listed color options`;
      const garageGroups = data.garageGroups || [];
      const garageAccessIsFree = garageGroups.length > 0 && garageGroups.every(group =>
        Number(group.costDeposit) === 0 && Number(group.costWithdraw) === 0);
      const rules = [
        garageAccessIsFree
          ? 'Garage deposits and withdrawals cost $0.'
          : 'Deposit and withdrawal fees vary by garage.',
        data.impound?.impoundRuinedVehicles && data.impound?.ruinedVehiclesRequireVehicleInsurance
          ? 'Insurance is required to recover a ruined vehicle.'
          : 'Ruined-vehicle recovery is not currently protected by required insurance.',
        'Repair fees still apply; players pay for repairs performed on their vehicles.'
      ];
      const ruleList = root.querySelector('[data-networks]');
      ruleList.replaceChildren(...rules.map(rule => {
        const item = document.createElement('li');
        item.textContent = rule;
        return item;
      }));
      root.querySelector('[data-search]').addEventListener('input', render);
      root.querySelectorAll('[data-category-filter]').forEach(button => {
        button.addEventListener('click', () => {
          selectedCategory = button.dataset.categoryFilter;
          render();
        });
      });
      render();
    })
    .catch(() => {
      root.querySelector('[data-status]').textContent =
        'Live Sparky configuration is temporarily unavailable.';
    });
})();

