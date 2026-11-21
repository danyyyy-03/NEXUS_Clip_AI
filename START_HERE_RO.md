# NEXUS Clip AI v0.1.1 — Instrucțiuni pentru Windows

## Ce face aplicația

- Transcrie vocea din clipuri audio și video local, folosind Faster-Whisper.
- Are interfață în limba engleză.
- Permite editarea subtitrărilor și exportul SRT, VTT, TXT.
- Poate adăuga o pistă selectabilă de subtitrări unui MP4, nu text imprimat definitiv.

## Pasul 1 — Python 3.12

Deschide CMD și verifică:

```bat
py -3.12 --version
```

Dacă lipsește, instalează Python 3.12 pentru Windows (64-bit) de pe https://www.python.org/downloads/.

## Pasul 2 — Extrage proiectul

Descarcă ZIP-ul, apoi click dreapta → **Extract All → Extract**. Deschide folderul `NEXUS_Clip_AI_v0.1.1`, unde sunt `setup.bat`, `run.bat`, `app.py`, `nexus_clip`, `tests`.

## Pasul 3 — Instalare

Dublu-click pe **setup.bat**. Programul creează un mediu separat `.venv` și instalează `faster-whisper`, `imageio-ffmpeg` și dependențele lor. La prima instalare este necesar internetul.

## Pasul 4 — Lansare

Dublu-click pe **run.bat**.

## Pasul 5 — Primul test

1. Apasă **Open video or audio** și alege un video/audio cu vorbire clară.
2. Alege modelul `tiny` și limba **English**, **Romanian** sau **Auto detect**.
3. Apasă **Transcribe locally**. La prima utilizare, modelul este descărcat în `%LOCALAPPDATA%\NEXUS_Clip_AI\models`.
4. Când apar subtitrările, dublu-click pe un rând pentru a-l corecta, apoi **Save caption**.
5. Apasă **Save SRT**, **Save VTT** sau **Save TXT**.
6. Pentru video, **Embed in MP4** creează un fișier nou cu subtitrare selectabilă.
7. Exporturile ajung implicit în `NEXUS_Clip_Exports`, lângă fișierul original.

## Testele automate

Dublu-click pe `test.bat` sau rulează:

```bat
py -3.12 -m unittest discover -s tests -v
```

Testele simulează recunoașterea AI; verificarea cu un clip real rămâne importantă.

## EXE experimental

După testarea aplicației, poți încerca `build.bat`. Executabilul ar trebui să apară în `dist\NEXUS_Clip_AI.exe`. Testează-l pe Windows înainte să-l distribui. Modelul Whisper nu este inclus în executabil.

## Depanare

- `No module named faster_whisper`: rulează `setup.bat`, apoi `run.bat`.
- `metadata_errors`: versiunea 0.1.1 conține deja corecția `av==17.1.0`. Pentru versiunea veche rulează `.venv\Scripts\python.exe -m pip install --force-reinstall --no-deps av==17.1.0`.
- Eroare la descărcarea modelului: verifică internetul și spațiul disponibil.
- MP4 export eșuat: codec-ul poate fi incompatibil; exportă SRT separat.
- Transcriere lentă: începe cu modelul `tiny`.
- Avertismente Windows pentru un EXE nesemnat: nu dezactiva protecțiile de securitate.

Nu folosi aplicația pentru înregistrări fără drepturile necesare. Verifică fiecare subtitrare înainte de publicare.
