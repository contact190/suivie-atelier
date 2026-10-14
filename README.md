# 🏭 SuiviPRO - Module Réglages & Organisation d'Atelier (Aluminium)

Système complet de configuration d'atelier, gestion des modèles de menuiseries, organisation des postes de travail multi-rôles, et **pointage biométrique Face ID par QR Code**.

Développé en **100% Python Pur** avec [NiceGUI](https://nicegui.io/) (FastAPI + Vue/Quasar sous le capot).

---

## 🚀 Fonctionnalités Clés

### 1. 🪟 Modèles de Menuiseries & Temps Cibles (Catalogue 32 Modèles)
- **32 modèles réels** issus du catalogue de production aluminium :
  - *Coulissants* : H31 (1 à 4 ouvrants, Galandage, Moustiquaire), H52 (2 et 3 rails).
  - *Ouvrants & Portes* : H40 (1 à 3 vantaux, oscillo-battant, porte va-et-vient, vasistas, accordéon), H68t (Rupture de pont thermique), Portes d'entrée.
  - *Fixes & Impostes* : Fixes intégrés, imposte haute, allège vitrée, précadres.
  - *Spéciaux* : Garde-corps Laila 1100 mm.
- **Ventilation du temps théorique par poste de travail** :
  - Calcul dynamique en minutes et pourcentages (Coupe/Débit, Grugage/Usinage, Assemblage, Vitrage, Contrôle/Emballage).
  - Possibilité d'**ajouter ou retirer librement des rôles** par modèle avec validation automatique de la somme à 100%.
  - Création de rôles personnalisés (palette de couleurs, icônes, poids par défaut).

### 2. 🏗️ Organisation d'Atelier & Tables Multi-Rôles
- Configuration modulaire des tables de travail (ajustable de 1 à 24 postes).
- **Support Multi-Rôles par table** : Une même table peut accueillir plusieurs étapes de fabrication (ex: Coupe + Grugage).
- **Assignation nominative des opérateurs** : Chaque rôle sur une table est directement attribué à un employé spécifique de l'équipe.

### 3. 👥 Employés d'Atelier & Système de Pointage en Temps Réel
- Registre complet des opérateurs (Nom, Matricule, Spécialité, Contact).
- Statut de présence en direct :
  - `🟢 Présent / Pointé` (avec heure exacte de pointage)
  - `🟠 En Pause`
  - `⚪ Non Pointé / Sorti`
- Badge biométrique Face ID (`📷 Face ID Actif` ou `⚠️ Sans Face ID`).
- Dialogue d'enrôlement facial avec prévisualisation.
- Journal d'historique en temps réel des derniers pointages.

### 4. 📱 Borne de Pointage Face ID & Accès Kiosk QR Code (`/pointage`)
- **Génération automatique de QR Code scannable** pour installer la borne sur smartphone ou tablette murale à l'entrée de l'atelier.
- **Caméra biométrique Face ID** avec mire ovale animée et balayage laser.
- Validation instantanée du pointage (Arrivée / Départ) avec notification visuelle et score de confiance biométrique.
- **Accès Administrateur sécurisé (PIN : 1234)** :
  - Permet d'enrôler et de **créer un nouvel employé sur place** depuis la tablette.
  - Capture photo instantanée de son Face ID pour qu'il puisse pointer dès la seconde suivante.

### 5. 🗄️ Base de Données (PostgreSQL / Supabase avec pgvector)
- Fichier de schéma SQL complet [`database_schema_supabase.sql`](database_schema_supabase.sql) conforme aux règles d'architecture et de performance Supabase :
  - Support des vecteurs biométriques via `pgvector` (`vector(128)`).
  - Tables : `employees`, `face_credentials`, `attendance_punches`, `workshop_tables`, `table_role_assignments`, `kiosk_settings`.
  - Triggers automatiques de synchronisation de présence.

---

## 🛠️ Installation & Démarrage

### Prérequis
- Python 3.10 ou supérieur

### 1. Installation des dépendances
```bash
pip install -r requirements.txt
```

### 2. Lancement de l'application
Sous Windows, double-cliquez sur `run.bat` ou lancez en ligne de commande :
```bash
python run.py
```

L'application s'ouvrira automatiquement dans votre navigateur par défaut sur :
- **Tableau de Bord & Réglages** : [http://localhost:8000](http://localhost:8000)
- **Borne Face ID Kiosk** : [http://localhost:8000/pointage](http://localhost:8000/pointage)

### 3. Exécution des tests unitaires
```bash
python test_settings.py
```

---

## 📁 Structure du Projet

```text
├── app.py                          # Application principale NiceGUI (UI Réglages & Kiosk Face ID)
├── settings_manager.py             # Moteur métier, calculs ratios, pointage, Face ID & persistance
├── settings.json                   # Base de données locale JSON (catalogue, rôles, employés, tables)
├── database_schema_supabase.sql    # Schéma de base de données PostgreSQL / Supabase avec pgvector
├── test_settings.py                # Suite de tests automatisés (Modèles, Rôles, Pointage, Face ID)
├── run.py                          # Lanceur autonome Python avec ouverture navigateur
├── run.bat                         # Raccourci Windows pour démarrage en 1 clic
├── requirements.txt                # Dépendances Python
└── README.md                       # Documentation du projet
```

---

## 🔒 Sécurité & Réglages Borne
- **Code PIN Administrateur de la Borne** : `1234` (modifiable dans les réglages).
