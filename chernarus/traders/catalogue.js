document.addEventListener('DOMContentLoaded', function () {
  var cfg = window.traderCatalogue;
  if (!cfg) return;

  var root = document.getElementById('traderCatalogue');
  if (!root) return;

  var search = root.querySelector('[data-catalogue-search]');
  var list = root.querySelector('[data-catalogue-list]');
  var empty = root.querySelector('[data-catalogue-empty]');
  var count = root.querySelector('[data-catalogue-count]');
  var filters = Array.prototype.slice.call(root.querySelectorAll('[data-catalogue-filter]'));
  var active = 'all';

  // Keep the catalogue focused on the inventory itself. Transaction direction
  // and the appropriate buy/sell price are shown on each individual item.
  filters.forEach(function (button) { button.style.display = 'none'; });
  var note = root.querySelector('.catalogue-note');
  if (note) note.style.display = 'none';
  var existingSummary = root.querySelector('.catalogue-transaction-summary');
  if (existingSummary) existingSummary.remove();

  function money(value) {
    if (cfg.currencyLabel) {
      return new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 }).format(value) + ' ' + cfg.currencyLabel;
    }
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: cfg.currency || 'USD',
      maximumFractionDigits: 0
    }).format(value);
  }

  function escapeHtml(value) {
    return String(value).replace(/[&<>'\"]/g, function (character) {
      return {'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','\"':'&quot;'}[character];
    });
  }

  function compareText(a, b) {
    return String(a).localeCompare(String(b), 'en', {sensitivity:'base', numeric:true});
  }

  function usesInheritedBuyback(item) {
    if (!cfg.inheritedCategoryBuyback || item.mode !== 'sell') return false;
    var excluded = cfg.buybackExcludedCategories || [];
    return excluded.indexOf(item.category) === -1;
  }

  function permissions(item) {
    if (typeof item.traderSells === 'boolean' || typeof item.traderBuys === 'boolean') {
      return {sells:Boolean(item.traderSells), buys:Boolean(item.traderBuys)};
    }
    if (usesInheritedBuyback(item)) return {sells:true, buys:true};
    return {sells:item.mode === 'sell', buys:item.mode === 'buy'};
  }

  function purchasePrice(item) {
    return item.buyPrice != null ? item.buyPrice : (item.mode === 'sell' ? item.price : null);
  }

  function resalePrice(item) {
    if (item.sellPrice != null) return item.sellPrice;
    if (item.mode === 'buy') return item.price;
    if (usesInheritedBuyback(item)) {
      var percent = cfg.inheritedSellPercent != null ? cfg.inheritedSellPercent : 75;
      return Math.round((purchasePrice(item) || 0) * (percent / 100));
    }
    return null;
  }

  function transactionValue(item, type) {
    return type === 'purchase' ? purchasePrice(item) : resalePrice(item);
  }

  function transactionPrice(item, type) {
    var variants = item.variants || [item];
    var values = variants.map(function (variant) { return transactionValue(variant, type); })
      .filter(function (value) { return value != null; })
      .sort(function (a, b) { return a - b; });
    if (!values.length) return '';
    if (values[0] === values[values.length - 1]) return money(values[0]);
    return money(values[0]) + ' – ' + money(values[values.length - 1]);
  }

  function titleWords(value) {
    return String(value || 'Default')
      .replace(/[_-]+/g, ' ')
      .replace(/\b\w/g, function (letter) { return letter.toUpperCase(); });
  }

  function collectableFamily(item) {
    var className = String(item.className || '').toLowerCase();
    var styles = [
      ['drip_adidascasual_', 'Adidas Casual'],
      ['drip_adidasyeezy350_', 'Adidas Yeezy 350'],
      ['drip_adidasyeezy750_', 'Adidas Yeezy 750'],
      ['drip_adidasyeezyslides_', 'Adidas Yeezy Slides'],
      ['drip_crocsocks_relaxed_', 'Crocs with Socks — Relaxed'],
      ['drip_crocsocks_sport_', 'Crocs with Socks — Sport'],
      ['drip_crocs_relaxed_', 'Crocs — Relaxed'],
      ['drip_crocs_sport_', 'Crocs — Sport'],
      ['drip_drippypoo_', 'Drippy Poo'],
      ['drip_hobbitfeet_', 'Hobbit Feet'],
      ['drip_mschfboots_', 'MSCHF Boots'],
      ['drip_nikeairforce_1_', 'Nike Air Force 1'],
      ['drip_nikeairjordan_1_', 'Nike Air Jordan 1'],
      ['drip_nikeairjordan_4_', 'Nike Air Jordan 4'],
      ['drip_nikeairyeezy_', 'Nike Air Yeezy'],
      ['drip_nikeairzoom_', 'Nike Air Zoom'],
      ['drip_nikemag_', 'Nike MAG'],
      ['drip_pampaboots_', 'Pampa Boots'],
      ['drip_piggyslippers_', 'Piggy Slippers'],
      ['drip_ragezrlegend_', 'Rage ZR Legend'],
      ['drip_sandals_', 'Sandals'],
      ['drip_socksandals_', 'Socks & Sandals'],
      ['drip_socks_', 'Socks'],
      ['drip_timberlandboots_', 'Timberland Boots'],
      ['drip_vansslipon_', 'Vans Slip-On']
    ];
    var style = styles.find(function (entry) { return className.indexOf(entry[0]) === 0; });
    if (style) {
      return {key:style[0], name:style[1], variantName:titleWords(className.slice(style[0].length)), variantLabel:'styles'};
    }

    var match;
    var paragonNames = {
      axe:'Axes', canister:'Canisters', crystal:'Crystals', cube:'Cubes',
      diamond:'Diamonds', gameboy:'Game Boys', glowrock:'Glow Rocks',
      kaws:'KAWS Figures', skull:'Skulls', sword:'Swords',
      triangle:'Triangles', trophy:'Trophies'
    };
    match = className.match(/^paragon_(axe|canister|crystal|cube|diamond|gameboy|glowrock|kaws|skull|sword|triangle|trophy)_(.+)$/);
    if (match) {
      return {key:'paragon_' + match[1], name:paragonNames[match[1]], variantName:titleWords(match[2]), variantLabel:'variants'};
    }
    if (className === 'paragon_goldbar' || className === 'paragon_goldbar_stack') {
      return {key:'paragon_gold_bars', name:'Gold Bars', variantName:className.endsWith('_stack') ? 'Stack' : 'Single Bar', variantLabel:'sizes'};
    }
    if (className === 'paragon_silverbar' || className === 'paragon_silver_stack') {
      return {key:'paragon_silver_bars', name:'Silver Bars', variantName:className.endsWith('_stack') ? 'Stack' : 'Single Bar', variantLabel:'sizes'};
    }

    match = className.match(/^pokemoncard_sealedbox(\d+)$/);
    if (match) return {key:'pokemon_sealed_boxes', name:'Sealed Pokémon Collection Boxes', variantName:'Box ' + Number(match[1]), variantLabel:'boxes'};

    match = className.match(/^vyse_labubu_(.+)$/);
    if (match) return {key:'vyse_labubu', name:'Labubu Figures', variantName:titleWords(match[1]), variantLabel:'figures'};
    if (className === 'vyse_monster_labubu') return {key:'vyse_labubu', name:'Labubu Figures', variantName:'Monster', variantLabel:'figures'};
    match = className.match(/^vyse_lego_(.+)$/);
    if (match) return {key:'vyse_lego', name:'LEGO Figures', variantName:titleWords(match[1]), variantLabel:'figures'};
    match = className.match(/^vyse_pokemon_(.+)$/);
    if (match) return {key:'vyse_pokemon_balls', name:'Pokémon Balls', variantName:titleWords(match[1]), variantLabel:'designs'};
    match = className.match(/^vyse_ps4_(.+)$/);
    if (match) {
      var ps4Names = {
        godofwar:'God of War', grandtheftautov:'Grand Theft Auto V',
        horizonzerodawn:'Horizon Zero Dawn', madmax:'Mad Max', rdr2:'Red Dead Redemption 2',
        shadowofthecolossus:'Shadow of the Colossus', spiderman:'Spider-Man',
        thelastofus:'The Last of Us', uncharted4:'Uncharted 4', untildawn:'Until Dawn'
      };
      return {key:'vyse_ps4_games', name:'PlayStation 4 Games', variantName:ps4Names[match[1]] || titleWords(match[1]), variantLabel:'games'};
    }
    match = className.match(/^vyse_yugioh_card_(\d+)$/);
    if (match) return {key:'vyse_yugioh_cards', name:'Yu-Gi-Oh! Cards', variantName:'Card ' + Number(match[1]), variantLabel:'cards'};

    if (item.category === 'Fallout Bobbleheads' && className !== 'dlt_falloutz_bobbleheadstandkit') {
      return {
        key:'fallout_bobbleheads',
        name:'Fallout Bobbleheads',
        variantName:String(item.name).replace(/^Fallout /, '').replace(/ Bobblehead$/, ''),
        variantLabel:'bobbleheads'
      };
    }
    if (item.category === 'Fallout Nuka-Cola' && className !== 'dlt_falloutz_nukacolarackkit') {
      return {
        key:'fallout_nuka_cola',
        name:'Fallout Nuka-Cola',
        variantName:String(item.name).replace(/^Fallout Nuka-Cola /, ''),
        variantLabel:'flavors'
      };
    }

    match = className.match(/^arrakis_condom_(.+)$/);
    if (match) {
      var condomNames = {donkeydick:'Donkey', extralarge:'Extra Large', extrasmall:'Extra Small', large:'Large', medium:'Medium', micro:'Micro', small:'Small'};
      return {key:'adult_condoms', name:'Condoms', variantName:condomNames[match[1]] || titleWords(match[1]), variantLabel:'sizes'};
    }
    match = className.match(/^arrakisbuttplug(.+)$/);
    if (match) return {key:'adult_butt_plugs', name:'Butt Plugs', variantName:titleWords(match[1]), variantLabel:'colors'};
    match = className.match(/^arrakis(.+)fleshlight$/);
    if (match) {
      var fleshlightNames = {black:'Black', brown:'Brown', pink:'Pink', bluewaffle:'Blue Waffle', cold:'Cold'};
      return {key:'adult_fleshlights', name:'Fleshlights', variantName:fleshlightNames[match[1]] || titleWords(match[1]), variantLabel:'styles'};
    }
    match = className.match(/^arrakisxmasdildo([12])half$/);
    if (match) return {key:'adult_dildos_half', name:'Half-Size Dildos', variantName:'Christmas ' + match[1], variantLabel:'styles'};
    match = className.match(/^arrakisxmasdildo([12])mega$/);
    if (match) return {key:'adult_dildos_mega', name:'Mega Dildos', variantName:'Christmas ' + match[1], variantLabel:'styles'};
    match = className.match(/^arrakisxmasdildo([12])$/);
    if (match) return {key:'adult_dildos', name:'Dildos', variantName:'Christmas ' + match[1], variantLabel:'styles'};
    match = className.match(/^arrakis(.+)dildohalf$/);
    if (match) return {key:'adult_dildos_half', name:'Half-Size Dildos', variantName:titleWords(match[1]), variantLabel:'styles'};
    match = className.match(/^arrakis(.+)dildomega$/);
    if (match) return {key:'adult_dildos_mega', name:'Mega Dildos', variantName:titleWords(match[1]), variantLabel:'styles'};
    match = className.match(/^arrakisdildopresent(.+)$/);
    if (match) return {key:'adult_dildo_presents', name:'Gift-Wrapped Dildos', variantName:titleWords(match[1]), variantLabel:'styles'};
    match = className.match(/^arrakis(.+)dildo$/);
    if (match) return {key:'adult_dildos', name:'Dildos', variantName:titleWords(match[1]), variantLabel:'styles'};
    match = className.match(/^arrakisprisonwallet(.+)$/);
    if (match) {
      var walletSizes = {dd:'Double D', el:'Extra Large', l:'Large', m:'Medium', mp:'Medium Plus', s:'Small', xs:'Extra Small'};
      return {key:'adult_prison_wallets', name:'Prison Wallets', variantName:walletSizes[match[1]] || match[1].toUpperCase(), variantLabel:'sizes'};
    }
    if (className === 'arrakissoap' || className === 'arrakissoappresent') {
      return {key:'adult_soap', name:'Soap', variantName:className.endsWith('present') ? 'Gift-Wrapped' : 'Standard', variantLabel:'versions'};
    }

    match = className.match(/^pokemoncard_box(\d+)$/);
    if (match) return {key:'storage_pokemon_boxes', name:'Pokémon Card Storage Boxes', variantName:'Box ' + Number(match[1]), variantLabel:'boxes'};
    match = className.match(/^fallout_lunchbox_(.+)$/);
    if (match) return {key:'storage_fallout_lunchboxes', name:'Fallout Lunchboxes', variantName:titleWords(match[1]), variantLabel:'designs'};

    return null;
  }

  function groupCollectableItems(items) {
    if (!cfg.groupCollectableVariants && !cfg.groupDrippyVariants) return items;
    var grouped = {};
    var standalone = [];
    items.forEach(function (item) {
      var family = collectableFamily(item);
      if (!family) {
        standalone.push(item);
        return;
      }
      var key = item.category + '|' + family.key;
      if (!grouped[key]) grouped[key] = {name:family.name, variantLabel:family.variantLabel, variants:[]};
      var variant = Object.assign({}, item);
      variant.variantName = family.variantName;
      grouped[key].variants.push(variant);
    });
    Object.keys(grouped).forEach(function (key) {
      var group = grouped[key];
      group.variants.sort(function (a, b) { return compareText(a.variantName, b.variantName); });
      if (group.variants.length === 1) {
        standalone.push(group.variants[0]);
        return;
      }
      var first = group.variants[0];
      standalone.push({
        name: group.name,
        className: group.variants.length + ' listed ' + group.variantLabel,
        category: first.category,
        traderSells: first.traderSells,
        traderBuys: first.traderBuys,
        variantLabel: group.variantLabel,
        variants: group.variants
      });
    });
    return standalone;
  }

  function variantMarkup(item) {
    if (!item.variants) return '';
    var rows = item.variants.map(function (variant) {
      var state = permissions(variant);
      var prices = [];
      if (state.sells) prices.push('Buy ' + money(purchasePrice(variant)));
      if (state.buys) prices.push('Sell ' + money(resalePrice(variant)));
      return '<div class="catalogue-variant-row"><span>' + escapeHtml(variant.variantName) + '</span><strong>' +
        escapeHtml(prices.join(' • ')) + '</strong></div>';
    }).join('');
    return '<details class="catalogue-variants"><summary>View ' + item.variants.length +
      ' ' + escapeHtml(item.variantLabel || 'variants') + ' and exact prices</summary><div class="catalogue-variant-list">' + rows + '</div></details>';
  }

  function itemMarkup(item) {
    var state = permissions(item);
    var both = state.sells && state.buys;
    var direction = both ? 'Buys & Sells' : (state.buys ? cfg.traderName + ' buys' : cfg.traderName + ' sells');
    var directionClass = both ? 'both' : (state.buys ? 'buys' : 'sells');
    var prices = '';

    if (both) {
      prices = '<div class="catalogue-price-pair">' +
        '<span><small>Buy from trader</small><strong>' + transactionPrice(item, 'purchase') + '</strong></span>' +
        '<span><small>Sell to trader</small><strong>' + transactionPrice(item, 'resale') + '</strong></span>' +
      '</div>';
    } else {
      var type = state.sells ? 'purchase' : 'resale';
      var label = state.sells ? 'Buy from trader' : 'Sell to trader';
      prices = '<div class="catalogue-price-pair catalogue-price-single">' +
        '<span><small>' + label + '</small><strong>' + transactionPrice(item, type) + '</strong></span>' +
      '</div>';
    }

    return '<article class="catalogue-item">' +
      '<div><div class="catalogue-name">' + escapeHtml(item.name) + '</div>' +
      '<div class="catalogue-class">' + escapeHtml(item.className) + '</div></div>' +
      '<div class="catalogue-meta"><span class="catalogue-direction ' + directionClass + '">' + escapeHtml(direction) + '</span>' + prices + '</div>' + variantMarkup(item) +
    '</article>';
  }

  function render() {
    var query = search ? search.value.trim().toLowerCase() : '';
    var allRows = groupCollectableItems(cfg.items);
    var rows = allRows.filter(function (item) {
      var variantText = (item.variants || []).map(function (variant) {
        return [variant.name, variant.className, variant.variantName].join(' ');
      }).join(' ');
      var haystack = [item.name, item.className, item.category, variantText].join(' ').toLowerCase();
      return !query || haystack.indexOf(query) !== -1;
    });

    if (count) {
      var groupedCatalogue = cfg.groupCollectableVariants || cfg.groupDrippyVariants;
      var noun = groupedCatalogue ? 'product' : 'item';
      count.textContent = rows.length + ' ' + noun + (rows.length === 1 ? '' : 's');
      if (groupedCatalogue && !query) count.textContent += ' • ' + cfg.items.length + ' live item variants';
    }
    empty.style.display = rows.length ? 'none' : 'block';

    var grouped = {};
    rows.forEach(function (item) {
      if (!grouped[item.category]) grouped[item.category] = [];
      grouped[item.category].push(item);
    });
    Object.keys(grouped).forEach(function (category) {
      grouped[category].sort(function (a, b) { return compareText(a.name, b.name) || compareText(a.className, b.className); });
    });

    var visibleCategories = Object.keys(grouped).sort(compareText);
    list.innerHTML = visibleCategories.map(function (category) {
      var items = grouped[category];
      var shouldOpen = Boolean(query) || visibleCategories.length === 1;
      return '<details class="catalogue-group"' + (shouldOpen ? ' open' : '') + '>' +
        '<summary class="catalogue-group-summary"><span class="catalogue-group-title">' + escapeHtml(category) + '</span>' +
        '<span class="catalogue-group-count">' + items.length + ' item' + (items.length === 1 ? '' : 's') + '</span></summary>' +
        '<div class="catalogue-group-items">' + items.map(itemMarkup).join('') + '</div></details>';
    }).join('');
  }

  if (search) search.addEventListener('input', render);
  render();
});

