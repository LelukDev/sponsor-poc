# Script de soutenance et préparation aux questions

Durée visée : **12 à 13 minutes** (le jury retire 1 point par minute au-delà de 15). Les 4 membres parlent. Remplacez A, B, C, D par vos prénoms.

## 1. Découpage et chrono

| Slide | Qui | Temps | Message en une phrase |
|---|---|---|---|
| 1 Problème | A | 1 min | Un trésorier bénévole écrit ses offres seul, le soir, et il reste des emplacements invendus. |
| 2 Solution | A | 1 min | Un nom de commerce entre, une offre adaptée au club avec le logo sur le matériel sort. |
| 3 Démo en direct | B | 3 min | Le jury choisit : on montre que l'outil s'adapte. |
| 4 Marché | C | 1 min | 56 100 clubs peuvent payer, on démarre avec 4 726. |
| 5 Modèle et prix | C | 1 min | 15 € par mois, soit 23 % de la valeur créée. |
| 6 Traction | D | 1 min | Pas de client payant : voici ce qui est prouvé et ce qu'on prouve en 30 jours. |
| 7 Concurrence | D | 1,5 min | Les autres rédigent ou courtent ; nous montrons le logo sur le vrai matériel. |
| 8 Équipe | tous | 0,5 min | Chacun se présente en une phrase. |
| 9 Financiers | C | 1 min | Seuil de rentabilité à 122 clubs, au mois 11. |
| 10 Demande | D | 0,5 min | 35 000 € pour 18 mois, trois jalons. |

**Première phrase (A), une personne, une douleur, un chiffre :** « Julien est trésorier bénévole d'un club de 320 licenciés. Le sponsoring pèse environ 9 % d'un budget d'environ 80 000 euros, et il écrit chaque offre seul, le soir. »

## 2. La démo (B), 3 minutes

Préparez ces cinq entrées avant. Ouvrez le lien 10 minutes avant le passage.

| # | Entrée | Ce que l'on doit voir | Rôle |
|---|---|---|---|
| 1 | Garage Martin | Minibus et bâche d'entrée, lien avec le besoin « renouveler le minibus » | facile |
| 2 | Pharmacie des Tilleuls | Barrières et chasubles (les familles), pas de minibus forcé | facile |
| 3 | Agence immobilière Century | Avertissement : le Groupe Lacroix Immobilier est déjà partenaire du secteur | difficile |
| 4 | Chez Momo | Validation humaine demandée : l'activité n'est pas claire | difficile |
| 5 | Cave à vins du Rhône | Blocage avant tout appel à l'IA (publicité encadrée) | hors périmètre |

Déroulé :
1. Contexte en une phrase : « Julien veut une offre pour un garage. »
2. Entrée choisie par le jury (pas la vôtre) : laissez-le taper un nom, importez **son** logo si possible.
3. Montrez le choix : « les emplacements pris ne sont jamais proposés ; le prix vient de la grille du club, pas de l'IA ».
4. Cas limite : un concurrent d'un sponsor, ou la cave à vins.
5. Chiffres : environ 0,0006 $ et 4 à 5 secondes pour la rédaction.

**Si le réseau tombe :** partage de connexion du téléphone. **Si l'app est endormie :** attendre quelques secondes, ne pas recharger plusieurs fois. **Jamais** : montrer la clé API ou le panneau *Secrets*. **Jamais** : une vidéo à la place de la démo.

## 3. Ce qu'il ne faut pas dire

- « Nous avons des clients » ou « des clubs ont validé » : faux à ce jour.
- « +30 % de sponsoring garanti » : c'est une hypothèse, la plus fragile du dossier.
- « Le marché fait X milliards » : notre marché est calculé de bas en haut, il est petit (1,53 M€ de marché atteignable).
- « Les photos sont générées en direct par l'IA » : non. Elles sont préparées une fois, le logo est posé par du code.
- « Aucun concurrent » : il y en a (All Sponsored, Leedeel, Spencer.club, SPONSO+, outils de dossiers).

## 4. Questions probables du jury et réponses

Chaque réponse s'appuie sur un chiffre ou une phrase du dossier ([dossier/chiffres.md](chiffres.md)). Apprenez la logique, pas le texte mot à mot.

**Choix du sujet (test des 3 questions, RICE)**
- *Pourquoi le sponsoring et pas les relances de cotisations, qui gagnent au RICE ?* Parce que le RICE favorise le volume, mais les relances sont déjà bien servies par des outils bon marché : c'est un « fill-in » à acheter. Le sponsoring est le seul à la fois utile (2/3 au test), à fort impact (+2,7 % du budget du club) et facile : un « quick win » sur la grille.
- *Vos notes de confiance sont-elles fiables ?* Non, ce sont des hypothèses écrites. La première action est d'appeler 10 clubs.

**ROI**
- *D'où vient le +30 % ?* C'est une hypothèse, pas une mesure. Elle est testée par 3 pilotes d'une saison (avant/après). Même à 30 % d'adoption, le prix reste à 31 % de la valeur, donc le modèle tient.
- *Quel est le mécanisme ?* Le club présente plus d'offres adaptées et signe plus de sponsors locaux. Gain net année 1 : 779 € pour un club moyen, 8 922 € pour un club phare.

