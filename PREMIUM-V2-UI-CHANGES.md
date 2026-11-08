# EdgeQuant Sentinel Premium v2 — actual navigation redesign

This update changes the **existing Tkinter UI only**:
- Hides the ttk Notebook tab strip through the Workspace.TNotebook.Tab layout.
- Uses the persistent left sidebar as the visible navigation for all existing pages.
- Enlarges the sidebar and updates its branding and active marker.
- Retains the existing live MT5 dashboard, LIMIT tracking, BE controls, Telegram and execution code.

The original trading engine `edgequant_auto.py` is unchanged.
The previous UI's old horizontal notebook tab strip is removed on Tk themes that support the style override.

## Testing
`python -m py_compile edgequant_desktop.py edgequant_auto.py` checks syntax.
GUI rendering and MT5 order execution require testing on a Windows machine.
This is a **navigation/layout correction**, not a pixel-perfect implementation of the approved concept.
