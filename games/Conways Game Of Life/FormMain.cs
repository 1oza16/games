using System;
using System.Diagnostics;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.IO;
using System.Runtime.InteropServices;
using System.Windows.Forms;
using NAudio;
using NAudio.Wave;
using Timer = System.Windows.Forms.Timer;

namespace ConwaysGameOfLife
{
    public partial class FormMain : Form
    {
        #region Campos

        // Patrones conocidos
        private string _selectedPattern = "Dibujado Libre";

        private ComboBox _cmbPatterns;
        private TrackBar _trkSpeed;
        private Label _lblSpeedVal;

        //  Grid 
        private bool[,] _grid;
        private bool[,] _next;
        private int _cols, _rows;

        //  Simulation state 
        private int _generation;
        private int _population;
        private bool _running;

        //  Zoom / pan 
        private const float MaxZoom = 4f;
        private float _zoom = 1f;
        private PointF _offset = PointF.Empty;
        private Point _panStart;
        private bool _panning;
        private float MinZoom
        {
            get
            {
                int fitCellSize = Math.Min(
                    _canvas.ClientSize.Width / _cols,
                    _canvas.ClientSize.Height / _rows);
                fitCellSize = Math.Max(2, Math.Min(32, fitCellSize));
                return fitCellSize / 8f;
            }
        }

        //  Settings 
        private int CellSize => Math.Max(2, (int)(8 * _zoom));

        //  Timer 
        private readonly Timer _simTimer = new Timer();
        private readonly Timer _musicTimer = new Timer();
        private int _targetFps = 60;
        private string[] _musicTracks = Array.Empty<string>();
        private int _currentTrack = -1;
        private bool _musicMuted;
        private Mp3FileReader? _musicReader;
        private Stream? _musicStream;
        private WaveOutEvent? _musicOutput;

        //  Colors 
        private static readonly Color BG = Color.FromArgb(4, 12, 36);
        private static readonly Color GRID_CLR = Color.FromArgb(20, 40, 90);
        private static readonly Color CELL_LO = Color.FromArgb(0, 150, 255);
        private static readonly Color TEXT_CLR = Color.FromArgb(0, 220, 255);

        // Recursos GDI (se liberan al cerrar) 
        private readonly SolidBrush _bgBrush = new SolidBrush(Color.FromArgb(4, 12, 36));
        private readonly Font _uiFont = new Font("Consolas", 9f, FontStyle.Regular);
        private readonly Font _titleFont = new Font("Consolas", 11f, FontStyle.Bold);

        // Canvas 
        private DoubleBufferedPanel _canvas;

        //  Toolbar 
        private Button _btnPlay, _btnStep, _btnReset, _btnSeed, _btnWeb, _btnMusic;
        private Label _lblSpeed;

        //  Mouse draw 
        private bool _drawing;
        private bool _drawValue;
        private const string WebsiteUrl = "https://1oza16.github.io/games/index.html#conway-view";

        #endregion

        #region Inicializacion

        public FormMain()
        {
            InitializeComponent();
            FormBorderStyle = FormBorderStyle.None;
            StartPosition = FormStartPosition.Manual;
            Bounds = Screen.FromPoint(Cursor.Position).Bounds;
            SetupCanvas();
            SetupToolbar();
            SetupTimer();
            SetupMusic();
            InitGrid();
            FitMapToCanvas();
            RandomSeed();
        }

        #endregion

        #region Patrones

