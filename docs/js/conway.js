//#region Simulación del fondo
(function () {
    const canvas = document.getElementById('bg-canvas');
    const ctx = canvas.getContext('2d');
    const CS = 14; // Tamaño de celda en píxeles
    let cols, rows, grid, next;

    function resize() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        cols = Math.ceil(canvas.width / CS) + 2;
        rows = Math.ceil(canvas.height / CS) + 2;
        grid = new Uint8Array(cols * rows);
        next = new Uint8Array(cols * rows);

        for (let i = 0; i < grid.length; i++) {
            grid[i] = Math.random() < 0.28 ? 1 : 0;
        }
    }

    function idx(x, y) {
        return ((x + cols) % cols) + ((y + rows) % rows) * cols;
    }

    function step() {
        for (let x = 0; x < cols; x++) {
            for (let y = 0; y < rows; y++) {
                let n = 0;

                for (let dx = -1; dx <= 1; dx++) {
                    for (let dy = -1; dy <= 1; dy++) {
                        if (dx === 0 && dy === 0) {
                            continue;
                        }

                        n += grid[idx(x + dx, y + dy)];
                    }
                }

                const cur = grid[idx(x, y)];
                next[idx(x, y)] = cur ? (n === 2 || n === 3 ? 1 : 0) : (n === 3 ? 1 : 0);
            }
        }

        let tmp = grid;
        grid = next;
        next = tmp;
    }

    function draw() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Dibuja las líneas de la cuadrícula.
        ctx.strokeStyle = '#0a1a4a';
        ctx.lineWidth = 0.5;

        for (let x = 0; x <= cols; x++) {
            ctx.beginPath();
            ctx.moveTo(x * CS, 0);
            ctx.lineTo(x * CS, canvas.height);
            ctx.stroke();
        }

        for (let y = 0; y <= rows; y++) {
            ctx.beginPath();
            ctx.moveTo(0, y * CS);
            ctx.lineTo(canvas.width, y * CS);
            ctx.stroke();
        }

        // Dibuja las células vivas.
        for (let x = 0; x < cols; x++) {
            for (let y = 0; y < rows; y++) {
                if (!grid[idx(x, y)]) {
                    continue;
                }

                const px = x * CS + 1;
                const py = y * CS + 1;
                const cw = CS - 2;
                ctx.fillStyle = 'rgba(0,40,100,0.6)';
                ctx.fillRect(px - 1, py - 1, cw + 2, cw + 2);
                ctx.fillStyle = '#0096ff';
                ctx.fillRect(px, py, cw, cw);
                ctx.fillStyle = 'rgba(0,220,255,0.5)';
                ctx.fillRect(px, py, Math.max(1, cw >> 1), Math.max(1, Math.floor(cw / 3)));
            }
        }
    }

    let last = 0;

    function loop(ts) {
        if (ts - last > 120) {
            step();
            draw();
            last = ts;
        }

        requestAnimationFrame(loop);
    }

    resize();
    window.addEventListener('resize', resize);
    requestAnimationFrame(loop);
})();
//#endregion Simulación del fondo

