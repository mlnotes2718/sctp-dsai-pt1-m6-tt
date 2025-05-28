# Voice Issue

## Windows

1. **Install a binary wheel via `pipwin`** (easiest, no compiler needed):

   ```bash
   pip install pipwin
   pipwin install pyaudio
   ```

2. **Or** download and install a pre-built wheel:

   * Go to [www.lfd.uci.edu/\~gohlke/pythonlibs](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio)
   * Download the wheel matching your Python version and architecture (e.g. `PyAudio-0.2.11-cp39-cp39-win_amd64.whl`)
   * Install with:

     ```bash
     pip install path\to\PyAudio-0.2.11-cp39-cp39-win_amd64.whl
     ```

3. **If you really want to compile from source** (not usually necessary):

   * Install the Microsoft Visual C++ Build Tools.
   * Then `pip install pyaudio` will compile against the bundled PortAudio.

---

## macOS

1. **Install PortAudio via Homebrew**:

   ```bash
   brew install portaudio
   ```

2. **Tell `pip` where to find it**:

   ```bash
   export LDFLAGS="-L/usr/local/lib"
   export CPPFLAGS="-I/usr/local/include"
   pip install pyaudio
   ```

   *(If your Homebrew prefix is different—e.g. on Apple Silicon—it might be `/opt/homebrew` instead of `/usr/local`.)*

3. **Or** install via Conda if you’re using Anaconda/Miniconda:

   ```bash
   conda install -c anaconda pyaudio
   ```

---

## Linux (Debian/Ubuntu)

1. **Install PortAudio dev headers**:

   ```bash
   sudo apt update
   sudo apt install portaudio19-dev libportaudiocpp0 ffmpeg
   ```

2. **Re-install PyAudio**:

   ```bash
   pip install --no-cache-dir pyaudio
   ```

   Or via Conda:

   ```bash
   conda install -c anaconda pyaudio
   ```

---

## Verifying the Fix

After installation, in a Python shell run:

```python
import pyaudio
print(pyaudio.get_portaudio_version_text())
```

You should see something like:

```
PortAudio V19.6.0-devel, revision 494...
```

If that prints without error, you’re all set!

---

### Common Pitfalls

* **Virtual environments:** Make sure you install PortAudio/PyAudio into the same environment you’re running your script from.
* **Multiple Python installs:** Check `which python` (or `where python`) vs. `pip --version` to ensure they align.
* **Permissions:** On Linux/macOS, if you see permission errors, try installing in user-mode: `pip install --user pyaudio`.

Feel free to let me know your OS and the exact commands you’ve tried if you still hit issues!