**Persona, parcours, *moment of truth***
- *Quelle est la moment of truth ?* Un nom de commerce entre, une offre adaptée avec le logo sur le matériel du club sort. La démo la montre en direct sur l'entrée du jury.
- *Julien existe-t-il ?* Non, c'est un persona illustratif. Les trois douleurs sont des hypothèses à confirmer par 10 appels.

**Pile en 7 couches, construire ou acheter**
- *Qu'avez-vous construit, qu'avez-vous acheté ?* Nous construisons l'orchestration (choix des emplacements, vérifications) et l'interface. Nous achetons le modèle d'IA (petit par défaut, grand en secours) et l'hébergement. Nous nous appuyons sur des partenaires pour la distribution (districts, ligues).
- *Pourquoi une IA ici ?* Pour choisir les bons emplacements selon le commerce et le besoin, et rédiger. Les prix et la disponibilité sont dans le code : l'IA ne les invente pas.

**Coût par appel et passage à l'échelle**
- *Combien coûte une offre ?* Environ 0,0006 $ en rédaction (mesuré), 4 à 5 secondes. À 400 clubs : environ 4,3 $ par mois, soit 0,04 % du chiffre d'affaires. Avec le grand modèle : environ 85 $ par mois, 0,7 %.
- *Les photos coûtent-elles à chaque fois ?* Non : 7 photos de base générées une fois pour 0,47 $, puis le logo est posé par du code.
- *Votre latence dépasse 3 s ?* Oui, 4 à 5 s en rédaction. Piste : afficher le texte au fil de l'eau.

**Marché**
- *Comment avez-vous compté ?* De bas en haut : clubs qui signent × prix. 51 150 clubs moyens + 4 950 clubs phares en France = 18,1 M€ ; football et rugby = 4 726 clubs, 1,53 M€ ; en 3 ans, 400 clubs soit 136 800 € par an.
- *Qui signe 11 clubs par mois ?* Les districts et les ligues qui relaient l'outil, plus des appels directs. Aucun accord signé à ce jour.
- *Et la fiabilité de vos données ?* La répartition des clubs date de 2011-2012 et le total national (~165 000) est une source faible. À recouper avec le ministère des Sports ou l'INJEP.

**Modèle économique et prix**
- *Pourquoi un abonnement et pas un pourcentage des sponsors signés ?* Un pourcentage suit mieux la valeur, mais il est difficile à mesurer et peu prévisible. Nous gardons l'idée en option pour les clubs phares.
- *Pourquoi 15 € ?* C'est 23 % de la valeur mensuelle créée (65 €) et sous les 19 à 49 € que les clubs paient déjà pour un logiciel de gestion. Règle du cours : 10 à 30 % de la valeur.
- *Pourquoi ne pas viser les petits clubs ?* 66 % des clubs, mais leur sponsoring (environ 1 060 € par an) laisse moins de 100 € de gain net : ils ne peuvent pas payer.

**Concurrence et défense**
- *Qu'est-ce qui empêche un concurrent de vous copier ?* Rien sur la technique : un prompt et une interface se refont en un week-end. Notre défense : les données (quelles offres signent, par secteur et prix), la distribution (districts, ligues) et l'attachement au flux de travail (inventaire, historique des sponsors, renouvellements).
- *All Sponsored fait déjà ça ?* Il mesure la visibilité des clubs et fait du courtage. Il ne prépare pas une offre par commerce avec le logo posé sur le matériel du club.

**Financiers**
- *Pourquoi 35 000 € ?* Creux de trésorerie de 14 967 € plus six mois de charges fixes (18 000 €), arrondi.
- *Que se passe-t-il si vous signez deux fois moins de clubs ?* Le seuil de rentabilité (122 clubs) recule. Il faut relancer le calcul avec le fichier `dossier/calc.py`, et dire que la demande couvre alors moins de mois.

**Responsabilité (RGPD, AI Act, équité)**
- *Quelles données personnelles ?* Le PoC n'en traite pas : noms de commerces, club fictif. En production : données du club et contacts professionnels, hébergement dans l'UE à prévoir, durée de conservation à fixer.
- *Classe de risque dans l'AI Act ?* Risque limité : un texte généré par l'IA doit être signalé comme tel (c'est écrit sous le mail). Vérifier les dates d'application sur EUR-Lex avant la soutenance.
- *Équité ?* L'outil ne décide rien sur des personnes. Il y a un garde-fou métier : alcool, tabac et jeux d'argent sont écartés, et un concurrent d'un sponsor existant est signalé.
- *Quel est le garde-fou si l'IA se trompe ?* Le code vérifie que chaque emplacement proposé est libre et calcule les prix ; l'offre porte la mention « à relire avant envoi ».

**Une question par membre**
Chaque membre doit pouvoir expliquer seul : le chiffre qu'il présente, d'où il vient (source ou hypothèse), et ce qui le ferait changer. Répétez en vous interrogeant à tour de rôle sur le dossier de chiffres.

## 5. La veille

- [ ] Lien de la démo ouvert, testé avec un vrai logo (png et jpg) et les 5 entrées
- [ ] Deck PDF envoyé avant lundi 23 novembre, lien de la démo dans le mail
- [ ] Répétition chronométrée, de bout en bout, sous 13 minutes
- [ ] Téléphone prêt pour le partage de connexion, ordinateur chargé
- [ ] Chacun sait répondre aux questions de sa partie
