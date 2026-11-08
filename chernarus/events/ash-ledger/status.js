(function () {
  document.querySelectorAll('[data-ash-ledger]').forEach(function (event) {
    var end = Date.parse(event.getAttribute('data-event-end'));
    var badge = event.querySelector('[data-ledger-status]');
    if (!badge || !Number.isFinite(end) || Date.now() < end) return;
    badge.classList.remove('event-status-live');
    badge.classList.add('event-status-closed');
    badge.innerHTML = '<i></i> Closed event';
    if (event.id === 'ash-ledger-card') {
      var pastList = document.getElementById('past-event-list');
      if (pastList) pastList.prepend(event);
    }
  });
})();
