# Dossier de chiffres : une seule source pour tout le pitch

Légende : **[S]** source citée ; **[M]** mesuré sur le PoC ; **[H]** hypothèse à tester auprès de vrais clubs.

Généré par `dossier/calc.py`. Changer une hypothèse en tête du fichier, relancer, et tous les chiffres suivent.

## 1. Fiche de faits : le marché des clubs sportifs amateurs

| Fait | Valeur | Statut |
|---|---|---|
| Clubs en France | ~165 000 | [S] source faible (Wikipédia 2020) |
| Clubs intermédiaires | 31% des clubs, budget moyen 80 145 € | [S] CNOSF, données anciennes |
| Clubs phares | 3% des clubs, budget moyen 917 857 € | [S] idem |
| Clubs de proximité | 66% des clubs, budget moyen 11 832 € | [S] idem, **exclus** (trop petit pour payer) |
| Part des partenariats dans les ressources | 9% | [S] CNOSF 2020 |
| Prix d'un logiciel de gestion de club | 19 à 49 € / mois | [S] comparateurs 2026 |
| Prix des supports | panneau 500-750 € HT ; maillot 1 500-5 000 € / saison ; minibus : aucune donnée | [S] une plaquette de rugby et un blog d'agence |
| Grille de la démo (10 emplacements, € par saison) | Barnum 300, Chasubles 350, Short 400, Bâche d'entrée 500, Manche 600, Barrière principale 600, Dos 700, Minibus 800, Barrières x3 900, Maillot poitrine 1 500 | [H] bas de fourchette |

## 2. Choix du use case (S1)

**Test des 3 questions** (payer, changer de concurrent, dégrader un chiffre) : 2 ou 3 oui = must-have.

| Use case | Pay | Switch | Degrade | Total | Fait |
|---|---|---|---|---|---|
| Propositions de sponsoring + maquettes | oui | non | oui | 2/3 **must-have** | sponsoring = 9 % des ressources ; 45 % des clubs peinent à couvrir leurs dépenses |
| Convocations / dispos depuis WhatsApp | non | non | oui | 1/3 nice-to-have | des outils gratuits existent (ClubPal, Kalisport Core) |
| Relances de cotisations | oui | non | oui | 2/3 **must-have** | cotisations = 68 % des ressources ; outils déjà payés (19 à 49 €/mois) |
| Dossiers de subvention | oui | non | oui | 2/3 **must-have** | subventions = 16 % des ressources ; rédaction longue pour des bénévoles |
| Comptes rendus de match (site, réseaux) | non | non | non | 0/3 nice-to-have | aucun chiffre ne bouge si on le retire |
| Planning des bénévoles (buvette, tournois) | non | non | oui | 1/3 nice-to-have | gain de temps sans euro mesurable |

**RICE** (must-have seulement) : R = événements par trimestre, I = 3 massif / 1 moyen, C = confiance, E = mois-personne [H].

| Use case | R | I | C | E | RICE |
|---|---|---|---|---|---|
| Relances de cotisations | 150 | 1 | 80% | 3 | 40,0 |
| Propositions de sponsoring + maquettes | 45 | 3 | 50% | 2 | 33,8 |
| Dossiers de subvention | 1,5 | 3 | 50% | 3 | 0,8 |

**ICE et grille impact-facilité** (impact = hausse du budget du club ; seuil 5,5).

| Use case | Impact | Confiance | Facilité | ICE | Quadrant | Calcul de l'impact |
|---|---|---|---|---|---|---|
| Relances de cotisations | 5 | 8 | 7 | 280 | Fill-in (acheter du tout fait) | +1,4 % du budget (2 pts de 68 %) |
| Propositions de sponsoring + maquettes | 8 | 5 | 6 | 240 | Quick win | +2,7 % du budget (30 % de 9 %) |
| Dossiers de subvention | 7 | 5 | 4 | 140 | Big bet | +2,4 % du budget (15 % de 16 %) |

