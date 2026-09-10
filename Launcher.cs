using System;
using System.Diagnostics;
using System.IO;
using System.Windows.Forms;

namespace SyncFlowLauncher {
    static class Program {
        [STAThread]
        static void Main() {
            string pythonPath = @"C:\Users\admin\AppData\Local\Programs\Python\Python312\python.exe";
            if (!File.Exists(pythonPath)) {
                pythonPath = @"C:\Users\admin\AppData\Local\Programs\Python\Python312\pythonw.exe";
            }

            string baseDir = AppDomain.CurrentDomain.BaseDirectory;
            string scriptDir = Path.Combine(baseDir, "syncflow-desktop");
            string scriptPath = Path.Combine(scriptDir, "main.py");

            if (!File.Exists(scriptPath)) {
                MessageBox.Show("Không tìm thấy main.py tại: " + scriptPath, "SyncFlow Launcher", MessageBoxButtons.OK, MessageBoxIcon.Error);
                return;
            }

            ProcessStartInfo psi = new ProcessStartInfo();
            psi.FileName = pythonPath;
            psi.Arguments = "\"" + scriptPath + "\"";
            psi.WorkingDirectory = scriptDir;
            psi.UseShellExecute = false;
            psi.CreateNoWindow = true;
            psi.WindowStyle = ProcessWindowStyle.Hidden;

            try {
                Process.Start(psi);
            } catch (Exception ex) {
                MessageBox.Show("Lỗi khởi động SyncFlow: " + ex.Message, "SyncFlow Launcher Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }
    }
}