        // Patrones conocidos
        private static readonly Dictionary<string, bool[,]> Patterns = new()
        {
            ["Glider"] = new bool[,] {
                {false,true,false},
                {false,false,true},
                {true,true,true}
            },
            ["Blinker"] = new bool[,] {
                {true,true,true}
            },
            ["Toad"] = new bool[,] {
                {false,true,true,true},
                {true,true,true,false}
            },
            ["Beacon"] = new bool[,] {
                {true,true,false,false},
                {true,false,false,false},
                {false,false,false,true},
                {false,false,true,true}
            },
            ["Pulsar"] = BuildPulsar(),
            ["Gosper Glider Gun"] = BuildGosperGun(),
            ["LWSS"] = new bool[,] {
                {false,true,false,false,true},
                {true,false,false,false,false},
                {true,false,false,false,true},
                {true,true,true,true,false}
            },
            ["R-pentomino"] = new bool[,] {
                {false,true,true},
                {true,true,false},
                {false,true,false}
            },
            ["Diehard"] = new bool[,] {
                {false,false,false,false,false,false,true,false},
                {true,true,false,false,false,false,false,false},
                {false,true,false,false,false,true,true,true}
            },
            ["Acorn"] = new bool[,] {
                {false,true,false,false,false,false,false},
                {false,false,false,true,false,false,false},
                {true,true,false,false,true,true,true}
            },
        };

        #endregion

        #region Interfaz y toolbar

        //  Canvas 
        private void SetupCanvas()
        {
            _canvas = new DoubleBufferedPanel
            {
                Dock = DockStyle.Fill,
                BackColor = BG,
                Cursor = Cursors.Cross,
            };

            _canvas.Paint += Canvas_Paint;
            _canvas.MouseDown += Canvas_MouseDown;
            _canvas.MouseMove += Canvas_MouseMove;
            _canvas.MouseUp += Canvas_MouseUp;
            _canvas.MouseWheel += Canvas_MouseWheel;

            Controls.Add(_canvas);
            _canvas.BringToFront();
        }

