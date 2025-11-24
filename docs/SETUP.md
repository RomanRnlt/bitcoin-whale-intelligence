# Setup Guide

Vollständige Setup-Anleitung für das Bitcoin Whale Intelligence Projekt.

## Inhaltsverzeichnis

- [Quick Start](#quick-start)
- [Basis Setup](#basis-setup)
  - [1. Repo klonen](#1-repo-klonen)
  - [2. Virtual Environment](#2-virtual-environment)
  - [3. Dependencies installieren](#3-dependencies-installieren)
  - [4. Projekt starten](#4-projekt-starten)
- [BigQuery Setup (Optional)](#bigquery-setup-optional)
  - [Service Account erstellen](#service-account-erstellen)
  - [Credentials speichern](#credentials-speichern)
  - [Testen](#testen)

---

## Quick Start

```bash
git clone https://github.com/RomanRnlt/bitcoin-whale-intelligence.git
cd bitcoin-whale-intelligence
source venv/bin/activate  # oder venv\Scripts\activate auf Windows
pip install -r requirements.txt
jupyter notebook
```

Dann im Browser: `notebooks/01_data_exploration.ipynb` öffnen.

Das Notebook läuft im Demo-Mode ohne BigQuery-Anbindung.

---

## Basis Setup

### 1. Repo klonen

```bash
git clone https://github.com/RomanRnlt/bitcoin-whale-intelligence.git
cd bitcoin-whale-intelligence
```

### 2. Virtual Environment

```bash
source venv/bin/activate  # macOS / Linux
# oder
venv\Scripts\activate     # Windows
```

### 3. Dependencies installieren

```bash
pip install -r requirements.txt
```

Installiert alle benötigten Packages (PySpark, GraphFrames, Pandas, etc.).

### 4. Projekt starten

**macOS / Linux:**

Mit Script:
```bash
./start_project.sh
```

Oder manuell:
```bash
source venv/bin/activate
export JAVA_HOME=$(/usr/libexec/java_home -v 11)  # macOS
jupyter notebook
```

**Windows:**

```cmd
venv\Scripts\activate
set JAVA_HOME=C:\Program Files\Java\jdk-11
jupyter notebook
```

Im Browser: `notebooks/01_data_exploration.ipynb` öffnen.

**Test:**
1. Alle Zellen ausführen (Shift+Enter oder "Run All")
2. Läuft im Demo-Mode ohne BigQuery
3. Alle Visualisierungen sollten angezeigt werden

---

## BigQuery Setup (Optional)

Das erste Notebook nutzt Demo-Daten. Für spätere Notebooks (ab Notebook 2) wird BigQuery benötigt.

### Service Account erstellen

**Schritt 1: Google Cloud Project erstellen**

https://console.cloud.google.com/projectcreate

- Project Name: `bitcoin-whale-intelligence` (oder eigener Name)
- Organization: Kann leer bleiben
- Click: "Create"

**Schritt 2: BigQuery API aktivieren**

https://console.cloud.google.com/apis/library/bigquery.googleapis.com

- Wähle dein Projekt oben aus
- Click: "Enable"

**Schritt 3: Service Account erstellen**

https://console.cloud.google.com/iam-admin/serviceaccounts/create

- Service account name: `bitcoin-whale-dev`
- Service account ID: (wird automatisch generiert)
- Click: "Create and Continue"
- Role: Wähle "BigQuery User"
- Click: "Continue" → "Done"

**Schritt 4: JSON Key erstellen**

https://console.cloud.google.com/iam-admin/serviceaccounts

- Click auf deinen Service Account
- Tab: "Keys"
- Click: "Add Key" → "Create new key"
- Key type: JSON
- Click: "Create" → Datei wird heruntergeladen

### Credentials speichern

1. Erstelle einen Ordner `.credentials` im Projekt-Root
2. Kopiere die heruntergeladene JSON-Datei aus dem Downloads-Ordner
3. Füge sie in `.credentials` ein
4. Benenne sie um zu: `bigquery-credentials.json`

### .env Datei erstellen

1. Kopiere die Datei `.env.example` im Projekt-Root
2. Benenne die Kopie um zu: `.env`
3. Öffne `.env` mit einem Texteditor
4. Stelle sicher, dass folgende Zeile vorhanden ist:
   ```
   GOOGLE_APPLICATION_CREDENTIALS=.credentials/bigquery-credentials.json
   ```

### Testen

```bash
./start_project.sh
```

Sollte anzeigen: "BigQuery credentials found"

---

## Weitere Dokumentation

- [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) - Projekt-Kontext
- [NOTEBOOK_WORKFLOW.md](NOTEBOOK_WORKFLOW.md) - Plan für alle Notebooks
