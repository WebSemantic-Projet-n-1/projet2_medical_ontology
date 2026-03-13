# Extensions web

Shared source for Chrome (MV3) and Firefox (MV2). The active manifest is always `manifest.json`.
Named copies (`manifest-chrome.json`, `manifest-firefox.json`) are the source of truth for each browser.

## Switching targets

Run `build.ps1` from the `extensions/` folder:

```powershell
.\build.ps1 -Target firefox   # switch to Firefox (MV2)
.\build.ps1 -Target chrome    # switch to Chrome  (MV3)
```

Then reload the `extensions/` folder as an unpacked extension in your browser.

## Firefox

Load via `about:debugging` → "This Firefox" → "Load Temporary Add-on" → select any file in `extensions/`.

## Chrome

Load via `chrome://extensions` → "Load unpacked" → select the `extensions/` folder.

https://developer.chrome.com/docs/extensions/get-started/tutorial/hello-world
