(function () {
  var now = Date.now();
  document.querySelectorAll('[data-bounty-hunt]').forEach(function (event) {
    var start = Date.parse(event.getAttribute('data-event-start'));
    var end = Date.parse(event.getAttribute('data-event-end'));
    var badge = event.querySelector('[data-bounty-status]');
    if (!badge || !Number.isFinite(start) || !Number.isFinite(end)) return;
    var state = now < start ? 'upcoming' : now < end ? 'live' : 'closed';
    badge.classList.remove('event-status-upcoming', 'event-status-live', 'event-status-closed');
    badge.classList.add('event-status-' + state);
    badge.innerHTML = '<i></i> ' + (state === 'upcoming' ? 'Upcoming event' : state === 'live' ? 'Live event' : 'Closed event');
    if (state === 'closed' && event.id === 'bigguns-bounty-hunt-card') {
      var pastList = document.getElementById('past-event-list');
      if (pastList) pastList.prepend(event);
    }
  });
})();
