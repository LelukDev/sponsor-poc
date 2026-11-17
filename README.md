# Sponsorship offer: proof of concept

Demo of our moment of truth: a local business, named by the jury, becomes a sponsorship offer that uses the free slots of a club, with its logo placed on realistic photos (jersey, pitch boards, minibus, banner, bibs, tent).

The club, its members, its sponsors and its prices are made up. See `sponsor/club.py`.

## How it works

1. **Club profile** (editable in the app): 10 slots with a price, a status (free or taken), the current sponsor and its sector, plus the needs of the club and its fundraising goal.
2. **Guardrail** (`sponsor/guardrail.py`): alcohol, tobacco, gambling and vague names are stopped before any call to the AI.
3. **Choice and writing** (`sponsor/llm.py`): one call to a small model through OpenRouter (large model as backup). It builds three offers from the free slots, using the business and the needs of the club.
4. **Checks by the code**: only slots that are really free are kept, prices come from the inventory, and a competitor of a current sponsor is flagged.
5. **Realistic photos** (`sponsor/scenes.py`): the logo is placed in perspective, with the light of the support, on photos made once (`assets/scenes`). Current sponsors stay visible on the photos. This costs nothing at run time.

Measured cost: about $0.0006 per offer (`anthropic/claude-haiku-5.5`), 3.5 to 4.5 seconds of writing.

## Prepare new photos (optional)

```bash
python tools/gen_scene.py name "prompt with magenta rectangles"   # makes a base photo (about $0.07)
python tools/prepare_scenes.py                                    # finds the magenta zones and removes the magenta
```

## Documents

```bash
python dossier/calc.py            # all the numbers: writes dossier/numbers.md
python dossier/build_deck.py      # the 10-slide deck: dossier/deck.pdf
python dossier/build_report.py    # support report (A4): dossier/report.pdf
python tools/audit.py             # checks punctuation, language, numbers and PDFs
```

The product name, the demo link and the team names go in `dossier/deck_config.json`. Run the two build scripts again after you change it.

## Run it on your computer

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
echo "OPENROUTER_API_KEY=your_key" > .env      # this file is ignored by Git
streamlit run app.py
python -m pytest -q                              # tests with no network call
```

## Put it online (Streamlit Community Cloud)

1. On share.streamlit.io, sign in with GitHub and create an app: repository `sponsor-poc`, file `app.py`.
2. In *Advanced settings*, then *Secrets*, paste:
   ```toml
   OPENROUTER_API_KEY = "your_key"
   ```
3. Never commit the key. The demo allows 20 offers per visitor and 1,500 in total.
