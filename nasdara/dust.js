(() => {
  const initNasdaraDust = () => {
    if (!document.body.classList.contains('world-nasdara') || document.querySelector('.nasdara-dust')) return;

    document.querySelectorAll('.ember-field').forEach((field) => field.remove());

    if (!document.getElementById('nasdara-dust-style')) {
      const style = document.createElement('style');
      style.id = 'nasdara-dust-style';
      style.textContent = `
        .nasdara-dust {
          position: fixed;
          inset: 0;
          z-index: 0;
          overflow: hidden;
          pointer-events: none;
          contain: layout paint style;
        }
        .world-nasdara > header,
        .world-nasdara > main,
        .world-nasdara > footer {
          position: relative;
          z-index: 1;
        }
        .nasdara-dust__grain {
          position: absolute;
          left: var(--start-x);
          top: var(--start-y);
          width: var(--size);
          height: var(--size);
          border-radius: 999px;
          background: var(--tone);
          opacity: var(--opacity);
          animation: nasdara-sand-drift var(--duration) linear var(--delay) infinite;
          will-change: transform, opacity;
        }
        .nasdara-dust__gust {
          position: absolute;
          left: -35vw;
          top: var(--gust-y);
          width: var(--gust-width);
          height: var(--gust-height);
          border-radius: 50%;
          background: linear-gradient(90deg, transparent, rgba(225, 188, 120, .12), rgba(135, 99, 61, .08), transparent);
          filter: blur(7px);
          opacity: .5;
          animation: nasdara-gust var(--gust-duration) linear var(--gust-delay) infinite;
          will-change: transform, opacity;
        }
        @keyframes nasdara-sand-drift {
          0% { transform: translate3d(-24vw, 0, 0) rotate(.1deg); opacity: 0; }
          12% { opacity: var(--opacity); }
          86% { opacity: calc(var(--opacity) * .72); }
          100% { transform: translate3d(124vw, var(--slope), 0) rotate(.1deg); opacity: 0; }
        }
        @keyframes nasdara-gust {
          0% { transform: translate3d(-8vw, 0, 0) skewX(-12deg); opacity: 0; }
          18% { opacity: .45; }
          78% { opacity: .22; }
          100% { transform: translate3d(138vw, var(--gust-slope), 0) skewX(-12deg); opacity: 0; }
        }
        @media (prefers-reduced-motion: reduce) {
          .nasdara-dust__grain { animation: none; opacity: .12; }
          .nasdara-dust__gust { display: none; }
        }
      `;
      document.head.appendChild(style);
    }

    const dust = document.createElement('div');
    dust.className = 'nasdara-dust';
    dust.setAttribute('aria-hidden', 'true');

    const compact = window.matchMedia('(max-width: 760px)').matches;
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const grainCount = compact ? 14 : 28;
    const tones = ['#C69A52', '#E1BC78', '#87633D'];

    for (let i = 0; i < grainCount; i += 1) {
      const grain = document.createElement('i');
      grain.className = 'nasdara-dust__grain';
      grain.style.setProperty('--start-x', `${Math.random() * 100}%`);
      grain.style.setProperty('--start-y', `${Math.random() * 100}%`);
      grain.style.setProperty('--size', `${(1 + Math.random() * 2.2).toFixed(1)}px`);
      grain.style.setProperty('--tone', tones[i % tones.length]);
      grain.style.setProperty('--opacity', `${(.14 + Math.random() * .24).toFixed(2)}`);
      grain.style.setProperty('--duration', `${(20 + Math.random() * 22).toFixed(1)}s`);
      grain.style.setProperty('--delay', reducedMotion ? '0s' : `${(-Math.random() * 34).toFixed(1)}s`);
      grain.style.setProperty('--slope', `${((Math.random() - .5) * 18).toFixed(1)}vh`);
      dust.appendChild(grain);
    }

    const gustCount = compact ? 1 : 3;
    for (let i = 0; i < gustCount; i += 1) {
      const gust = document.createElement('b');
      gust.className = 'nasdara-dust__gust';
      gust.style.setProperty('--gust-y', `${18 + Math.random() * 68}%`);
      gust.style.setProperty('--gust-width', `${32 + Math.random() * 30}vw`);
      gust.style.setProperty('--gust-height', `${2 + Math.random() * 4}px`);
      gust.style.setProperty('--gust-duration', `${30 + Math.random() * 18}s`);
      gust.style.setProperty('--gust-delay', reducedMotion ? '0s' : `${(-Math.random() * 38).toFixed(1)}s`);
      gust.style.setProperty('--gust-slope', `${((Math.random() - .5) * 10).toFixed(1)}vh`);
      dust.appendChild(gust);
    }

    document.body.appendChild(dust);
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initNasdaraDust, { once: true });
  } else {
    initNasdaraDust();
  }
})();
