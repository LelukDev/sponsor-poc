# Proposition de sponsoring : PoC

Démo du moment de vérité (*moment of truth*) : un commerce local, cité par le jury, devient une proposition de sponsoring qui tient compte des emplacements libres du club, avec son logo posé sur des photos réalistes (maillot, barrières, minibus, bâche, chasubles, barnum).

Club, effectifs, sponsors et prix : fictifs, voir `sponsor/club.py`.

## Fonctionnement

1. **Profil du club** (modifiable dans l'application) : 10 emplacements avec prix, statut libre ou pris, sponsor actuel et son secteur ; besoins du club ; objectif de collecte.
2. **Garde-fou** (`sponsor/guardrail.py`) : alcool, tabac, jeux d'argent, nom trop vague. Aucun appel d'IA dans ces cas.
3. **Choix et rédaction** (`sponsor/llm.py`) : un appel à un petit modèle via OpenRouter (grand modèle en secours). Il choisit trois offres parmi les emplacements libres, selon le commerce et les besoins du club.
4. **Vérification par le code** : seuls les emplacements réellement libres sont gardés, les prix viennent de l'inventaire, un concurrent d'un sponsor existant est signalé.
5. **Photos réalistes** (`sponsor/scenes.py`) : le logo est posé en perspective, avec la lumière du support, sur des photos générées une fois (dossier `assets/scenes`). Les sponsors déjà en place apparaissent sur les photos. Aucun coût à l'exécution.

Coût mesuré : environ 0,0006 $ par proposition (modèle `anthropic/claude-haiku-5.5`), 3,5 à 4,5 s de rédaction.

## Préparer de nouvelles photos (facultatif)

```bash
python tools/gen_scene.py nom "prompt avec rectangles magenta"   # génère une photo de base (environ 0,07 $)
python tools/prepare_scenes.py                                   # détecte les zones magenta, efface le magenta
```

## Livrables du dossier

```bash
python dossier/calc.py            # chiffres : écrit dossier/chiffres.md
python dossier/build_deck.py      # deck de 10 slides : dossier/deck.pdf
python dossier/build_report.py    # rapport A4 : dossier/report.pdf
python tools/audit.py             # audit : ponctuation, cohérence des chiffres, PDF
```

Le nom du produit, le lien de la démo et les noms de l'équipe se renseignent dans `dossier/deck_config.json`, puis on relance les deux constructions.

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