        //  Toolbar 
        private void SetupToolbar()
        {
            var toolbar = new Panel
            {
                Dock = DockStyle.Bottom,
                Height = 50,
                BackColor = Color.FromArgb(6, 16, 44),
            };
            var gameControls = new FlowLayoutPanel
            {
                AutoSize = true,
                AutoSizeMode = AutoSizeMode.GrowAndShrink,
                BackColor = Color.Transparent,
                FlowDirection = FlowDirection.LeftToRight,
                Margin = Padding.Empty,
                WrapContents = false,
            };
            var patternControls = new FlowLayoutPanel
            {
                AutoSize = true,
                AutoSizeMode = AutoSizeMode.GrowAndShrink,
                BackColor = Color.Transparent,
                FlowDirection = FlowDirection.LeftToRight,
                Margin = Padding.Empty,
                WrapContents = false,
            };
            var utilityControls = new FlowLayoutPanel
            {
                AutoSize = true,
                AutoSizeMode = AutoSizeMode.GrowAndShrink,
                BackColor = Color.Transparent,
                FlowDirection = FlowDirection.LeftToRight,
                Margin = Padding.Empty,
                WrapContents = false,
            };

            // Botones existentes
            _btnPlay = MakeButton("REANUDAR");
            _btnStep = MakeButton("PASO");
            _btnReset = MakeButton("REINICIAR");
            _btnSeed = MakeButton("SEMILLA");
            _btnWeb = MakeButton("WEB");
            _btnMusic = MakeButton("♫ MUTEAR");
            _btnMusic.AccessibleName = "Silenciar música";
            var btnExit = MakeButton("SALIR");

            // ComboBox de patrones
            _cmbPatterns = new ComboBox
            {
                Width = 160,
                FlatStyle = FlatStyle.Flat,
                BackColor = Color.FromArgb(8, 30, 80),
                ForeColor = TEXT_CLR,
                Font = _uiFont,
                DropDownStyle = ComboBoxStyle.DropDownList,
                Margin = new Padding(5, 14, 5, 0),
            };
            //foreach (var key in Patterns.Keys) _cmbPatterns.Items.Add(key);
            //_cmbPatterns.SelectedIndex = 0;
            _cmbPatterns.SelectedIndexChanged += (s, e) =>
                _selectedPattern = _cmbPatterns.SelectedItem?.ToString() ?? "Glider";
            _cmbPatterns.Items.Add("Dibujado Libre");   // primer elemento
            foreach (var key in Patterns.Keys) _cmbPatterns.Items.Add(key);
            _cmbPatterns.SelectedIndex = 0;            // arranca en Free Draw
            _cmbPatterns.SelectedIndexChanged += (s, e) =>
            {
                var sel = _cmbPatterns.SelectedItem?.ToString() ?? "";
                _selectedPattern = sel == "Dibujado Libre" ? null : sel;
            };

            // TrackBar velocidad
            _trkSpeed = new TrackBar
            {
                Width = 160,
                Height = 40,
                Minimum = 1,
                Maximum = 8,          // x1 � x8
                Value = 4,          // x4 = 60 fps por defecto
                TickStyle = TickStyle.None,
                BackColor = Color.FromArgb(6, 16, 44),
                Margin = new Padding(5, 5, 5, 0),
            };

            _lblSpeedVal = new Label
            {
                Text = SpeedLabel(_trkSpeed.Value),
                ForeColor = TEXT_CLR,
                BackColor = Color.Transparent,
                Font = _uiFont,
                AutoSize = true,
                Margin = new Padding(5, 17, 5, 0),
            };
            var lblDrawn = new Label
            {
                Text = "DIBUJADO",
                ForeColor = TEXT_CLR,
                BackColor = Color.Transparent,
                Font = _uiFont,
                AutoSize = true,
                Margin = new Padding(5, 17, 5, 0),
            };
            var lblTime = new Label
            {
                Text = "TIEMPO",
                ForeColor = TEXT_CLR,
                BackColor = Color.Transparent,
                Font = _uiFont,
                AutoSize = true,
                Margin = new Padding(5, 17, 5, 0),
            };
            var leftSeparator = new Panel
            {
                BackColor = GRID_CLR,
                Size = new Size(1, 24),
            };
            var rightSeparator = new Panel
            {
                BackColor = GRID_CLR,
                Size = new Size(1, 24),
            };

            _trkSpeed.ValueChanged += (s, e) =>
            {
                _targetFps = _trkSpeed.Value * 15;          // x1=15fps � x8=120fps
                _simTimer.Interval = 1000 / _targetFps;
                _lblSpeedVal.Text = SpeedLabel(_trkSpeed.Value);
            };

            // Quitar _lblSpeed del toolbar (ya no lo necesitas)
            _btnPlay.Click += (s, e) => TogglePlay();
            _btnStep.Click += (s, e) => { Step(); _canvas.Invalidate(); };
            _btnReset.Click += (s, e) => Reset();
            _btnSeed.Click += (s, e) => { RandomSeed(); _canvas.Invalidate(); };
            _btnWeb.Click += (s, e) =>
            {
                if (string.IsNullOrWhiteSpace(WebsiteUrl)) return;

                System.Diagnostics.Process.Start(new ProcessStartInfo
                {
                    FileName = WebsiteUrl,
                    UseShellExecute = true
                });
            };
            _btnMusic.Click += (s, e) => ToggleMusicMute();
            btnExit.Click += (s, e) => Close();

            gameControls.Controls.AddRange(new Control[]
                { _btnPlay, _btnStep, _btnReset, _btnSeed });
            patternControls.Controls.AddRange(new Control[]
                { lblDrawn, _cmbPatterns, lblTime, _trkSpeed, _lblSpeedVal });
            utilityControls.Controls.AddRange(new Control[] { _btnMusic, _btnWeb, btnExit });
            toolbar.Controls.AddRange(new Control[]
                { gameControls, patternControls, utilityControls, leftSeparator, rightSeparator });
            pictureBoxConwaysGame.Size = new Size(44, 44);
            pictureBoxConwaysGame.BackgroundImageLayout = ImageLayout.Zoom;
            pictureBoxConwaysGame.BackColor = Color.Transparent;
            toolbar.Controls.Add(pictureBoxConwaysGame);

            void PositionControlGroups()
            {
                const int sidePadding = 8;
                int imageRight = toolbar.ClientSize.Width - sidePadding;
                pictureBoxConwaysGame.Location = new Point(
                    imageRight - pictureBoxConwaysGame.Width,
                    Math.Max(0, (toolbar.ClientSize.Height - pictureBoxConwaysGame.Height) / 2));

                int controlsStart = sidePadding;
                int controlsWidth = Math.Max(0, pictureBoxConwaysGame.Left - sidePadding - controlsStart);
                int groupWidth = gameControls.Width + patternControls.Width + utilityControls.Width;
                int extraSpace = Math.Max(0, controlsWidth - groupWidth);
                int leftAreaWidth = gameControls.Width + extraSpace / 3;
                int middleAreaWidth = patternControls.Width + extraSpace / 3;
                int rightAreaWidth = controlsWidth - leftAreaWidth - middleAreaWidth;
                int middleAreaStart = controlsStart + leftAreaWidth;
                int rightAreaStart = middleAreaStart + middleAreaWidth;

                gameControls.Location = new Point(
                    controlsStart + Math.Max(0, (leftAreaWidth - gameControls.Width) / 2),
                    Math.Max(0, (toolbar.ClientSize.Height - gameControls.Height) / 2));
                patternControls.Location = new Point(
                    middleAreaStart + Math.Max(0, (middleAreaWidth - patternControls.Width) / 2),
                    Math.Max(0, (toolbar.ClientSize.Height - patternControls.Height) / 2));
                utilityControls.Location = new Point(
                    rightAreaStart + Math.Max(0, (rightAreaWidth - utilityControls.Width) / 2),
                    Math.Max(0, (toolbar.ClientSize.Height - utilityControls.Height) / 2));
                leftSeparator.Location = new Point(
                    middleAreaStart - leftSeparator.Width / 2,
                    Math.Max(0, (toolbar.ClientSize.Height - leftSeparator.Height) / 2));
                rightSeparator.Location = new Point(
                    rightAreaStart - rightSeparator.Width / 2,
                    Math.Max(0, (toolbar.ClientSize.Height - rightSeparator.Height) / 2));
            }

            toolbar.Resize += (s, e) => PositionControlGroups();
            gameControls.SizeChanged += (s, e) => PositionControlGroups();
            patternControls.SizeChanged += (s, e) => PositionControlGroups();
            utilityControls.SizeChanged += (s, e) => PositionControlGroups();
            PositionControlGroups();

            Controls.Add(toolbar);
        }

