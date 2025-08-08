# 📜 ARB – README

## 📌 Présentation du projet
ARB est un outil automatisé qui aide à signaler et enregistrer les interventions policières (rafles) en temps réel.  
Il utilise des données préformatées (JSON) pour conserver les informations sur chaque événement : localisation, type d’intervention, agents présents, temps d’attente, etc.  
Le but est de **collecter, analyser et éventuellement alerter des réseaux de soutien**.

---

## 🗂 Structure du projet

Voici les fichiers principaux :
- **`ARB.py`**  
  Le programme principal qui lit les données et les traite.  
  C’est ici que s’effectuent la lecture des fichiers JSON, l’analyse des informations, et éventuellement leur affichage ou traitement.
  
- **`report.json`**  
  Exemple de fichier de données.  
  Contient les informations d’une intervention (date, lieu, type, nombre d’agents, issue, etc.) au format JSON.

---

## 🔧 Pré-requis pour exécuter le bot
Pas besoin de connaissances techniques poussées, mais il faut installer les outils de base :

1. **Installer Python** (version 3.9 ou plus récente)  
   - Sur Windows : télécharger depuis [python.org](https://www.python.org/downloads/) et cocher *"Add Python to PATH"*.  
   - Sur Mac : déjà installé dans la plupart des cas.  
   - Sur Linux : utiliser la commande  
     ```bash
     sudo apt install python3
     ```

2. **Télécharger les fichiers du projet**  
   Mets `AntiRafleBot.py` et `report.json` dans le même dossier.

3. **Installer les bibliothèques nécessaires**  
   Dans un terminal, exécute :  
   ```bash
   pip install requests
   ```
   *(si d’autres dépendances sont ajoutées plus tard, elles seront listées ici)*

---

## ▶️ Comment exécuter le bot
1. Ouvre un terminal dans le dossier contenant les fichiers.
2. Lance le script avec :  
   ```bash
   python AntiRafleBot.py
   ```
3. Le programme lira le fichier `report.json` et affichera les informations sur la dernière intervention enregistrée.

---

## 📂 Fonctionnement interne
- Le script lit **`report.json`** qui contient des données structurées.
- Ces données sont ensuite **interprétées** pour être affichées ou envoyées.
- Les champs typiques dans `report.json` sont :
  - `location_type` : type de lieu (ex. métro)
  - `other_location` : précision du lieu
  - `time_delta` : durée estimée depuis l’événement
  - `agents` : type et nombre d’agents présents
  - `intervention_type` : type d’intervention
  - `target_count` : nombre de personnes ciblées
  - `issue` : issue de l’intervention
  - `contact` : contact établi ou non

---

## 📌 Bonnes pratiques pour continuer le développement
- **Toujours tester avec un fichier JSON de test** avant d’utiliser en conditions réelles.
- **Sauvegarder les anciens rapports** dans un dossier `archives/` pour conserver un historique.
- **Commenter le code** pour que les prochaines personnes comprennent les changements.
- **Documenter chaque nouvelle fonctionnalité** dans ce README.

---

## 🛠 TODO – Évolutions prévues

1. **Bot d’alerte Signal/Télégram** *(à faire)*  
   - Permettre l’envoi automatique d’un message sur Signal ou Telegram lorsqu’une nouvelle intervention est détectée.
   - **Idée d’implémentation** :
     - Surveiller un dossier ou un flux de données pour détecter un nouveau `report.json`.
     - Utiliser l’API Telegram Bot ou une intégration Signal pour envoyer :
       - La localisation
       - Le type d’intervention
       - Le nombre d’agents
       - L’heure
   - Objectif : prévenir rapidement un groupe de soutien.

2. **Interface graphique simple** pour visualiser les rapports.
3. **Envoi automatique des rapports** vers un serveur central ou une base de données.
4. **Ajout de géolocalisation sur carte** (via Google Maps ou OpenStreetMap).
5. **Mode temps réel** pour enregistrer les événements au fur et à mesure.
