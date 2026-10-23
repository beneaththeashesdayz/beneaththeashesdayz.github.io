(() => {
  const DATA_URL = '../../../data/live-market/p2p-listings.json';
  const root = document.querySelector('[data-p2p-market]');
  if (!root) return;

  const listEl = root.querySelector('[data-p2p-list]');
  const searchEl = root.querySelector('[data-p2p-search]');
  const sortEl = root.querySelector('[data-p2p-sort]');
  const countEl = root.querySelector('[data-p2p-count]');
  const syncEl = root.querySelector('[data-p2p-synced]');
  const statusEl = root.querySelector('[data-p2p-status]');
  const emptyEl = root.querySelector('[data-p2p-empty]');
  const feeEls = document.querySelectorAll('[data-p2p-fee]');
  const durationEls = document.querySelectorAll('[data-p2p-duration]');

  let payload = null;

  const conditionLabels = {
    0: 'Pristine',
    1: 'Worn',
    2: 'Damaged',
    3: 'Badly Damaged',
    4: 'Ruined'
  };

  function money(value) {
    const number = Number(value);
    if (!Number.isFinite(number)) return '$0';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 0
    }).format(number);
  }

  function formatTimestamp(value) {
    const date = value ? new Date(value) : null;
    if (!date || Number.isNaN(date.getTime())) return 'Unknown';
    return new Intl.DateTimeFormat(undefined, {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit'
    }).format(date);
  }

  function durationLabel(seconds) {
    const total = Number(seconds);
    if (!Number.isFinite(total) || total <= 0) return '7 days';
    const days = Math.round(total / 86400);
    return days === 1 ? '1 day' : `${days} days`;
  }

  function timeLeft(expiresAt) {
    if (!expiresAt) return 'Unknown';
    const diff = new Date(expiresAt).getTime() - Date.now();
    if (!Number.isFinite(diff) || diff <= 0) return 'Expired';

    const minutes = Math.floor(diff / 60000);
    const days = Math.floor(minutes / 1440);
    const hours = Math.floor((minutes % 1440) / 60);
    const mins = minutes % 60;

    if (days > 0) return `${days}d ${hours}h`;
    if (hours > 0) return `${hours}h ${mins}m`;
    return `${Math.max(mins, 1)}m`;
  }

  function isActive(item) {
    if (!item.expiresAt) return true;
    const expiry = new Date(item.expiresAt).getTime();
    return Number.isFinite(expiry) ? expiry > Date.now() : true;
  }

  function text(parent, className, value) {
    const el = document.createElement('div');
    if (className) el.className = className;
    el.textContent = value;
    parent.appendChild(el);
    return el;
  }

  function detail(label, value) {
    const wrap = document.createElement('div');
    wrap.className = 'p2p-detail';
    text(wrap, 'p2p-detail-label', label);
    text(wrap, 'p2p-detail-value', value);
    return wrap;
  }

  function createListingCard(item) {
    const card = document.createElement('article');
    card.className = 'p2p-listing-card';
    card.dataset.key = item.key || '';

    const top = document.createElement('div');
    top.className = 'p2p-listing-top';

    const titleWrap = document.createElement('div');
    titleWrap.className = 'p2p-listing-title-wrap';
    text(titleWrap, 'p2p-listing-name', item.name || item.className || 'Unknown Item');
    if (item.className) text(titleWrap, 'p2p-listing-class', item.className);

    const price = document.createElement('div');
    price.className = 'p2p-listing-price';
    price.textContent = money(item.price);

    top.append(titleWrap, price);
    card.appendChild(top);

    const details = document.createElement('div');
    details.className = 'p2p-listing-details';
    details.append(
      detail('Seller', item.seller || 'Unknown Survivor'),
      detail('Condition', conditionLabels[Number(item.healthLevel)] || `Level ${item.healthLevel ?? '?'}`),
      detail('Time Left', timeLeft(item.expiresAt)),
      detail('Listed', formatTimestamp(item.listedAt))
    );
    card.appendChild(details);

    const included = Array.isArray(item.includedItems) ? item.includedItems : [];
    if (included.length) {
      const cargo = document.createElement('details');
      cargo.className = 'p2p-cargo';
      const summary = document.createElement('summary');
      summary.textContent = `${included.length} included item${included.length === 1 ? '' : 's'}`;
      cargo.appendChild(summary);

      const cargoList = document.createElement('ul');
      included.forEach(entry => {
        const li = document.createElement('li');
        const amount = Number(entry.quantity);
        const quantity = Number.isFinite(amount) && amount > 1 ? ` × ${Math.round(amount)}` : '';
        li.textContent = `${entry.name || entry.className || 'Item'}${quantity}`;
        cargoList.appendChild(li);
      });
      cargo.appendChild(cargoList);
      card.appendChild(cargo);
    }

    return card;
  }

  function currentListings() {
    if (!payload || !Array.isArray(payload.listings)) return [];
    const query = (searchEl?.value || '').trim().toLowerCase();
    let rows = payload.listings.filter(isActive);

    if (query) {
      rows = rows.filter(item => {
        const haystack = [item.name, item.className, item.seller]
          .filter(Boolean)
          .join(' ')
          .toLowerCase();
        return haystack.includes(query);
      });
    }

    const sort = sortEl?.value || 'expiring';
    rows.sort((a, b) => {
      if (sort === 'newest') return String(b.listedAt || '').localeCompare(String(a.listedAt || ''));
      if (sort === 'price-low') return Number(a.price || 0) - Number(b.price || 0);
      if (sort === 'price-high') return Number(b.price || 0) - Number(a.price || 0);
      if (sort === 'seller') return String(a.seller || '').localeCompare(String(b.seller || ''));
      return String(a.expiresAt || '9999').localeCompare(String(b.expiresAt || '9999'));
    });
    return rows;
  }

  function render() {
    if (!payload) return;
    const rows = currentListings();
    listEl.replaceChildren(...rows.map(createListingCard));

    const activeTotal = (payload.listings || []).filter(isActive).length;
    if (countEl) {
      countEl.textContent = searchEl?.value
        ? `${rows.length} of ${activeTotal} live listing${activeTotal === 1 ? '' : 's'}`
        : `${activeTotal} live listing${activeTotal === 1 ? '' : 's'}`;
    }

    if (emptyEl) emptyEl.hidden = rows.length !== 0;
  }

  async function load() {
    if (statusEl) statusEl.textContent = 'Loading live listings…';
    try {
      const response = await fetch(`${DATA_URL}?v=${Date.now()}`, { cache: 'no-store' });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      payload = await response.json();

      if (!Array.isArray(payload.listings)) payload.listings = [];
      if (syncEl) syncEl.textContent = `Last server sync: ${formatTimestamp(payload.syncedAt)}`;
      if (Number.isFinite(Number(payload.listingFeePercent))) {
        feeEls.forEach(el => { el.textContent = `${Number(payload.listingFeePercent)}%`; });
      }
      durationEls.forEach(el => { el.textContent = durationLabel(payload.maxListingTimeSeconds); });

      if (statusEl) {
        statusEl.textContent = payload.status === 'ok'
          ? 'Live server market feed'
          : 'Live feed is temporarily unavailable; showing the most recent published snapshot.';
        statusEl.classList.toggle('warning', payload.status !== 'ok');
      }
      render();
    } catch (error) {
      console.error('Unable to load P2P market data:', error);
      if (statusEl) {
        statusEl.textContent = 'Live listings could not be loaded right now.';
        statusEl.classList.add('warning');
      }
      if (countEl) countEl.textContent = 'Market feed unavailable';
      if (emptyEl) {
        emptyEl.hidden = false;
        emptyEl.textContent = 'No live market data is available at the moment. Try again shortly.';
      }
    }
  }

  searchEl?.addEventListener('input', render);
  sortEl?.addEventListener('change', render);
  setInterval(render, 60000);
  load();
})();