        private static string SpeedLabel(int v) => $"x{v}";

        private Button MakeButton(string text) => new Button
        {
            Text = text,
            Size = new Size(88, 26),
            FlatStyle = FlatStyle.Flat,
            BackColor = Color.FromArgb(8, 30, 80),
            ForeColor = TEXT_CLR,
            Font = _uiFont,
            Cursor = Cursors.Hand,
            Margin = new Padding(3, 11, 3, 0),
            FlatAppearance = { BorderColor = CELL_LO, BorderSize = 1 },
        };

        #endregion

        #region Simulacion

        //  Timer 
        private void SetupTimer()
        {
            _simTimer.Interval = 1000 / _targetFps;
            _simTimer.Tick += (s, e) => { Step(); _canvas.Invalidate(); };
        }

        private void TogglePlay()
        {
            _running = !_running;
            if (_running) _simTimer.Start(); else _simTimer.Stop();
            _btnPlay.Text = _running ? "PAUSAR" : "REANUDAR";
        }

        //  Grid 
        private void InitGrid()
        {
            _cols = 200;
            _rows = 120;
            _grid = new bool[_cols, _rows];
            _next = new bool[_cols, _rows];
        }

        private void FitMapToCanvas()
        {
            _zoom = MinZoom;
            int cellSize = CellSize;
            _offset.X = (_canvas.ClientSize.Width - _cols * cellSize) / 2f;
            _offset.Y = (_canvas.ClientSize.Height - _rows * cellSize) / 2f;
        }

        private readonly Random _rng = new Random();

        private void RandomSeed()
        {
            _generation = 0;
            _population = 0;
            for (int x = 0; x < _cols; x++)
                for (int y = 0; y < _rows; y++)
                    _grid[x, y] = _rng.NextDouble() < 0.30;
        }

