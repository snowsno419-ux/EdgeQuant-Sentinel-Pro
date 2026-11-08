EdgeQuant Sentinel - SINHALA VOICE CLIPS

SINHALA CLIPS INCLUDED
----------------------
    tp.wav           - take profit hit
    sl.wav           - stop loss hit
    be.wav           - break even moved
    filled.wav       - pending order triggered
    online.wav       - bot started
    summary.wav      - daily summary
    target.wav       - target milestone
    target_done.wav  - target reached
    update.wav       - periodic update
    nextplan.wav     - tomorrow's plan

LANGUAGE-SAFE PLAYBACK
----------------------
  When VOICE_LANG = "SI", the app only selects a Sinhala clip or an installed
  Sinhala Windows speech voice. It will NOT silently play/read an English
  voice as a Sinhala fallback.

  If an event has no Sinhala recording (for example loss_limit or weekend) and
  Windows does not have a Sinhala speech voice installed, that event is silent
  and a warning is written to the app log. Add a matching .wav file here, or
  install the Sinhala speech voice:

    Windows Settings -> Time & Language -> Language & region -> Add Sinhala
    -> install the Sinhala speech component. Then press REFRESH in the VOICE
    panel, or restart EdgeQuant.

  VOICE_MODE = AI uses the matching recorded clip. WINDOWS uses the installed
  language-matched Windows voice. BOTH uses both when that language's TTS voice
  is installed; with Sinhala selected and no Sinhala TTS, it uses the Sinhala
  recording only.

To add a recorded clip, use the exact event filename listed above, save it as
16-bit PCM WAV (22050 Hz), and place it in this folder.
