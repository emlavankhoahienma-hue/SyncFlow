using System;
using System.Diagnostics;
using System.IO;
using System.Windows.Forms;

namespace SyncFlowLauncher {
    static class Program {
        [STAThread]
        static void Main() {
            string pythonwPath = @"C:\Users\admin\AppData\Local\Programs\Python\Python312\pythonw.exe";
            if (!File.Exists(pythonwPath)) {
                // Fallback to python.exe if pythonw is not found
                pythonwPath = @"C:\Users\admin\AppData\Local\Programs\Python\Python312\python.exe";
            }

            string baseDir = AppDomain.CurrentDomain.BaseDirectory;
            string scriptDir = Path.Combine(baseDir, "syncflow-desktop");
            string scriptPath = Path.Combine(scriptDir, "main.py");

            if (!File.Exists(scriptPath)) {
                MessageBox.Show("Cannot find main.py at: " + scriptPath, "SyncFlow Launcher", MessageBoxButtons.OK, MessageBoxIcon.Error);
                return;
            }

            ProcessStartInfo psi = new ProcessStartInfo();
            psi.FileName = pythonwPath;
            psi.Arguments = "\"" + scriptPath + "\"";
            psi.WorkingDirectory = scriptDir;
            psi.UseShellExecute = false;
            psi.CreateNoWindow = true;
            psi.WindowStyle = ProcessWindowStyle.Hidden;

            try {
                Process.Start(psi);
            } catch (Exception ex) {
                MessageBox.Show("Failed to start SyncFlow: " + ex.Message, "SyncFlow Launcher Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }
    }
}