        private void Reset()
        {
            _simTimer.Stop();
            _running = false;
            _generation = 0;
            _population = 0;
            _btnPlay.Text = "REANUDAR";
            for (int x = 0; x < _cols; x++)
                for (int y = 0; y < _rows; y++)
                    _grid[x, y] = false;
            _canvas.Invalidate();
        }

        //  Simulacion 
        private void Step()
        {
            int pop = 0;
            for (int x = 0; x < _cols; x++)
                for (int y = 0; y < _rows; y++)
                {
                    int n = CountNeighbours(x, y);
                    bool cur = _grid[x, y];
                    bool nxt = cur ? (n == 2 || n == 3) : (n == 3);
                    _next[x, y] = nxt;
                    if (nxt) pop++;
                }

            // swap buffers
            var tmp = _grid; _grid = _next; _next = tmp;
            _generation++;
            _population = pop;
        }

        private int CountNeighbours(int x, int y)
        {
            int c = 0;
            for (int dx = -1; dx <= 1; dx++)
                for (int dy = -1; dy <= 1; dy++)
                {
                    if (dx == 0 && dy == 0) continue;
                    int nx = (x + dx + _cols) % _cols;
                    int ny = (y + dy + _rows) % _rows;
                    if (_grid[nx, ny]) c++;
                }
            return c;
        }

        #endregion

        #region Renderizado

        //  Paint (usa directamente e.Graphics del panel con doble buffer) 
        private void Canvas_Paint(object sender, PaintEventArgs e)
        {
            Graphics g = e.Graphics;
            g.SmoothingMode = SmoothingMode.None;
            g.InterpolationMode = InterpolationMode.NearestNeighbor;
            g.PixelOffsetMode = PixelOffsetMode.Half;

            // Fondo
            g.Clear(BG);

            int cs = CellSize;
            float ox = _offset.X;
            float oy = _offset.Y;
            int w = _canvas.Width;
            int h = _canvas.Height;

            // Rejilla (solo cuando el zoom es suficiente)
            if (cs >= 5)
            {
                using var gp = new Pen(GRID_CLR, 0.5f);
                for (int x = 0; x <= _cols; x++)
                {
                    float px = ox + x * cs;
                    if (px < -1 || px > w + 1) continue;
                    g.DrawLine(gp, px, 0, px, h);
                }
                for (int y = 0; y <= _rows; y++)
                {
                    float py = oy + y * cs;
                    if (py < -1 || py > h + 1) continue;
                    g.DrawLine(gp, 0, py, w, py);
                }
            }

            // Celdas solo las visibles
            int startX = Math.Max(0, (int)(-ox / cs));
            int startY = Math.Max(0, (int)(-oy / cs));
            int endX = Math.Min(_cols, startX + (int)(w / cs) + 2);
            int endY = Math.Min(_rows, startY + (int)(h / cs) + 2);
            int pad = cs > 4 ? 1 : 0;

            using var cellBrush = new SolidBrush(CELL_LO);
            using var glowBrush = new SolidBrush(Color.FromArgb(40, 0, 180, 255));
            using var hiLiBrush = new SolidBrush(Color.FromArgb(120, 0, 255, 255));

            for (int x = startX; x < endX; x++)
            {
                for (int y = startY; y < endY; y++)
                {
                    if (!_grid[x, y]) continue;

                    float px = ox + x * cs + pad;
                    float py = oy + y * cs + pad;
                    int cw = Math.Max(1, cs - pad * 2);

                    if (cs >= 6)
                        g.FillRectangle(glowBrush, px - 1, py - 1, cw + 2, cw + 2);

                    g.FillRectangle(cellBrush, px, py, cw, cw);

                    if (cs >= 5)
                        g.FillRectangle(hiLiBrush, px, py, Math.Max(1, cw / 2), Math.Max(1, cw / 3));
                }
            }

            // HUD
            DrawHud(g, w, h);
        }

