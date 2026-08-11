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

    list.innerHTML = rows.map(function (item) {
      var direction = item.mode === 'buy' ? cfg.traderName + ' buys' : cfg.traderName + ' sells';
      var directionClass = item.mode === 'buy' ? 'buys' : 'sells';

      return '<article class="catalogue-item">' +
        '<div>' +
          '<div class="catalogue-name">' + item.name + '</div>' +
          '<div class="catalogue-class">' + item.className + '</div>' +
        '</div>' +
        '<div class="catalogue-meta">' +
          '<span class="catalogue-category">' + item.category + '</span>' +
          '<span class="catalogue-direction ' + directionClass + '">' + direction + '</span>' +
          '<span class="catalogue-price">' + money(item.price) + '</span>' +
        '</div>' +
      '</article>';
    }).join('');

    filters.forEach(function (button) {
      button.classList.toggle('active', button.dataset.catalogueFilter === active);
    });
  }

  if (search) {
    search.addEventListener('input', render);
  }

  filters.forEach(function (button) {
    button.addEventListener('click', function () {
      active = button.dataset.catalogueFilter;
      render();
    });
  });

  render();
});