**Lecture honnête.** Les relances de cotisations gagnent au RICE et à l'ICE grâce au volume et à la confiance, mais leur impact reste sous le seuil : des outils bon marché existent déjà, donc c'est un « fill-in » à acheter. Les propositions de sponsoring sont le seul use case à la fois must-have, à fort impact et facile : un quick win. Toutes les notes de confiance sont des hypothèses : la première action est d'appeler 10 clubs pour les tester.

## 3. ROI : hausse du sponsoring (S1)

Archétype : **revenue uplift**. Mécanisme nommé : *le club présente plus de propositions personnalisées et signe plus de sponsors locaux.*

| | Club intermédiaire | Club phare |
|---|---|---|
| Budget moyen [S] | 80 145 € | 917 857 € |
| Sponsoring actuel (9 %) | 7 213 € | 82 607 € |
| Hausse possible à plein régime (30%) [H] | 2 164 € | 24 782 € |
| Gain net année 1 (adoption 40%, 90% net) [H] | **779 €** | **8 922 €** |
| Valeur par mois | 64,9 € | 743,5 € |
| Prix de l'outil par an | 180 € | 1 800 € |
| ROI année 1 | 333% | 396% |

**Phrase du cours :** « En année 1, un club intermédiaire signe pour 779 € de sponsoring net en plus (hausse de 30% du sponsoring, adoption de 40%) ; un club phare, 8 922 €. »

**Sensibilité à l'adoption :**

| Adoption | Gain net intermédiaire | Gain net phare | Prix en % de la valeur (inter. / phare) |
|---|---|---|---|
| 30% | 584 € | 6 691 € | 31% / 27% |
| 40% | 779 € | 8 922 € | 23% / 20% |
| 50% | 974 € | 11 152 € | 18% / 16% |
| 60% | 1 169 € | 13 382 € | 15% / 13% |

## 4. Marché bottom-up (S4)

Client qui signe : **le club** (le trésorier ou le président). Deux plans : Club intermédiaire et Club phare.

| | Clubs | × ARPA | = Marché |
|---|---|---|---|
| **TAM** : clubs intermédiaires + phares en France | 51 150 + 4 950 | 180 € / 1 800 € | **18,1 M€** |
| **SAM** : football + rugby (démo et réseaux de districts) | 4 309 + 417 = 4 726 | idem | **1,53 M€** |
| **SOM** : 3 ans | 360 + 40 = 400 clubs (8,5% du SAM) | idem | **136 800 € ARR** |

Contrôle : 400 clubs en 36 mois = **11,1 nouveaux clubs par mois**. Qui les signe ? Les districts et les ligues, qui relaient l'outil à leurs clubs (partenariat à négocier [H]), plus de l'appel direct.

Les petits clubs de proximité sont exclus du TAM : leur sponsoring (9 % de ~11 800 €, soit ~1 060 €) laisse moins de 100 € de gain net par an.

## 5. Modèle économique et prix (S4)

Modèle : **abonnement SaaS par club**, deux plans selon la taille (le prix suit la valeur créée, qui augmente avec le budget).

| | Club intermédiaire | Club phare |
|---|---|---|
| Prix | **15 € / mois** | **150 € / mois** |
| Part de la valeur captée | 23% | 20% |
| Coût de service [H] | 3 € / mois | 12 € / mois |
| Marge brute | 80% | 92% |

**Phrase du cours :** « 15 € par mois, soit 23% des 65 € de valeur mensuelle créée, pour un coût de service de 3 € ; 150 € par mois pour un club phare, soit 20% de 743 €. »

Le prix reste sous les 19 à 49 € d'un logiciel de gestion : l'outil est un complément léger, pas un remplaçant. À 10-30 % de la valeur, il suit la règle du cours.

