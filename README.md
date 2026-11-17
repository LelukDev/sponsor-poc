# Proposition de sponsoring : PoC

Démo du moment de vérité (*moment of truth*) : un commerce local, cité par le jury, devient une proposition de sponsoring avec le logo posé sur un maillot, un minibus et un panneau de stade.

Club, effectifs et prix : fictifs, voir `sponsor/club.py` et `sponsor/pricing.py`.

## Fonctionnement

1. Garde-fou (`sponsor/guardrail.py`) : alcool, tabac, jeux d'argent, nom trop vague. Aucun appel d'IA dans ces cas.
2. Rédaction (`sponsor/llm.py`) : un appel à un petit modèle via OpenRouter, grand modèle en secours.
3. Prix : grille fixe, jamais produite par l'IA.
4. Maquettes (`sponsor/mockups.py`) : dessins SVG, logo importé ou nom du commerce.

Coût mesuré : environ 0,0004 $ et 3 à 4 secondes par proposition (modèle `anthropic/claude-haiku-5.5`).

## Lancer en local

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
echo "OPENROUTER_API_KEY=votre_cle" > .env      # fichier ignoré par Git
streamlit run app.py
python -m pytest -q                              # tests sans appel réseau
```

## Mettre en ligne (Streamlit Community Cloud)

1. Sur share.streamlit.io, se connecter avec GitHub et créer une app : dépôt `sponsor-poc`, fichier `app.py`.
2. Dans *Advanced settings* > *Secrets*, coller :
   ```toml
   OPENROUTER_API_KEY = "votre_cle"
   ```
3. Ne jamais commiter la clé. La démo limite à 20 générations par session et 1 500 au total.
