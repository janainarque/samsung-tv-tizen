/* Seasonal AniList carousel: one query, local rotation, no navigation requests. */
var SeasonAnime = (function () {
  'use strict';
  var CACHE_KEY = 'fmtv.seasonAnime.v1';
  var FRESH_MS = 6 * 60 * 60 * 1000;
  var STALE_MS = 7 * 24 * 60 * 60 * 1000;
  var started = false, focused = false, suspended = false, controls = null;

  function artwork(root, item) {
    var current = root.querySelector('.anime-art');
    var next = item && item.art && item.loaded ? item.art : null;
    if (next) {
      next.hidden = false;
      if (next !== current) current.parentNode.replaceChild(next, current);
    } else current.hidden = true;
  }

  function season(date) {
    return {name: ['WINTER', 'SPRING', 'SUMMER', 'FALL'][Math.floor(date.getMonth() / 3)], year: date.getFullYear()};
  }
  function imageURL(value) {
    return typeof value === 'string' && /^https:\/\/s\d*\.anilist\.co\//i.test(value) ? value : '';
  }
  function media(value) {
    if (!value || !value.title) return null;
    var title = [value.title.english, value.title.romaji, value.title.native].filter(function (s) {
      return typeof s === 'string' && s.trim();
    })[0];
    if (!title) return null;
    return {title: title.trim().slice(0, 180), languageAvailability: [],
      image: imageURL(value.bannerImage) || imageURL(value.coverImage && value.coverImage.large),
      episodes: typeof value.episodes === 'number' && value.episodes > 0 ? value.episodes : null,
      score: typeof value.averageScore === 'number' && value.averageScore >= 0 && value.averageScore <= 100 ? value.averageScore : null,
      genres: (Array.isArray(value.genres) ? value.genres : []).filter(function (g) { return typeof g === 'string'; }).slice(0, 2)};
  }
  function readCache() {
    try { return JSON.parse(localStorage.getItem(CACHE_KEY) || 'null'); } catch (e) { return null; }
  }
  function saveCache(cache) {
    try { localStorage.setItem(CACHE_KEY, JSON.stringify(cache)); } catch (e) { /* storage denied/full */ }
  }
  function render(root, item, state, category) {
    root.className = 'anime-' + (item ? 'ready' : state || 'error') + (focused ? ' anime-focused' : '');
    artwork(root, item);
    var movie = category === 'movies', series = category === 'series';
    var heading = series ? 'Séries em destaque' : movie ? 'Filmes em destaque' : 'Animes da temporada';
    root.setAttribute('aria-label', series ? 'Séries em destaque' : movie ? 'Filmes em destaque' : 'Anime da temporada');
    var label = root.querySelector('.anime-label');
    if (label) label.textContent = series ? 'SÉRIES EM DESTAQUE' : movie ? 'FILMES EM DESTAQUE' : 'ANIME DA TEMPORADA';
    root.querySelector('h2').textContent = item ? item.title : heading;
    var info = item ? item.genres.slice() : [];
    if (item && item.year) info.push(item.year);
    if (item && item.episodes) info.push(item.episodes + ' episódios');
    if (item && item.score !== null) info.push('Nota ' + item.score + '/100');
    var messages = {
      loading: 'Carregando destaque da temporada…',
      empty: 'Nenhum anime encontrado para esta temporada.',
      timeout: 'A consulta demorou demais. Seus aplicativos continuam disponíveis.',
      network: 'Sem conexão com o AniList. Seus aplicativos continuam disponíveis.',
      rate: 'AniList temporariamente limitado. Tente em outra abertura.',
      error: 'Destaque indisponível. Seus aplicativos continuam disponíveis.'
    };
    root.querySelector('.anime-info').textContent = item ? info.join(' · ') || 'Destaque da temporada' : (series ? 'Séries indisponíveis no momento.' : movie ? 'Filmes indisponíveis no momento.' : messages[state] || messages.error);
  }
  function init(root) {
    if (started || !root) return;
    // Never expose unstyled content if an old stylesheet or a failed load is used.
    if (window.getComputedStyle && window.getComputedStyle(root).position !== 'absolute') {
      console.warn('AniList: stylesheet unavailable; feature remains hidden.');
      return;
    }
    root.hidden = false;
    started = true;
    var list = [], index = 0, timer = null, transition = null;
    var category = 'anime', groups = {anime: {items: [], index: 0, state: 'loading'}, movies: {items: [], index: 0, state: 'error'}, series: {items: [], index: 0, state: 'error'}};
    var dots = root.querySelector('.anime-dots');
    function indicators() {
      for (var i = 0; i < dots.children.length; i++) dots.children[i].className = i === index ? 'current' : '';
    }
    function show() {
      render(root, list[index], groups[category].state, category);
      indicators();
    }
    function stop() {
      if (timer !== null) window.clearInterval(timer);
      if (transition !== null) window.clearTimeout(transition);
      timer = transition = null;
      if (list.length) show();
    }
    function advance(direction) {
      if (list.length < 2 || transition !== null) return;
      if (document.hidden) { stop(); return; }
      function commit() {
        transition = null;
        index = (index + (direction === -1 ? -1 : 1) + list.length) % list.length;
        groups[category].index = index;
        show();
      }
      if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) commit();
      else {
        // Never fade to zero: text and a background stay visible throughout.
        root.className = 'anime-ready anime-changing' + (focused ? ' anime-focused' : '');
        transition = window.setTimeout(commit, 160);
      }
    }
    function resume() {
      stop();
      if (!suspended && !focused && !document.hidden && list.length > 1) timer = window.setInterval(advance, 10000);
    }
    function rebuild() {
      dots.innerHTML = '';
      for (var i = 0; i < list.length; i++) dots.appendChild(document.createElement('span'));
      show();
    }
    function useList(items, kind) {
      kind = kind || 'anime';
      if (groups[kind].items === items) return;
      groups[kind].items = items;
      groups[kind].index = Math.min(groups[kind].index, Math.max(0, items.length - 1));
      // Preload only when the source list changes, never while browsing.
      items.forEach(function (item) {
        if (!item.image || item.art) return;
        var image = new window.Image();
        image.className = 'anime-art'; image.alt = ''; image.hidden = true;
        item.art = image; item.loaded = false;
        image.onload = function () { item.loaded = true; if (list[index] === item) artwork(root, item); };
        image.onerror = function () { item.loaded = false; if (list[index] === item) artwork(root, item); };
        image.src = item.image;
      });
      if (category === kind) {
        stop(); list = items; index = groups[kind].index; rebuild(); resume();
      }
    }
    function animeState(state) {
      groups.anime.state = state;
      if (category === 'anime' && !list.length) show();
    }
    controls = {suspend: function (value) { if (suspended !== value) { suspended = value; resume(); } }, focus: function (value) {
      if (focused === value) return;
      focused = value; resume(); root.classList.toggle('anime-focused', focused);
    }, step: function (direction) { if (focused) advance(direction); },
    select: function (kind) {
      if (!groups[kind] || category === kind) return;
      stop(); groups[category].index = index; category = kind;
      list = groups[kind].items; index = groups[kind].index; rebuild(); resume();
    }, current: function () {
      var item = list[index];
      return item ? {title: item.title, image: item.image, category: category} : null;
    }, movies: function (items) { useList(items, 'movies'); },
    series: function (items) { useList(items, 'series'); }};
    document.addEventListener('visibilitychange', resume);
    var now = Date.now(), current = season(new Date(now));
    var key = current.name + '-' + current.year;
    var cache = readCache();
    if (!cache || cache.season !== key) cache = {season: key, at: 0, retryAt: 0, item: null};
    var items = [];
    // Revalidate cached data too: localStorage is not a trusted API response.
    if (now >= cache.at && now - cache.at < STALE_MS) {
      var entries = Array.isArray(cache.items) ? cache.items : cache.item ? [cache.item] : [];
      items = entries.slice(0, 5).map(function (item) {
        return media({title: {english: item && item.title}, bannerImage: item && item.image,
          episodes: item && item.episodes, averageScore: item && item.score, genres: item && item.genres});
      }).filter(function (item) { return !!item; });
    }
    if (items.length) useList(items);
    else animeState('loading');
    // Upgrade an old single-item cache with one list request, preserving its fallback.
    if ((items.length && Array.isArray(cache.items) && now - cache.at < FRESH_MS) || now < cache.retryAt) {
      if (!items.length) animeState(cache.error || 'error');
      return;
    }
    var xhr, finished = false;
    function fail(reason) {
      if (finished) return;
      finished = true;
      // No automatic retry. A later page load may try after the cooldown.
      var retry = 0;
      try { retry = Number(xhr.getResponseHeader('Retry-After')) || 0; } catch (e) {}
      cache.retryAt = Date.now() + Math.min(86400, Math.max(900, retry)) * 1000;
      cache.error = reason || 'error';
      saveCache(cache);
      animeState(cache.error);
    }
    try {
      xhr = new XMLHttpRequest();
      xhr.open('POST', 'https://graphql.anilist.co', true);
      xhr.timeout = 8000;
      xhr.setRequestHeader('Content-Type', 'application/json');
      xhr.setRequestHeader('Accept', 'application/json');
      xhr.onerror = function () {
        // Browsers intentionally do not distinguish CORS from transport failures in JS.
        console.warn('AniList: network/CORS failure; inspect the Network panel for details.');
        fail('network');
      };
      xhr.ontimeout = function () { fail('timeout'); };
      xhr.onabort = function () { fail('error'); };
      xhr.onload = function () {
        if (finished) return;
        if (xhr.status !== 200) {
          console.warn('AniList: HTTP ' + xhr.status);
          fail(xhr.status === 429 ? 'rate' : 'error'); return;
        }
        var result;
        try {
          var response = JSON.parse(xhr.responseText);
          if (response.errors) { fail(); return; }
          if (!response.data || !response.data.Page || !Array.isArray(response.data.Page.media)) { fail('error'); return; }
          if (!response.data.Page.media.length) { fail('empty'); return; }
          result = response.data.Page.media.slice(0, 5).map(media).filter(function (item) { return !!item; });
        } catch (e) { fail(); return; }
        if (!result.length) { fail('empty'); return; }
        finished = true;
        saveCache({season: key, at: Date.now(), retryAt: 0, items: result});
        useList(result);
      };
      xhr.send(JSON.stringify({
        query: 'query ($season: MediaSeason, $year: Int) { Page(page: 1, perPage: 5) { media(type: ANIME, format: TV, isAdult: false, season: $season, seasonYear: $year, sort: POPULARITY_DESC) { title { english romaji native } bannerImage coverImage { large } episodes averageScore genres } } }',
        variables: {season: current.name, year: current.year}
      }));
    } catch (e) { fail(); }
  }
  return {setSuspended: function (value) { if (controls) controls.suspend(value); }, current: function () { return controls ? controls.current() : null; }, init: init, setFocused: function (value) { if (controls) controls.focus(value); },
    step: function (direction) { if (controls) controls.step(direction); },
    select: function (kind) { if (controls) controls.select(kind); },
    movies: function (items) { if (controls) controls.movies(items); },
    series: function (items) { if (controls) controls.series(items); }};
}());
// Independent from discovery, weather and the rest of the Home startup.
SeasonAnime.init(document.getElementById('season-anime'));