//#region Datos de patrones
const PATTERNS_DATA = [
    {
        name: 'Glider',
        cat: 'Nave (Spaceship)',
        desc: 'El patrón móvil más pequeño. Se desplaza diagonalmente 1 celda cada 4 generaciones. Fue el primer patrón descubierto que viaja indefinidamente.',
        grid: [[0, 1, 0], [0, 0, 1], [1, 1, 1]],
        w: 5,
        h: 5,
        ox: 1,
        oy: 1
    },
    {
        name: 'Blinker',
        cat: 'Oscilador P2',
        desc: 'El oscilador más pequeño posible. Alterna entre una línea horizontal y una vertical cada generación. Extremadamente común en el caos inicial.',
        grid: [[1, 1, 1]],
        w: 5,
        h: 3,
        ox: 1,
        oy: 1
    },
    {
        name: 'Pulsar',
        cat: 'Oscilador P3',
        desc: 'Con período 3 y 48 celdas vivas, el Pulsar es uno de los patrones más visualmente impresionantes. Aparece naturalmente con cierta frecuencia.',
        grid: (() => {
            const p = Array.from({ length: 13 }, () => Array(13).fill(0));
            [
                [0, 2], [0, 3], [0, 4], [0, 8], [0, 9], [0, 10],
                [5, 2], [5, 3], [5, 4], [5, 8], [5, 9], [5, 10],
                [7, 2], [7, 3], [7, 4], [7, 8], [7, 9], [7, 10],
                [12, 2], [12, 3], [12, 4], [12, 8], [12, 9], [12, 10],
                [1, 0], [2, 0], [3, 0], [4, 0], [8, 0], [9, 0], [10, 0], [11, 0],
                [1, 5], [2, 5], [3, 5], [4, 5], [8, 5], [9, 5], [10, 5], [11, 5],
                [1, 7], [2, 7], [3, 7], [4, 7], [8, 7], [9, 7], [10, 7], [11, 7],
                [1, 12], [2, 12], [3, 12], [4, 12], [8, 12], [9, 12], [10, 12], [11, 12]
            ].forEach(([r, c]) => p[r][c] = 1);

            return p;
        })(),
        w: 15,
        h: 15,
        ox: 1,
        oy: 1
    },
    {
        name: 'Gosper Glider Gun',
        cat: 'Cañón',
        desc: 'El primer cañón descubierto (1970, Bill Gosper). Emite un nuevo Glider cada 30 generaciones, produciendo crecimiento poblacional indefinido.',
        grid: (() => {
            const p = Array.from({ length: 11 }, () => Array(38).fill(0));
            [
                [5, 1], [5, 2], [6, 1], [6, 2],
                [5, 11], [6, 11], [7, 11], [4, 12], [8, 12], [3, 13], [9, 13], [3, 14], [9, 14],
                [6, 15], [4, 16], [8, 16], [5, 17], [6, 17], [7, 17], [6, 18],
                [3, 21], [4, 21], [5, 21], [3, 22], [4, 22], [5, 22], [2, 23], [6, 23],
                [1, 25], [2, 25], [6, 25], [7, 25],
                [3, 35], [4, 35], [3, 36], [4, 36]
            ].forEach(([r, c]) => p[r][c] = 1);

            return p;
        })(),
        w: 40,
        h: 13,
        ox: 1,
        oy: 1
    },
    {
        name: 'R-pentomino',
        cat: 'Methuselah',
        desc: 'Solo 5 celdas activas, pero evoluciona durante 1103 generaciones antes de estabilizarse. Fue el primer patrón de larga vida descubierto.',
        grid: [[0, 1, 1], [1, 1, 0], [0, 1, 0]],
        w: 5,
        h: 5,
        ox: 1,
        oy: 1
    },
    {
        name: 'LWSS',
        cat: 'Nave (Spaceship)',
        desc: 'Lightweight Spaceship, la nave más pequeña que se mueve horizontalmente. Período 4, se desplaza 2 celdas por ciclo.',
        grid: [[0, 1, 0, 0, 1], [1, 0, 0, 0, 0], [1, 0, 0, 0, 1], [1, 1, 1, 1, 0]],
        w: 7,
        h: 6,
        ox: 1,
        oy: 1
    },
    {
        name: 'Block',
        cat: 'Still Life',
        desc: 'El patrón estático más pequeño y más común. Un cuadrado 2×2 que permanece eternamente estable. Aparece constantemente como residuo de patrones caóticos.',
        grid: [[1, 1], [1, 1]],
        w: 4,
        h: 4,
        ox: 1,
        oy: 1
    },
    {
        name: 'Beacon',
        cat: 'Oscilador P2',
        desc: 'Dos bloques 2×2 que se tocan en una esquina. Oscila entre dos estados: los dos bloques completos, y los bloques con las esquinas interiores alternando.',
        grid: [[1, 1, 0, 0], [1, 0, 0, 0], [0, 0, 0, 1], [0, 0, 1, 1]],
        w: 6,
        h: 6,
        ox: 1,
        oy: 1
    },
    {
        name: 'Acorn',
        cat: 'Methuselah',
        desc: '7 celdas que producen 633 celdas vivas tras 5206 generaciones. Uno de los patrones de mayor tiempo de vida para su tamaño inicial.',
        grid: [[0, 1, 0, 0, 0, 0, 0], [0, 0, 0, 1, 0, 0, 0], [1, 1, 0, 0, 1, 1, 1]],
        w: 9,
        h: 5,
        ox: 1,
        oy: 1
    }
];
//#endregion Datos de patrones

