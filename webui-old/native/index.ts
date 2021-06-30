import { app, BrowserWindow } from 'electron';

function createWindow () {
  const win = new BrowserWindow({
    width: 1024,
    height: 768,
    webPreferences: {
      nodeIntegration: true
    }
  })

  win.loadURL('http://localhost:8888');
  // win.webContents.openDevTools();
}

app.whenReady().then(createWindow)

app.on("window-all-closed", () => {
  app.quit();
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});