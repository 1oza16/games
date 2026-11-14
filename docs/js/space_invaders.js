// Cambio entre las dos páginas explicativas.
(function () {
    const views = Array.from(document.querySelectorAll('.game-view'));
    const switchButtons = Array.from(document.querySelectorAll('.game-switch [data-view]'));
    const conwayView = document.getElementById('conway-view');
    const invadersView = document.getElementById('space-invaders-view');

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

// Recreativa ambiental inspirada en la partida de Pygame.
(function () {
    const canvas = document.getElementById('invaders-background');
    const ctx = canvas.getContext('2d');
    const WIDTH = 800;
    const HEIGHT = 700;
    const colors = {
        black: '#000000',
        white: '#f5f5f5',
        cyan: '#14dcf0',
        green: '#32eb32',
        yellow: '#ebeb32',
        red: '#eb3232',
        pink: '#eb788c',
        purple: '#c832c8'
    };

    const sprites = {
        green: [
            ['...11...', '..1111..', '.111111.', '11.11.11', '11111111', '..1..1..', '.1.11.1.', '1......1'],
            ['...11...', '..1111..', '.111111.', '11.11.11', '11111111', '...11...', '..1..1..', '.1....1.']
        ],
        yellow: [
            ['..1.....1..', '...1...1...', '..1111111..', '.11.111.11.', '11111111111', '1.1111111.1', '1.1.....1.1', '...11.11...'],
            ['..1.....1..', '1..1...1..1', '1.1111111.1', '111.111.111', '11111111111', '.111111111.', '..1.....1..', '.1.......1.']
        ],
        red: [
            ['....1111....', '.1111111111.', '111111111111', '111..11..111', '111111111111', '...11..11...', '..11.11.11..', '11........11'],
            ['....1111....', '.1111111111.', '111111111111', '111..11..111', '111111111111', '..11....11..', '.11......11.', '..11....11..']
        ],
        ufo: [
            '....111111....', '..1111111111..', '.111111111111.', '.11.11.11.11..',
            '11111111111111', '...111..111...', '.....1..1.....'
        ],
        player: [
            '.....1.....', '....111....', '....111....', '.111111111.',
            '11111111111', '11111111111', '11111111111'
        ],
        bunker: [
            '....11111111111111....', '...1111111111111111...', '..111111111111111111..',
            '.11111111111111111111.', '1111111111111111111111', '1111111111111111111111',
            '1111111111111111111111', '1111111111111111111111', '111111....11....111111',
            '11111......1......1111', '1111.......1.......111', '111........1........11',
            '11.........1.........1'
        ]
    };

    const stars = Array.from({ length: 170 }, (_, index) => ({
        x: (index * 193 + 37) % WIDTH,
        y: (index * 127 + 11) % HEIGHT,
        size: index % 17 === 0 ? 2 : 1,
        speed: 10 + (index % 5) * 8,
        tint: index % 6 === 0 ? '#aaaac8' : colors.white
    }));
    const spritePreviews = Array.from(document.querySelectorAll('.space-invaders-page canvas[data-sprite]'));
    const previewColors = {
        green: colors.green,
        yellow: colors.yellow,
        red: colors.red,
        ufo: colors.purple,
        player: colors.cyan,
        bunker: colors.pink
    };

    let aliens = [];
    let bunkers = [];
    let bullets = [];
    let boss = null;
    let ufo = null;
    let score = 0;
    let lives = 3;
    let wave = 1;
    let playerX = WIDTH / 2;
    let elapsed = 0;
    let formationOffset = 0;
    let formationY = 112;
    let formationDirection = 1;
    let nextPlayerShot = 0;
    let nextAlienShot = 0;
    let nextUfo = 8;
    let gameOverAt = 0;
    let lastFrame = 0;
    let running = false;
    let frameId = 0;

    function makeBunkers() {
        return [90, 265, 440, 615].map(x => ({
            x,
            y: 520,
            pixels: sprites.bunker.map(row => Array.from(row, value => value === '1'))
        }));
    }

    function startWave() {
        aliens = [];
        boss = null;
        bullets = [];
        formationOffset = 0;
        formationY = 112;
        formationDirection = 1;

        if (wave % 5 === 0) {
            boss = { x: 400, y: 115, direction: 1, health: 5 + (wave / 5 - 1) * 2, maxHealth: 5 + (wave / 5 - 1) * 2 };
            return;
        }

        for (let row = 0; row < 5; row++) {
            for (let column = 0; column < 11; column++) {
                aliens.push({ row, column, alive: true });
            }
        }
    }

    function resetGame() {
        score = 0;
        lives = 3;
        wave = 1;
        playerX = WIDTH / 2;
        elapsed = 0;
        nextPlayerShot = 0;
        nextAlienShot = 1;
        nextUfo = 9;
        gameOverAt = 0;
        ufo = null;
        bunkers = makeBunkers();
        startWave();
    }

        function drawSprite(pattern, x, y, pixelSize, color, context) {
        const target = context || ctx;
        target.fillStyle = color;
        pattern.forEach((row, rowIndex) => {
            for (let column = 0; column < row.length; column++) {
                if (row[column] === '1') {
                    target.fillRect(x + column * pixelSize, y + rowIndex * pixelSize, pixelSize, pixelSize);
                }
            }
        });
    }

    let previewFrame = -1;

    function drawSpritePreviews(frame) {
        if (previewFrame === frame) {
            return;
        }
        previewFrame = frame;

        spritePreviews.forEach(preview => {
            const sprite = sprites[preview.dataset.sprite];
            const pattern = Array.isArray(sprite[0]) ? sprite[frame] : sprite;
            const pixelSize = 4;
            preview.width = pattern[0].length * pixelSize;
            preview.height = pattern.length * pixelSize;
            const previewContext = preview.getContext('2d');
            previewContext.imageSmoothingEnabled = false;
            drawSprite(pattern, 0, 0, pixelSize, previewColors[preview.dataset.sprite], previewContext);
        });
    }

    function fireAlienShot() {
        if (boss) {
            [-24, 0, 24].forEach((offset, index) => {
                bullets.push({
                    x: boss.x + offset,
                    y: boss.y + 35,
                    velocityX: (index - 1) * 65,
                    velocityY: 235 + wave * 2,
                    enemy: true
                });
            });
        } else {
            const activeAliens = aliens.filter(alien => alien.alive);
            if (activeAliens.length) {
                const alien = activeAliens[Math.floor(Math.random() * activeAliens.length)];
                const x = 105 + alien.column * 49 + formationOffset;
                const y = 116 + alien.row * 39 + formationY;
                bullets.push({ x, y, velocityX: (playerX - x) * 0.12, velocityY: 220 + wave * 5, enemy: true });
            }
        }
        nextAlienShot = elapsed + 0.8 + Math.random() * 0.85;
    }

    function damageBunker(bullet) {
        for (const bunker of bunkers) {
            const column = Math.floor((bullet.x - bunker.x) / 4);
            const row = Math.floor((bullet.y - bunker.y) / 4);
            if (
                row < 0 ||
                row >= bunker.pixels.length ||
                column < 0 ||
                column >= bunker.pixels[row].length ||
                !bunker.pixels[row][column]
            ) {
                continue;
            }
            for (let dy = -1; dy <= 1; dy++) {
                for (let dx = -1; dx <= 1; dx++) {
                    const targetRow = row + dy;
                    const targetColumn = column + dx;
                    if (bunker.pixels[targetRow] && targetColumn >= 0 && targetColumn < bunker.pixels[targetRow].length) {
                        bunker.pixels[targetRow][targetColumn] = false;
                    }
                }
            }
            return true;
        }
        return false;
    }

    function update(delta) {
        elapsed += delta;
        stars.forEach(star => {
            star.y += star.speed * delta;
            if (star.y > HEIGHT) {
                star.y = 0;
                star.x = Math.random() * WIDTH;
            }
        });

        playerX = WIDTH / 2 + Math.sin(elapsed * 0.55) * 245;
        if (elapsed >= nextPlayerShot) {
            bullets.push({ x: playerX, y: 620, velocityX: 0, velocityY: -390, enemy: false });
            nextPlayerShot = elapsed + 0.58;
        }
        if (elapsed >= nextAlienShot) {
            fireAlienShot();
        }
        if (!ufo && elapsed >= nextUfo) {
            ufo = { x: -55, y: 74, velocityX: 115, points: [50, 100, 150, 300][Math.floor(Math.random() * 4)] };
            nextUfo = elapsed + 11 + Math.random() * 7;
        }

        if (boss) {
            boss.x += boss.direction * (100 + wave * 5) * delta;
            if (boss.x < 105 || boss.x > 695) {
                boss.direction *= -1;
            }
        } else {
            const speed = 26 + Math.max(0, 55 - aliens.filter(alien => alien.alive).length) * 0.55 + wave * 2;
            formationOffset += formationDirection * speed * delta;
            if (formationOffset > 58 || formationOffset < -58) {
                formationDirection *= -1;
                formationY += 17;
            }
            if (aliens.some(alien => alien.alive && 116 + alien.row * 39 + formationY > 575)) {
                lives = 0;
            }
        }

        if (ufo) {
            ufo.x += ufo.velocityX * delta;
            if (ufo.x > WIDTH + 60) {
                ufo = null;
            }
        }

        for (let index = bullets.length - 1; index >= 0; index--) {
            const bullet = bullets[index];
            bullet.x += bullet.velocityX * delta;
            bullet.y += bullet.velocityY * delta;

            if (bullet.y < -20 || bullet.y > HEIGHT + 20 || bullet.x < -20 || bullet.x > WIDTH + 20) {
                bullets.splice(index, 1);
                continue;
            }
            if (bullet.y >= 520 && bullet.y <= 572 && damageBunker(bullet)) {
                bullets.splice(index, 1);
                continue;
            }
            if (bullet.enemy) {
                if (bullet.y >= 610 && bullet.y <= 650 && Math.abs(bullet.x - playerX) < 22) {
                    lives--;
                    bullets.splice(index, 1);
                    continue;
                }
            } else if (boss && Math.abs(bullet.x - boss.x) < 60 && bullet.y >= boss.y && bullet.y <= boss.y + 55) {
                boss.health--;
                score += 50;
                bullets.splice(index, 1);
                if (boss.health <= 0) {
                    score += 500;
                    boss = null;
                }
                continue;
            } else if (!boss) {
                const alien = aliens.find(candidate => {
                    const alienX = 105 + candidate.column * 49 + formationOffset;
                    const alienY = 116 + candidate.row * 39 + formationY;
                    return candidate.alive && Math.abs(bullet.x - alienX) < 22 && Math.abs(bullet.y - alienY) < 22;
                });
                if (alien) {
                    alien.alive = false;
                    score += alien.row === 0 ? 30 : alien.row < 3 ? 20 : 10;
                    bullets.splice(index, 1);
                    continue;
                }
            }
            if (!bullet.enemy && ufo && Math.abs(bullet.x - ufo.x) < 40 && Math.abs(bullet.y - ufo.y) < 20) {
                score += ufo.points;
                ufo = null;
                bullets.splice(index, 1);
            }
        }

        if (lives <= 0) {
            lives = 0;
            if (!gameOverAt) {
                gameOverAt = elapsed;
            } else if (elapsed - gameOverAt > 2.4) {
                resetGame();
            }
        } else if (!boss && aliens.every(alien => !alien.alive)) {
            wave++;
            startWave();
        }
    }

    function draw() {
        ctx.fillStyle = colors.black;
        ctx.fillRect(0, 0, WIDTH, HEIGHT);

        stars.forEach((star, index) => {
            ctx.globalAlpha = 0.35 + (Math.sin(elapsed * 1.8 + index) + 1) * 0.28;
            ctx.fillStyle = star.tint;
            ctx.fillRect(star.x, star.y, star.size, star.size);
        });
        ctx.globalAlpha = 1;

        ctx.font = 'bold 15px monospace';
        ctx.fillStyle = colors.cyan;
        ctx.fillText('PUNTOS <1>', 38, 26);
                ctx.fillText('OLEADA', WIDTH - 108, 26);
        ctx.font = 'bold 18px monospace';
        ctx.fillStyle = colors.white;
        ctx.fillText(String(score).padStart(6, '0'), 52, 52);
        ctx.fillText(String(wave).padStart(2, '0'), WIDTH - 92, 52);

        if (boss) {
            const pattern = sprites.red[Math.floor(elapsed * 2) % 2];
            drawSprite(pattern, boss.x - 24, boss.y, 4, colors.red);
            ctx.strokeStyle = colors.white;
            ctx.strokeRect(WIDTH / 2 - 80, 68, 160, 5);
            ctx.fillStyle = colors.red;
            ctx.fillRect(WIDTH / 2 - 79, 69, 158 * (boss.health / boss.maxHealth), 3);
        } else {
            const frame = Math.floor(elapsed * 2.2) % 2;
            drawSpritePreviews(frame);
            aliens.forEach(alien => {
                if (!alien.alive) {
                    return;
                }
                const type = alien.row === 0 ? 'green' : alien.row < 3 ? 'yellow' : 'red';
                const color = alien.row === 0 ? colors.green : alien.row < 3 ? colors.yellow : colors.red;
                const pattern = sprites[type][frame];
                const pixelSize = type === 'green' ? 3 : 2;
                const x = 105 + alien.column * 49 + formationOffset;
                const y = 116 + alien.row * 39 + formationY;
                drawSprite(pattern, x - Math.floor(pattern[0].length * pixelSize / 2), y, pixelSize, color);
            });
        }
        if (boss) {
            drawSpritePreviews(Math.floor(elapsed * 2.2) % 2);
        }

        bunkers.forEach(bunker => {
            bunker.pixels.forEach((row, rowIndex) => {
                row.forEach((alive, columnIndex) => {
                    if (alive) {
                        ctx.fillStyle = colors.pink;
                        ctx.fillRect(bunker.x + columnIndex * 4, bunker.y + rowIndex * 4, 4, 4);
                    }
                });
            });
        });

        if (ufo) {
            drawSprite(sprites.ufo, ufo.x, ufo.y, 3, colors.purple);
        }

        bullets.forEach(bullet => {
            ctx.fillStyle = colors.white;
            ctx.fillRect(bullet.x - 2, bullet.y - 7, 4, 14);
        });

        if (lives > 0 || Math.floor(elapsed * 8) % 2 === 0) {
            drawSprite(sprites.player, playerX - 16, 645, 3, colors.cyan);
        }
        ctx.fillStyle = colors.white;
        ctx.font = 'bold 16px monospace';
        ctx.fillText(String(lives), 18, HEIGHT - 22);
        for (let life = 0; life < Math.max(0, lives - 1); life++) {
            drawSprite(sprites.player, 58 + life * 48, HEIGHT - 44, 2, colors.cyan);
        }
        ctx.fillStyle = colors.red;
        ctx.fillRect(0, HEIGHT - 15, WIDTH, 3);

        if (gameOverAt) {
            ctx.fillStyle = 'rgba(0, 0, 0, 0.72)';
            ctx.fillRect(0, HEIGHT / 2 - 42, WIDTH, 84);
            ctx.fillStyle = colors.red;
            ctx.textAlign = 'center';
            ctx.font = 'bold 28px monospace';
            ctx.fillText('FIN DE PARTIDA', WIDTH / 2, HEIGHT / 2 + 8);
            ctx.textAlign = 'left';
        }
    }

    function resizeCanvas() {
        const ratio = Math.min(window.devicePixelRatio || 1, 1.5);
        canvas.width = Math.round(window.innerWidth * ratio);
        canvas.height = Math.round(window.innerHeight * ratio);
        ctx.setTransform(canvas.width / WIDTH, 0, 0, canvas.height / HEIGHT, 0, 0);
    }

    function animate(timestamp) {
        if (!document.body.classList.contains('space-invaders-active') || document.hidden) {
            running = false;
            frameId = 0;
            return;
        }
        const delta = lastFrame ? Math.min((timestamp - lastFrame) / 1000, 0.05) : 0;
        lastFrame = timestamp;
        update(delta);
        draw();
        frameId = window.requestAnimationFrame(animate);
    }

    function startAnimation() {
        if (!document.body.classList.contains('space-invaders-active')) {
            return;
        }
        draw();
        if (running || document.hidden) {
            return;
        }
        running = true;
        lastFrame = 0;
        frameId = window.requestAnimationFrame(animate);
    }

    resetGame();
    resizeCanvas();
    window.addEventListener('resize', () => {
        resizeCanvas();
        if (document.body.classList.contains('space-invaders-active')) {
            draw();
        }
    });
    window.addEventListener('gameviewchange', startAnimation);
    document.addEventListener('visibilitychange', () => {
        if (document.hidden) {
            running = false;
            if (frameId) {
                window.cancelAnimationFrame(frameId);
                frameId = 0;
            }
        } else {
            startAnimation();
        }
    });
    startAnimation();
})();