# Optional offline Sinhala female voice — V4.8 integration preview

## What it is

- Model: Dialog/UoM `dialoglk/SinhalaVITS-TTS-F1`, female speaker Nipunika, VITS architecture, Sinhala (`si-LK`).
- Model card: <https://huggingface.co/dialoglk/SinhalaVITS-TTS-F1>
- The upstream model card declares **MPL-2.0**. Review the current model card/license before redistribution; EdgeQuant's source ZIP does not contain the checkpoint.
- The published model repository currently documents Coqui TTS 0.21.1 and the bundled Sinhala-to-Roman script. The optional Windows installer uses Python 3.11 in a separate virtual environment, CPU PyTorch 2.2.2, `TTS==0.21.1`, and soundfile. This choice is aligned to the upstream example, but **has not been validated on Windows in this workspace**.

## Installation on Windows

1. Extract the complete EdgeQuant package to a writable folder outside `Program Files`.
2. Start EdgeQuant and open the **VOICE** panel.
3. Press **INSTALL OFFLINE VOICE** and confirm. The installer opens in a separate console. It can take a long time and needs about 1 GB for the model plus several GB for the Python/PyTorch/TTS environment and temporary files.
4. Install Python 3.11 (64-bit) with the Windows `py` launcher if it is not already installed. The installer does not replace EdgeQuant's existing Python.
5. The installer downloads model/runtime files from Hugging Face/PyPI, synthesizes a sample, and tries to play it through Windows. It marks the runtime ready only after the test command succeeds.
6. Restart EdgeQuant or press **REFRESH**, set **LANGUAGE = SI**, and use **TEST TP** / **TEST ENTRY** before relying on spoken reports.

The installer asks separately before running. If it fails, read the console output and rerun after fixing the reported issue. A partially downloaded checkpoint uses a `.part` file and can resume when the installer is run again. The installer creates its environment and model files beside the app; keep those files on a local, writable drive.

## Privacy and routing

- The installed worker runs as a child process, binds **no network port**, and accepts text only from a private JSON file queue under `%LOCALAPPDATA%\EdgeQuantSentinel\sinhala_voice_queue`.
- Signal/report text, P&L values, account figures, channel names, prices, and order details are not sent to a TTS cloud service. They remain on the PC for synthesis and playback.
- Internet is needed only for the user's one-time installer downloads (Python packages from PyPI and public model files from Hugging Face). At speech time the local model and runtime are used.
- Sinhala routing prefers a detected matching **female** Windows SAPI voice; otherwise it uses the local female VITS model when ready. Figures, decimal digits, times, currency, and common trading acronyms are expanded into Sinhala word forms, then locally romanized and filtered to the model's published character vocabulary. Sinhala dynamic reports are not replaced by a static event clip and do not fall back to English. The resulting spoken forms and pronunciation quality still require a real listening test. If neither live-figure route accepts the report, the app logs that it was not spoken.
- UI/log terms are deliberate: **queued** means accepted into the local queue; **dispatched** means Windows SAPI was invoked; **played** is shown only after the local worker returns a successful playback result. Windows SAPI dispatch itself is not represented as confirmed playback.

## Limits and test status

This V4.8 code integration is a preview, not proof that the model works on a particular Windows PC. The following have **not** been verified in this workspace:

- Installing Python/TTS/PyTorch on Windows with this exact set of pinned versions.
- Loading the ~1 GB checkpoint/config through the selected Coqui runtime.
- Successful real-time or report-length synthesis, pronunciation quality, pacing, or CPU/RAM usage.
- Windows audio device playback, sleep/display-off interaction, or a complete user report round-trip.
- Building or testing the Windows/PyInstaller EXE.

The installer runs an on-device sample test when the user chooses it; its result is not assumed here. If the package/runtime changes later, repeat that Windows install, inference, and playback test before describing Sinhala speech as verified.
