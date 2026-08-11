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

  function money(value) {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: cfg.currency || 'USD',
      maximumFractionDigits: 0
    }).format(value);
  }

  function escapeHtml(value) {
    return String(value).replace(/[&<>'"]/g, function (character) {
      return {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        "'": '&#39;',
        '"': '&quot;'
      }[character];
    });
  }

  function itemMarkup(item) {
    var direction = item.mode === 'buy' ? cfg.traderName + ' buys' : cfg.traderName + ' sells';
    var directionClass = item.mode === 'buy' ? 'buys' : 'sells';

    return '<article class="catalogue-item">' +
      '<div>' +
        '<div class="catalogue-name">' + escapeHtml(item.name) + '</div>' +
        '<div class="catalogue-class">' + escapeHtml(item.className) + '</div>' +
      '</div>' +
      '<div class="catalogue-meta">' +
        '<span class="catalogue-direction ' + directionClass + '">' + escapeHtml(direction) + '</span>' +
        '<span class="catalogue-price">' + money(item.price) + '</span>' +
      '</div>' +
    '</article>';
  }

  function render() {
    var query = search ? search.value.trim().toLowerCase() : '';

    var rows = cfg.items.filter(function (item) {
      var matchesFilter = active === 'all' || item.category === active || item.mode === active;
      var haystack = [item.name, item.className, item.category].join(' ').toLowerCase();
      var matchesSearch = !query || haystack.indexOf(query) !== -1;
      return matchesFilter && matchesSearch;
    });

    count.textContent = rows.length + ' item' + (rows.length === 1 ? '' : 's');
    empty.style.display = rows.length ? 'none' : 'block';

    var grouped = {};
    rows.forEach(function (item) {
      if (!grouped[item.category]) grouped[item.category] = [];
      grouped[item.category].push(item);
    });

    var categoryOrder = [];
    cfg.items.forEach(function (item) {
      if (categoryOrder.indexOf(item.category) === -1) categoryOrder.push(item.category);
    });

    var visibleCategories = categoryOrder.filter(function (category) {
      return grouped[category] && grouped[category].length;
    });

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
