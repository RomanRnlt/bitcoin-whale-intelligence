#!/usr/bin/env python3
"""
Aktualisiert die Spark-Konfiguration im Experiment-Notebook für größere Datasets.
"""
import json
import sys
from pathlib import Path

def update_notebook():
    notebook_path = Path("notebooks/bitcoin_whale_explained_experiment.ipynb")

    if not notebook_path.exists():
        print(f"❌ Notebook nicht gefunden: {notebook_path}")
        return False

    # Notebook laden
    with open(notebook_path, 'r', encoding='utf-8') as f:
        notebook = json.load(f)

    # Suche die Zelle mit create_spark_session
    updated = False
    for cell in notebook['cells']:
        if cell['cell_type'] == 'code':
            source = ''.join(cell['source'])

            # Finde die Zelle mit der Spark-Konfiguration
            if 'spark.driver.maxResultSize' in source and '4g' in source:
                print("✅ Gefunden: Spark-Konfiguration")

                # Ersetze die Konfiguration
                old_config = '        .config("spark.driver.maxResultSize", "4g")'
                new_config = '''        .config("spark.driver.maxResultSize", "8g")  # Erhoeht fuer groessere Datasets
        # Off-Heap Memory fuer bessere Performance bei grossen Datasets (6GB+)
        .config("spark.memory.offHeap.enabled", "true")
        .config("spark.memory.offHeap.size", "6g")  # 6GB Off-Heap fuer Daten-Caching'''

                # Aktualisiere die Source-Zeilen
                new_source = []
                for line in cell['source']:
                    if 'spark.driver.maxResultSize", "4g"' in line:
                        # Ersetze die alte Zeile mit der neuen Konfiguration
                        new_source.append('        .config("spark.driver.maxResultSize", "8g")  # Erhoeht fuer groessere Datasets\n')
                        new_source.append('        # Off-Heap Memory fuer bessere Performance bei grossen Datasets (6GB+)\n')
                        new_source.append('        .config("spark.memory.offHeap.enabled", "true")\n')
                        new_source.append('        .config("spark.memory.offHeap.size", "6g")  # 6GB Off-Heap fuer Daten-Caching\n')
                    else:
                        new_source.append(line)

                cell['source'] = new_source
                updated = True
                print("✅ Spark-Konfiguration aktualisiert:")
                print("   - spark.driver.maxResultSize: 4g → 8g")
                print("   - spark.memory.offHeap.enabled: true")
                print("   - spark.memory.offHeap.size: 6g")
                break

    if not updated:
        print("⚠️  Keine Änderungen vorgenommen")
        return False

    # Backup erstellen
    backup_path = notebook_path.with_suffix('.ipynb.backup')
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(notebook, f, indent=1, ensure_ascii=False)
    print(f"💾 Backup erstellt: {backup_path}")

    # Notebook speichern
    with open(notebook_path, 'w', encoding='utf-8') as f:
        json.dump(notebook, f, indent=1, ensure_ascii=False)

    print(f"✅ Notebook aktualisiert: {notebook_path}")
    return True

if __name__ == "__main__":
    success = update_notebook()
    sys.exit(0 if success else 1)