//#region Dibujo y tarjetas de patrones
function drawPatternCanvas(canvas, data) {
    const W = canvas.width;
    const H = canvas.height;
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = '#04081a';
    ctx.fillRect(0, 0, W, H);

    const g = data.grid;
    const rows = g.length;
    const cols = g[0].length;
    const cs = Math.min(Math.floor((W - 20) / cols), Math.floor((H - 20) / rows), 12);
    const startX = Math.floor((W - cols * cs) / 2);
    const startY = Math.floor((H - rows * cs) / 2);

    // Dibuja el fondo de la cuadrícula.
    ctx.strokeStyle = '#0a1a4a';
    ctx.lineWidth = 0.5;

    for (let x = 0; x <= cols; x++) {
        ctx.beginPath();
        ctx.moveTo(startX + x * cs, startY);
        ctx.lineTo(startX + x * cs, startY + rows * cs);
        ctx.stroke();
    }

    for (let y = 0; y <= rows; y++) {
        ctx.beginPath();
        ctx.moveTo(startX, startY + y * cs);
        ctx.lineTo(startX + cols * cs, startY + y * cs);
        ctx.stroke();
    }

    for (let r = 0; r < rows; r++) {
        for (let c = 0; c < cols; c++) {
            if (!g[r][c]) {
                continue;
            }

            const px = startX + c * cs + 1;
            const py = startY + r * cs + 1;
            const cw = cs - 2;
            ctx.fillStyle = 'rgba(0,40,100,0.6)';
            ctx.fillRect(px - 1, py - 1, cw + 2, cw + 2);
            ctx.fillStyle = '#0096ff';
            ctx.fillRect(px, py, cw, cw);
            ctx.fillStyle = 'rgba(0,220,255,0.5)';
            ctx.fillRect(px, py, Math.max(1, cw >> 1), Math.max(1, Math.floor(cw / 3)));
        }
    }
}

function buildPatternCards() {
    const grid = document.getElementById('patterns-grid');

    PATTERNS_DATA.forEach(p => {
        const card = document.createElement('div');
        card.className = 'pattern-card';

        const cv = document.createElement('canvas');
        cv.className = 'pattern-preview';
        cv.width = 560;
        cv.height = 220;
        card.appendChild(cv);

        const info = document.createElement('div');
        info.className = 'pattern-info';
        info.innerHTML = `
            <div class="pattern-category">${p.cat}</div>
            <h3>${p.name}</h3>
            <p>${p.desc}</p>
        `;
        card.appendChild(info);
        grid.appendChild(card);

        setTimeout(() => drawPatternCanvas(cv, p), 50);
    });
}
//#endregion Dibujo y tarjetas de patrones

//#region Inicialización de tarjetas
buildPatternCards();
//#endregion Inicialización de tarjetas

//#region Revelado al desplazarse
const observer = new IntersectionObserver(entries => {
    entries.forEach(e => {
        if (e.isIntersecting) {
            e.target.classList.add('visible');
        }
    });
}, { threshold: 0.08 });

document.querySelectorAll('.scroll-reveal').forEach(el => observer.observe(el));
//#endregion Revelado al desplazarse
