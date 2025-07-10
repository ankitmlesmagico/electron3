const { app, BrowserWindow, ipcMain } = require('electron')
const { spawn } = require('child_process')
const path = require('path')
const os = require('os')
const fs = require('fs')

let pythonProcess = null

function createWindow() {
  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
    },
    icon: path.join(__dirname, 'icon.png'), // Add your app icon
  })

  win.loadFile('index.html')

  // Open DevTools in development
  if (!app.isPackaged) {
    win.webContents.openDevTools()
  }
}

function getExecutablePath() {
  if (app.isPackaged) {
    // In production, use the bundled executable
    const executableName =
      process.platform === 'win32' ? 'WebAgent.exe' : 'WebAgent'
    return path.join(process.resourcesPath, 'python-executable', executableName)
  } else {
    // In development, use python3 directly
    return 'python3'
  }
}

function getExecutableArgs() {
  if (app.isPackaged) {
    // No args needed for the standalone executable
    return []
  } else {
    // In development, pass the script path
    return [path.join(__dirname, 'webautomate_ai', 'agent.py')]
  }
}

function setupEnvironment() {
  const envPath = app.isPackaged
    ? path.join(process.resourcesPath, 'python-executable', '.env')
    : path.join(__dirname, 'webautomate_ai', '.env')

  // Set up environment variables
  const env = { ...process.env }

  if (fs.existsSync(envPath)) {
    // Load .env file if it exists
    const envContent = fs.readFileSync(envPath, 'utf8')
    envContent.split('\n').forEach((line) => {
      const [key, value] = line.split('=')
      if (key && value) {
        env[key.trim()] = value.trim()
      }
    })
  }

  // Set Playwright browsers path for bundled version
  if (app.isPackaged) {
    env.PLAYWRIGHT_BROWSERS_PATH = path.join(
      process.resourcesPath,
      'python-executable',
      'playwright-browsers'
    )
  }

  return env
}

ipcMain.on('start-python', (event) => {
  if (pythonProcess) {
    event.sender.send(
      'python-output',
      '[INFO] Python process is already running.\n'
    )
    return
  }

  const executablePath = getExecutablePath()
  const args = getExecutableArgs()
  const env = setupEnvironment()

  console.log('Executable path:', executablePath)
  console.log('Arguments:', args)
  console.log('Working directory:', os.homedir())

  // Check if executable exists (in production)
  if (app.isPackaged) {
    if (!fs.existsSync(executablePath)) {
      event.sender.send(
        'python-output',
        `[ERROR] Python executable not found at: ${executablePath}\n`
      )
      return
    }

    // Make sure it's executable (important for Linux)
    try {
      fs.chmodSync(executablePath, '755')
    } catch (error) {
      console.error('Error setting executable permissions:', error)
    }
  }

  // Use user's home directory as working directory
  const userHome = os.homedir()

  pythonProcess = spawn(executablePath, args, {
    cwd: userHome,
    env: env,
    stdio: ['pipe', 'pipe', 'pipe'],
  })

  // Handle process startup
  pythonProcess.stdout.on('data', (data) => {
    const output = data.toString()
    console.log('Python stdout:', output)
    event.sender.send('python-output', output)
  })

  pythonProcess.stderr.on('data', (data) => {
    const error = data.toString()
    console.error('Python stderr:', error)
    event.sender.send('python-output', `[ERROR] ${error}`)
  })

  pythonProcess.on('close', (code) => {
    const message = `\n[WebAgent exited with code ${code}]\n`
    console.log(message)
    event.sender.send('python-output', message)
    pythonProcess = null
  })

  pythonProcess.on('error', (error) => {
    const errorMessage = `[ERROR] Failed to start WebAgent: ${error.message}\n`
    console.error(errorMessage)
    event.sender.send('python-output', errorMessage)
    pythonProcess = null
  })

  // Send initial message
  event.sender.send('python-output', '[INFO] Starting WebAgent...\n')
})

ipcMain.on('python-input', (event, input) => {
  if (pythonProcess && pythonProcess.stdin.writable) {
    pythonProcess.stdin.write(input + '\n')
  } else {
    event.sender.send(
      'python-output',
      '[ERROR] WebAgent is not running or not ready for input.\n'
    )
  }
})

ipcMain.on('stop-python', (event) => {
  if (pythonProcess) {
    pythonProcess.kill('SIGTERM')
    event.sender.send('python-output', '[INFO] Stopping WebAgent...\n')
  }
})

// App event handlers
app.whenReady().then(() => {
  createWindow()

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow()
    }
  })
})

app.on('window-all-closed', () => {
  // Clean up Python process
  if (pythonProcess) {
    pythonProcess.kill('SIGTERM')
  }

  if (process.platform !== 'darwin') {
    app.quit()
  }
})

app.on('before-quit', () => {
  // Clean up Python process
  if (pythonProcess) {
    pythonProcess.kill('SIGTERM')
  }
})