        private void DrawHud(Graphics g, int w, int h)
        {
            using var textBrush = new SolidBrush(TEXT_CLR);
            g.DrawString("CONWAY'S GAME OF LIFE", _titleFont, textBrush, 10, 8);
            g.DrawString($"Generación: {_generation:N0}", _uiFont, textBrush, 10, 28);
            g.DrawString($"Población: {_population:N0}", _uiFont, textBrush, 10, 44);

            // fps y zoom
            string info = $"Velocidad: {_targetFps} fps   Zoom: {(int)(_zoom * 100)}%";
            var sz = g.MeasureString(info, _uiFont);
            g.DrawString(info, _uiFont, textBrush, w - sz.Width - 10, 8);

            DrawStar(g, w - 30, h - 30, 14, TEXT_CLR);
        }

        private void DrawStar(Graphics g, float cx, float cy, float r, Color c)
        {
            using var p = new Pen(c, 1.5f);
            float r2 = r * 0.3f;
            for (int i = 0; i < 4; i++)
            {
                double a = Math.PI / 2 * i;
                g.DrawLine(p, cx, cy, (float)(cx + Math.Cos(a) * r), (float)(cy + Math.Sin(a) * r));
            }
            for (int i = 0; i < 4; i++)
            {
                double a = Math.PI / 4 + Math.PI / 2 * i;
                g.DrawLine(p, cx, cy, (float)(cx + Math.Cos(a) * r2), (float)(cy + Math.Sin(a) * r2));
            }
        }

        #endregion

        #region Raton

        //  Mouse 
        private void Canvas_MouseDown(object sender, MouseEventArgs e)
        {
            if (e.Button == MouseButtons.Right)
            {
                _panning = true;
                _panStart = e.Location;
                _canvas.Cursor = Cursors.SizeAll;
                return;
            }
            if (e.Button == MouseButtons.Left)
            {
                var (cx, cy) = ScreenToCell(e.Location);
                if (InBounds(cx, cy))
                {
                    bool[,] pat = null;
                    bool hasPattern = !string.IsNullOrEmpty(_selectedPattern)
                                      && Patterns.TryGetValue(_selectedPattern, out pat);

                    if (hasPattern && pat != null)
                    {
                        int ph = pat.GetLength(0);
                        int pw = pat.GetLength(1);
                        for (int dy = 0; dy < ph; dy++)
                            for (int dx = 0; dx < pw; dx++)
                            {
                                int gx = cx - pw / 2 + dx;
                                int gy = cy - ph / 2 + dy;
                                if (InBounds(gx, gy) && pat[dy, dx])
                                    _grid[gx, gy] = true;
                            }
                        _canvas.Invalidate();
                    }
                    else
                    {
                        _drawing = true;
                        _drawValue = !_grid[cx, cy];
                        _grid[cx, cy] = _drawValue;
                        _canvas.Invalidate();
                    }
                }
            }
        }

        private void Canvas_MouseMove(object sender, MouseEventArgs e)
        {
            if (_panning)
            {
                _offset.X += e.X - _panStart.X;
                _offset.Y += e.Y - _panStart.Y;
                _panStart = e.Location;
                ClampOffset();
                _canvas.Invalidate();
                return;
            }
            if (_drawing)
            {
                var (cx, cy) = ScreenToCell(e.Location);
                if (InBounds(cx, cy) && _grid[cx, cy] != _drawValue)
                {
                    _grid[cx, cy] = _drawValue;
                    _canvas.Invalidate();
                }
            }
        }

        private void Canvas_MouseUp(object sender, MouseEventArgs e)
        {
            _panning = _drawing = false;
            _canvas.Cursor = Cursors.Cross;
        }

        private void Canvas_MouseWheel(object sender, MouseEventArgs e)
        {
            float factor = e.Delta > 0 ? 1.15f : 1f / 1.15f;
            float newZoom = Math.Max(MinZoom, Math.Min(MaxZoom, _zoom * factor));
            float mx = e.X - _offset.X;
            float my = e.Y - _offset.Y;
            float scale = newZoom / _zoom;
            _offset.X = e.X - mx * scale;
            _offset.Y = e.Y - my * scale;
            _zoom = newZoom;
            ClampOffset();
            _canvas.Invalidate();
        }

