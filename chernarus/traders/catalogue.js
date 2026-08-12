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

  var guidanceText = 'Inventory is grouped by market category. Searching automatically opens the matching category, and the transaction filters work across all categories.';
  var note = root.querySelector('.catalogue-note');
  if (!note) {
    note = document.createElement('p');
    note.className = 'catalogue-note';
  }
  note.textContent = guidanceText;
  if (search) search.insertAdjacentElement('afterend', note);

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
    if (usesInheritedBuyback(item)) {
      return {sells:true, buys:true};
    }
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

  function itemMarkup(item) {
    var state = permissions(item);
    var both = state.sells && state.buys;
    var direction = both ? 'Buys & Sells' : (state.buys ? cfg.traderName + ' buys' : cfg.traderName + ' sells');
    var directionClass = both ? 'both' : (state.buys ? 'buys' : 'sells');
    var prices = '';

    if (both) {
      prices = '<div class="catalogue-price-pair">' +
        '<span><small>Buy from trader</small><strong>' + money(purchasePrice(item)) + '</strong></span>' +
        '<span><small>Sell to trader</small><strong>' + money(resalePrice(item)) + '</strong></span>' +
      '</div>';
    } else {
      var value = state.sells ? purchasePrice(item) : resalePrice(item);
      var label = state.sells ? 'Buy from trader' : 'Sell to trader';
      prices = '<div class="catalogue-price-pair catalogue-price-single">' +
        '<span><small>' + label + '</small><strong>' + money(value) + '</strong></span>' +
      '</div>';
    }

    return '<article class="catalogue-item">' +
      '<div>' +
        '<div class="catalogue-name">' + escapeHtml(item.name) + '</div>' +
        '<div class="catalogue-class">' + escapeHtml(item.className) + '</div>' +
      '</div>' +
      '<div class="catalogue-meta">' +
        '<span class="catalogue-direction ' + directionClass + '">' + escapeHtml(direction) + '</span>' +
        prices +
      '</div>' +
    '</article>';
  }

  function matchesActive(item) {
    var state = permissions(item);
    if (active === 'all') return true;
    if (active === 'purchase') return state.sells;
    if (active === 'sale') return state.buys;
    if (active === 'both') return state.sells && state.buys;
    return item.category === active;
  }

  function render() {
    var query = search ? search.value.trim().toLowerCase() : '';

    var rows = cfg.items.filter(function (item) {
      var haystack = [item.name, item.className, item.category].join(' ').toLowerCase();
      return matchesActive(item) && (!query || haystack.indexOf(query) !== -1);
    });

    count.textContent = rows.length + ' item' + (rows.length === 1 ? '' : 's');
    empty.style.display = rows.length ? 'none' : 'block';

    var grouped = {};
    rows.forEach(function (item) {
      if (!grouped[item.category]) grouped[item.category] = [];
      grouped[item.category].push(item);
    });

    Object.keys(grouped).forEach(function (category) {
      grouped[category].sort(function (a, b) {
        return compareText(a.name, b.name) || compareText(a.className, b.className);
      });
    });

    var visibleCategories = Object.keys(grouped).sort(compareText);

    list.innerHTML = visibleCategories.map(function (category) {
      var items = grouped[category];
      var shouldOpen = Boolean(query) || active === category || visibleCategories.length === 1;
      return '<details class="catalogue-group"' + (shouldOpen ? ' open' : '') + '>' +
        '<summary class="catalogue-group-summary">' +
          '<span class="catalogue-group-title">' + escapeHtml(category) + '</span>' +
          '<span class="catalogue-group-count">' + items.length + ' item' + (items.length === 1 ? '' : 's') + '</span>' +
        '</summary>' +
        '<div class="catalogue-group-items">' + items.map(itemMarkup).join('') + '</div>' +
      '</details>';
    }).join('');

    filters.forEach(function (button) {
      button.classList.toggle('active', button.dataset.catalogueFilter === active);
    });
  }

  if (search) search.addEventListener('input', render);
  filters.forEach(function (button) {
    button.addEventListener('click', function () {
      active = button.dataset.catalogueFilter;
      render();
    });
  });
  render();
});
