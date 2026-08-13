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
    return money(values[0]) + ' â€“ ' + money(values[values.length - 1]);
  }

  function titleWords(value) {
    return String(value || 'Default')
      .replace(/[_-]+/g, ' ')
      .replace(/\b\w/g, function (letter) { return letter.toUpperCase(); });
  }

  function groupDrippyItems(items) {
    if (!cfg.groupDrippyVariants) return items;
    var styles = [
      ['drip_adidascasual_', 'Adidas Casual'],
      ['drip_adidasyeezy350_', 'Adidas Yeezy 350'],
      ['drip_adidasyeezy750_', 'Adidas Yeezy 750'],
      ['drip_adidasyeezyslides_', 'Adidas Yeezy Slides'],
      ['drip_crocsocks_relaxed_', 'Crocs with Socks â€” Relaxed'],
      ['drip_crocsocks_sport_', 'Crocs with Socks â€” Sport'],
      ['drip_crocs_relaxed_', 'Crocs â€” Relaxed'],
      ['drip_crocs_sport_', 'Crocs â€” Sport'],
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
    var grouped = {};
    var standalone = [];
    items.forEach(function (item) {
      if (item.category !== 'Drippy Sneakers') {
        standalone.push(item);
        return;
      }
      var className = String(item.className || '').toLowerCase();
      var style = styles.find(function (entry) { return className.indexOf(entry[0]) === 0; });
      if (!style) {
        standalone.push(item);
        return;
      }
      if (!grouped[style[0]]) grouped[style[0]] = {name:style[1], variants:[]};
      var variant = Object.assign({}, item);
      variant.variantName = titleWords(className.slice(style[0].length));
      grouped[style[0]].variants.push(variant);
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
        className: group.variants.length + ' listed styles',
        category: first.category,
        traderSells: first.traderSells,
        traderBuys: first.traderBuys,
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
        escapeHtml(prices.join(' â€¢ ')) + '</strong></div>';
    }).join('');
    return '<details class="catalogue-variants"><summary>View ' + item.variants.length +
      ' styles and exact prices</summary><div class="catalogue-variant-list">' + rows + '</div></details>';
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
    var allRows = groupDrippyItems(cfg.items);
    var rows = allRows.filter(function (item) {
      var variantText = (item.variants || []).map(function (variant) {
        return [variant.name, variant.className, variant.variantName].join(' ');
      }).join(' ');
      var haystack = [item.name, item.className, item.category, variantText].join(' ').toLowerCase();
      return !query || haystack.indexOf(query) !== -1;
    });

    if (count) {
      count.textContent = rows.length + ' product' + (rows.length === 1 ? '' : 's');
      if (cfg.groupDrippyVariants && !query) count.textContent += ' â€¢ ' + cfg.items.length + ' live item variants';
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