        #endregion

        #region Teclado y viewport

        //  Teclado
        protected override bool ProcessCmdKey(ref Message msg, Keys keyData)
        {
            switch (keyData)
            {
                case Keys.Space: TogglePlay(); return true;
                case Keys.Right: Step(); _canvas.Invalidate(); return true;
                case Keys.R: Reset(); return true;
                case Keys.S: RandomSeed(); _canvas.Invalidate(); return true;
                case Keys.Add:
                case Keys.Oemplus: ChangeSpeed(10); return true;
                case Keys.Subtract:
                case Keys.OemMinus: ChangeSpeed(-10); return true;
            }
            return base.ProcessCmdKey(ref msg, keyData);
        }

        private void ChangeSpeed(int delta)
        {
            _targetFps = Math.Max(1, Math.Min(120, _targetFps + delta));
            _simTimer.Interval = 1000 / _targetFps;
        }

        //  Helpers 
        private (int x, int y) ScreenToCell(Point p)
        {
            int cs = CellSize;
            return ((int)((p.X - _offset.X) / cs), (int)((p.Y - _offset.Y) / cs));
        }

        private bool InBounds(int x, int y) => x >= 0 && x < _cols && y >= 0 && y < _rows;

        private void ClampOffset()
        {
            int cs = CellSize;
            int gridW = _cols * cs;
            int gridH = _rows * cs;
            int cw = _canvas.Width;
            int ch = _canvas.Height;

            float marginX = cw * 0.05f;
            float marginY = ch * 0.05f;

            _offset.X = ClampAxisOffset(_offset.X, gridW, cw, marginX);
            _offset.Y = ClampAxisOffset(_offset.Y, gridH, ch, marginY);
        }

        private static float ClampAxisOffset(float offset, int gridSize, int viewportSize, float margin)
        {
            float minOffset = viewportSize - gridSize - margin;
            if (minOffset > margin)
                return (viewportSize - gridSize) / 2f;

            return Math.Max(minOffset, Math.Min(margin, offset));
        }

        #endregion

        #region Musica

        private const string MusicAlias = "conwayMusic";
        private const string MusicResourcePrefix = "ConwaysGameOfLife.Music.";

        private void SetupMusic()
        {
            _musicTracks = Array.FindAll(
                typeof(FormMain).Assembly.GetManifestResourceNames(),
                resourceName => resourceName.StartsWith(MusicResourcePrefix, StringComparison.Ordinal)
                    && resourceName.EndsWith(".mp3", StringComparison.OrdinalIgnoreCase));
            Array.Sort(_musicTracks, StringComparer.Ordinal);
            if (_musicTracks.Length == 0)
            {
                DisableMusic("No se encontraron canciones MP3 incrustadas en el ejecutable.");
                return;
            }

            _musicTimer.Interval = 500;
            _musicTimer.Tick += MusicTimer_Tick;
            if (!TryStartRandomTrack(out string error))
            {
                DisableMusic(error);
                return;
            }

            _musicTimer.Start();
        }

        private void DisableMusic(string message)
        {
            _btnMusic.Enabled = false;
            _btnMusic.Text = "♫ INACTIVA";
            MessageBox.Show(this, message, "Música no disponible", MessageBoxButtons.OK, MessageBoxIcon.Warning);
        }

        private void MusicTimer_Tick(object? sender, EventArgs e)
        {
            if (_musicOutput?.PlaybackState == PlaybackState.Stopped
                && !TryStartRandomTrack(out string error))
            {
                _musicTimer.Stop();
                DisableMusic(error);
            }
        }

