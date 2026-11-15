namespace ConwaysGameOfLife
{
    partial class FormMain
    {

        private System.ComponentModel.IContainer components = null;

        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null))
                components.Dispose();
            base.Dispose(disposing);
        }

        private void InitializeComponent()
        {
            System.ComponentModel.ComponentResourceManager resources = new System.ComponentModel.ComponentResourceManager(typeof(FormMain));
            pictureBoxConwaysGame = new PictureBox();
            ((System.ComponentModel.ISupportInitialize)pictureBoxConwaysGame).BeginInit();
            SuspendLayout();
            // 
            // pictureBoxConwaysGame
            // 
            pictureBoxConwaysGame.BackgroundImage = (Image)resources.GetObject("pictureBoxConwaysGame.BackgroundImage");
            pictureBoxConwaysGame.BackgroundImageLayout = ImageLayout.Stretch;
            pictureBoxConwaysGame.InitialImage = null;
            pictureBoxConwaysGame.Location = new Point(1159, 653);
            pictureBoxConwaysGame.Name = "pictureBoxConwaysGame";
            pictureBoxConwaysGame.Size = new Size(37, 43);
            pictureBoxConwaysGame.TabIndex = 0;
            pictureBoxConwaysGame.TabStop = false;
            pictureBoxConwaysGame.Click += pictureBoxConwaysGame_Click;
            // 
            // FormMain
            // 
            BackColor = Color.FromArgb(4, 12, 36);
            ClientSize = new Size(1200, 700);
            Controls.Add(pictureBoxConwaysGame);
            Font = new Font("Consolas", 9F);
            ForeColor = Color.FromArgb(0, 220, 255);
            Icon = (Icon)resources.GetObject("$this.Icon");
            MaximizeBox = false;
            MinimumSize = new Size(600, 400);
            Name = "FormMain";
            StartPosition = FormStartPosition.CenterScreen;
            Text = "El Juego de la Vida - Conway";
            ((System.ComponentModel.ISupportInitialize)pictureBoxConwaysGame).EndInit();
            ResumeLayout(false);
        }
        private PictureBox pictureBoxConwaysGame;
    }
}
