// Banda sonora ambiental y controles compartidos entre vistas.
(function () {
    const audio = document.getElementById('game-soundtrack');
    const toggle = document.getElementById('soundtrack-toggle');
    const playlists = {
        'conway-view': {
            tracks: [
                'sound/Life of Conway/Life of Conway - Falling Through the Hourglass.mp3',
                'sound/Life of Conway/Life of Conway - Into Midnight.mp3',
                'sound/Life of Conway/Life of Conway - Refreshing.mp3',
                'sound/Life of Conway/Life of Conway - Sky Sailing.mp3'
            ],
            remaining: [],
            lastTrack: null
        },
        'space-invaders-view': {
            tracks: [
                'sound/Space Invaders/Space Invaders Soundtrack - Neptune 1.mp3',
                'sound/Space Invaders/Space Invaders Soundtrack - Neptune 2 .mp3',
                'sound/Space Invaders/Space Invaders Soundtrack - Pluto 1 .mp3',
                'sound/Space Invaders/Space Invaders Soundtrack - Pluto 2 .mp3',
                'sound/Space Invaders/Space Invaders Soundtrack - Uranus 1 .mp3'
            ],
            remaining: [],
            lastTrack: null
        }
    };

    let activePlaylist = null;
    let muted = false;
    let playRequest = 0;

    function updateToggle(message) {
        if (!activePlaylist || activePlaylist.tracks.length === 0) {
            toggle.disabled = true;
            toggle.textContent = '♫ Sin música';
            toggle.setAttribute('aria-label', 'No hay música disponible para este juego');
            toggle.setAttribute('aria-pressed', 'false');
            return;
        }

        const label = message || (muted ? '♫ Activar música' : '♫ Silenciar música');
        toggle.disabled = false;
        toggle.textContent = label;
        toggle.setAttribute('aria-label', label.replace('♫ ', ''));
        toggle.setAttribute('aria-pressed', String(muted));
    }

    function getNextTrack(playlist) {
        if (playlist.remaining.length === 0) {
            playlist.remaining = playlist.tracks.slice();
            for (let index = playlist.remaining.length - 1; index > 0; index--) {
                const swapIndex = Math.floor(Math.random() * (index + 1));
                [playlist.remaining[index], playlist.remaining[swapIndex]] =
                    [playlist.remaining[swapIndex], playlist.remaining[index]];
            }

            const lastIndex = playlist.remaining.length - 1;
            if (playlist.remaining.length > 1 && playlist.remaining[lastIndex] === playlist.lastTrack) {
                [playlist.remaining[0], playlist.remaining[lastIndex]] =
                    [playlist.remaining[lastIndex], playlist.remaining[0]];
            }
        }

        playlist.lastTrack = playlist.remaining.pop();
        return playlist.lastTrack;
    }

    function playCurrentTrack() {
        const request = ++playRequest;
        audio.muted = muted;

        const playPromise = audio.play();
        if (playPromise && typeof playPromise.then === 'function') {
            playPromise.then(() => {
                if (request === playRequest) {
                    updateToggle();
                }
            }).catch(error => {
                if (request !== playRequest || error.name === 'AbortError') {
                    return;
                }
                updateToggle(error.name === 'NotAllowedError' ? '♫ Iniciar música' : '♫ Reintentar música');
            });
        }
    }

    function playNextTrack() {
        audio.src = getNextTrack(activePlaylist);
        audio.load();
        playCurrentTrack();
    }

    window.addEventListener('gameviewchange', event => {
        const playlist = playlists[event.detail.viewId];
        if (!playlist) {
            return;
        }

        playRequest++;
        audio.pause();
        audio.removeAttribute('src');
        audio.load();
        activePlaylist = playlist;
        updateToggle();

        if (playlist.tracks.length > 0) {
            playNextTrack();
        }
    });

    audio.addEventListener('ended', () => {
        if (activePlaylist && activePlaylist.tracks.length > 0) {
            playNextTrack();
        }
    });

    audio.addEventListener('error', () => {
        if (activePlaylist && activePlaylist.tracks.length > 0 && audio.src) {
            updateToggle('♫ Error al cargar música');
        }
    });

    toggle.addEventListener('click', () => {
        if (!activePlaylist || activePlaylist.tracks.length === 0) {
            return;
        }

        if (audio.paused) {
            muted = false;
            audio.muted = false;
            if (audio.src && !audio.error) {
                playCurrentTrack();
            } else {
                playNextTrack();
            }
            return;
        }

        muted = !muted;
        audio.muted = muted;
        updateToggle();
    });
})();

(function () {
    const views = Array.from(document.querySelectorAll('.game-view'));
    const switchButtons = Array.from(document.querySelectorAll('.game-switch [data-view]'));
    const conwayView = document.getElementById('conway-view');
    const invadersView = document.getElementById('space-invaders-view');
    const favicon = document.getElementById('site-favicon');
    const defaultFavicon = favicon.getAttribute('href');

    function activateView(viewId, updateHash) {
        views.forEach(view => {
            view.hidden = view.id !== viewId;
        });

        switchButtons.forEach(button => {
            const isActive = button.dataset.view === viewId;
            button.classList.toggle('is-active', isActive);
            button.setAttribute('aria-pressed', String(isActive));
        });

        const isInvaders = viewId === 'space-invaders-view';
        document.body.classList.toggle('space-invaders-active', isInvaders);
        document.title = isInvaders ? 'Space Invaders — Arcade' : "Conway's Game of Life";
        favicon.href = isInvaders ? 'img/space invaders - favicon.ico' : defaultFavicon;
        window.dispatchEvent(new CustomEvent('gameviewchange', { detail: { viewId } }));

        if (updateHash) {
            history.replaceState(null, '', '#' + viewId);
        }
    }

    switchButtons.forEach(button => {
        button.addEventListener('click', () => {
            activateView(button.dataset.view, true);
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    });

    const initialHashTarget = document.getElementById(location.hash.slice(1));
    const initialView = initialHashTarget && initialHashTarget.closest('.game-view');
    activateView(initialView ? initialView.id : conwayView.id, false);

    window.addEventListener('hashchange', () => {
        const hashTarget = document.getElementById(location.hash.slice(1));
        const targetView = hashTarget && hashTarget.closest('.game-view');
        if (targetView && targetView.id !== invadersView.id && targetView.id !== conwayView.id) {
            return;
        }
        if (targetView) {
            activateView(targetView.id, false);
        }
    });
})();

(function () {
    const observer = new IntersectionObserver(entries => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
            }
        });
    }, { threshold: 0.08 });

    document.querySelectorAll('.scroll-reveal').forEach(element => observer.observe(element));
})();