        private bool TryStartRandomTrack(out string error)
        {
            StopMusicTrack();

            int nextTrack = _rng.Next(_musicTracks.Length);
            if (_musicTracks.Length > 1 && nextTrack == _currentTrack)
                nextTrack = (nextTrack + _rng.Next(1, _musicTracks.Length)) % _musicTracks.Length;

            try
            {
                _musicStream = typeof(FormMain).Assembly.GetManifestResourceStream(_musicTracks[nextTrack]);
                if (_musicStream == null)
                    throw new InvalidOperationException($"No se encontró el recurso de música: {_musicTracks[nextTrack]}");

                _musicReader = new Mp3FileReader(_musicStream);
                _musicOutput = new WaveOutEvent();
                _musicOutput.Init(_musicReader);
                _musicOutput.Volume = _musicMuted ? 0f : 1f;
                _musicOutput.Play();
                _currentTrack = nextTrack;
                error = string.Empty;
                return true;
            }
            catch (Exception ex) when (ex is IOException
                || ex is InvalidOperationException
                || ex is COMException
                || ex is MmException
                || ex is ArgumentException)
            {
                StopMusicTrack();
                error = ex.Message;
                return false;
            }
        }

        private void StopMusicTrack()
        {
            if (_musicOutput != null)
            {
                if (_musicOutput.PlaybackState != PlaybackState.Stopped)
                    _musicOutput.Stop();
                _musicOutput.Dispose();
                _musicOutput = null;
            }

            _musicReader?.Dispose();
            _musicReader = null;
            _musicStream?.Dispose();
            _musicStream = null;
        }

        private void ToggleMusicMute()
        {
            bool muted = !_musicMuted;
            if (_musicOutput == null) return;
            _musicOutput.Volume = muted ? 0f : 1f;
            _musicMuted = muted;
            _btnMusic.Text = muted ? "♫ ACTIVAR" : "♫ MUTEAR";
            _btnMusic.AccessibleName = muted ? "Activar música" : "Silenciar música";
        }

        #endregion

        #region Cierre recursos

        // Dispose
        protected override void OnFormClosed(FormClosedEventArgs e)
        {
            _simTimer.Stop();
            _musicTimer.Stop();
            _musicTimer.Dispose();
            StopMusicTrack();
            _bgBrush?.Dispose();
            _uiFont?.Dispose();
            _titleFont?.Dispose();
            base.OnFormClosed(e);
        }

        #endregion

        #region Constructor patrones

        private static bool[,] BuildPulsar()
        {
            var p = new bool[13, 13];
            int[] cols = { 2, 3, 4, 8, 9, 10 };
            int[] rows1 = { 0, 5, 7, 12 };
            int[] rows2 = { 1, 2, 3, 4, 8, 9, 10, 11 };
            foreach (int r in rows1) foreach (int c in cols) p[r, c] = true;
            int[] edgeCols = { 0, 5, 7, 12 };
            foreach (int r in rows2) foreach (int c in edgeCols) p[r, c] = true;
            return p;
        }

        private static bool[,] BuildGosperGun()
        {
            var p = new bool[11, 38];
            var cells = new (int r, int c)[] {
                (5,1),(5,2),(6,1),(6,2),
                (5,11),(6,11),(7,11),(4,12),(8,12),(3,13),(9,13),(3,14),(9,14),
                (6,15),(4,16),(8,16),(5,17),(6,17),(7,17),(6,18),
                (3,21),(4,21),(5,21),(3,22),(4,22),(5,22),(2,23),(6,23),
                (1,25),(2,25),(6,25),(7,25),
                (3,35),(4,35),(3,36),(4,36)
            };

            foreach (var (r, c) in cells) p[r, c] = true;
            return p;
        }

        private void pictureBoxConwaysGame_Click(object sender, EventArgs e)
        {
        }

        #endregion
    }

    #region Dibujo doble buffer

    // Panel con doble buffer nativo
    public class DoubleBufferedPanel : Panel
    {
        public DoubleBufferedPanel()
        {
            SetStyle(
                ControlStyles.UserPaint |
                ControlStyles.AllPaintingInWmPaint |
                ControlStyles.OptimizedDoubleBuffer |
                ControlStyles.ResizeRedraw, true);
            UpdateStyles();
        }
    }

    #endregion
}
