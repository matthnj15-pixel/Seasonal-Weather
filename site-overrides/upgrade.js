// Responsive enhancement layer for Seasonal Weather.
(() => {
  'use strict';
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const cards = [document.getElementById('hero-widget'), document.getElementById('preview-widget')].filter(Boolean);
  const current = name => document.querySelector(`[data-${name}].selected`)?.dataset[name];
  const names = { spring:'Spring',summer:'Summer',fall:'Autumn',winter:'Winter',sunny:'Sunny',partly:'Partly cloudy',cloudy:'Overcast',rain:'Rain',heavy:'Downpour',storm:'Storm',snow:'Snow',fog:'Fog',day:'Day',twilight:'Twilight',night:'Night' };
  const picture = () => `assets/backgrounds/${current('season')}_${current('condition')}_${current('phase')}.jpg`;
  const description = () => [current('season'),current('condition'),current('phase')].map(k => names[k]).join(' · ');

  cards.forEach(card => {
    let lastImage = card.style.backgroundImage;
    new MutationObserver(() => {
      const nextImage = card.style.backgroundImage;
      if (!nextImage || nextImage === lastImage) return;
      if (lastImage && !reduced) {
        card.querySelectorAll('.scene-transition').forEach(el => el.remove());
        const old = document.createElement('div');
        old.className = 'scene-transition';
        old.style.backgroundImage = lastImage;
        card.append(old);
        requestAnimationFrame(() => { old.style.opacity = '0'; });
        setTimeout(() => old.remove(), 750);
      }
      lastImage = nextImage;
    }).observe(card, {attributes:true,attributeFilter:['style']});
  });

  const controls = document.querySelector('.controls-panel');
  let miniature, miniLabel;
  if (controls) {
    const element = document.createElement('div');
    element.className = 'mobile-scene-preview';
    element.innerHTML = '<span class="mini-picture" aria-hidden="true"></span><span><strong></strong><small>Changes as you choose conditions</small></span>';
    controls.prepend(element);
    miniature = element.querySelector('.mini-picture');
    miniLabel = element.querySelector('strong');
  }
  const sync = () => {
    if (miniature) miniature.style.backgroundImage = `url("${picture()}")`;
    if (miniLabel) miniLabel.textContent = description();
    document.querySelectorAll('[data-gallery-season]').forEach(el => el.setAttribute('aria-pressed', String(el.dataset.gallerySeason === current('season'))));
  };
  document.querySelectorAll('[data-season],[data-condition],[data-phase],[data-gallery-season]').forEach(el => el.addEventListener('click', () => queueMicrotask(sync)));
  sync();

  const hero = document.querySelector('.hero-stage .scene-frame');
  if (hero) {
    const order = ['sunny','partly','cloudy','rain','heavy','storm','snow','fog'];
    const cycle = () => document.querySelector(`[data-condition="${order[(order.indexOf(current('condition')) + 1) % order.length]}"]`)?.click();
    hero.setAttribute('role','button'); hero.tabIndex = 0;
    hero.setAttribute('aria-label','Preview another weather condition');
    hero.addEventListener('click',cycle);
    hero.addEventListener('keydown',e => { if(e.key === 'Enter'||e.key === ' '){e.preventDefault();cycle();} });
    const hint = document.querySelector('.hero-stage .stage-note span:nth-child(2)');
    if(hint) hint.textContent = 'Tap preview to change the sky';
  }

  const navbar = document.querySelector('.navbar');
  const nav = navbar?.querySelector('.nav-links');
  if(navbar && nav) {
    nav.id = 'mobile-navigation';
    const button = document.createElement('button');
    button.className='menu-toggle';button.type='button';
    button.setAttribute('aria-controls',nav.id);
    button.innerHTML='<span aria-hidden="true">☰</span>';
    navbar.append(button);
    const setOpen = open => {
      nav.classList.toggle('is-open',open);
      button.setAttribute('aria-expanded',String(open));
      button.setAttribute('aria-label',open?'Close navigation menu':'Open navigation menu');
      button.firstElementChild.textContent = open ? '×' : '☰';
    };
    setOpen(false);
    button.addEventListener('click',() => setOpen(!nav.classList.contains('is-open')));
    nav.querySelectorAll('a').forEach(link => link.addEventListener('click',() => setOpen(false)));
    document.addEventListener('click',e => {if(!navbar.contains(e.target)) setOpen(false);});
    document.addEventListener('keydown',e => {if(e.key==='Escape') setOpen(false);});
    matchMedia('(min-width:1001px)').addEventListener('change',e => {if(e.matches) setOpen(false);});
  }
})();