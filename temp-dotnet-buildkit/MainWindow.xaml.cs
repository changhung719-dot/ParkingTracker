using System.Windows;

namespace BuildKit;

public partial class MainWindow : Window
{
    public MainWindow()
    {
        InitializeComponent();
        using var port = new System.IO.Ports.SerialPort();
    }
}