**Ne pas confondre deux prix.** Les 500 / 800 / 1 500 € de la démo sont ce que **le club** facture **au commerce sponsor**, par saison. Les 15 et 150 € par mois sont ce que **nous** facturons **au club**.

## 5 bis. Traction (slide 6) : ce qu'on peut dire honnêtement

- Aucun client à ce jour : ne pas en prétendre.
- Prouvé : un PoC en ligne qui produit une proposition en 4 à 5 s pour environ 0,0006 $, sur n'importe quel commerce choisi par le jury.
- Plan de pilote chiffré : 3 clubs intermédiaires, 1 saison, mesure avant/après du sponsoring signé (hypothèse +30 %). Succès : au moins +15 % ou 2 nouveaux sponsors par club.
- À obtenir avant la soutenance si possible : 10 appels à des clubs, 2 ou 3 retours à citer, et une lettre d'intention d'un club ou d'un district. Seulement des retours réels.

## 6. Coût de l'IA, mesuré puis projeté (S3 et S5)

- Une proposition = 1 appel (le modèle lit l'inventaire du club et choisit les emplacements), 1560 tokens en entrée, 780 en sortie **[M]**.
- Les photos réalistes sont générées une seule fois (7 images, environ 0,47 $ au total) ; la pose du logo se fait ensuite par code, sans coût ni appel réseau.
- Petit modèle (claude-haiku-5.5, 0,10 / 0,50 $ par million) : **0,00055 $** par proposition ; temps de rédaction mesuré : 3,5 à 4,5 s.
- Grand modèle (claude-sonnet-5.5, 2 / 10 $ par million) : 0,01092 $ par proposition.
- À l'échelle du SOM : 7 800 propositions par mois, soit **4,3 $ par mois** avec le petit modèle (0,04% du chiffre d'affaires mensuel), 85 $ avec le grand modèle (0,7%).
- Le coût de l'IA n'est donc pas le sujet : l'hébergement et le support dominent. Le temps de rédaction mesuré (3,5 à 4,5 s) dépasse la cible de 3 s du cours ; piste : afficher le texte au fil de l'eau.

## 7. Financiers (S4 et S5)

- Clients à 36 mois : 400 (360 + 40), montée linéaire.
- Revenu mensuel à 36 mois : **11 400 €** (136 800 € ARR). Prix moyen 28,5 €, coût de service moyen 3,9 €, marge brute **86%**.
- Charges fixes : 3 000 € par mois [H].
- **Seuil de rentabilité : 122 clubs**, atteint au **mois 11**.
- Trésorerie la plus basse avant rentabilité : **14 967 €**.
- **Demande : 35 000 € pour 18 mois**, soit le creux de trésorerie plus 6 mois de charges de marge. Jalon : 122 clubs payants (dont une dizaine de plans phares) et un accord avec au moins un district.

| Mois | Clubs | Revenu mensuel | Résultat du mois | Trésorerie cumulée |
|---|---|---|---|---|
| 6 | 67 | 1 900 € | -1 360 € | -12 260 € |
| 12 | 133 | 3 800 € | 280 € | -14 680 € |
| 18 | 200 | 5 700 € | 1 920 € | -7 260 € |
| 24 | 267 | 7 600 € | 3 560 € | 10 000 € |
| 36 | 400 | 11 400 € | 6 840 € | 74 040 € |

## 8. Ce qui reste à prouver

1. Que l'outil fait vraiment monter le sponsoring : l'hypothèse +30 % est la plus fragile. Test : 3 clubs pilotes, avant/après sur une saison.
2. Que des clubs paient 15 ou 150 € par mois : appeler 10 clubs intermédiaires cette semaine.
3. Que les districts relaient l'outil : 2 ou 3 conversations.
4. Les données de répartition des clubs datent de 2011-2012 et le total national est une source faible : à recouper avec le ministère des Sports ou l'INJEP.
5. Aucun tarif de minibus trouvé : le prix de 800 € est une hypothèse.
