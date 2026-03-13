# QR Code Generator

Application web de génération de QR codes personnalisés, construite avec **Streamlit** et **Python**.

🔗 **[Accéder à l'application](https://share.streamlit.io)**

---

## Fonctionnalités

- **Encodage** de n'importe quel texte ou URL
- **Logo personnalisé** au centre du QR code (PNG, JPG, WEBP)
- **6 formes de modules** : Carré, Rond/Dots, Carré espacé, Cercle, Barres verticales, Barres horizontales
- **Couleurs libres** : couleur des modules et couleur de fond
- **Coins arrondis** sur l'image finale
- **Export PNG haute résolution** (300 dpi)

---

## Aperçu

| Paramètres | Résultat |
|------------|----------|
| Forme, couleurs, logo configurables | QR code 600×600px exportable en 300 dpi |

---

## Installation locale

### Prérequis
- Python 3.10+

### Étapes

```bash
# Cloner le repo
git clone https://github.com/agbeya/QR-CODE-GENERATOR.git
cd QR-CODE-GENERATOR

# Créer un environnement virtuel
python -m venv .venv
source .venv/bin/activate  # macOS/Linux

# Installer les dépendances
pip install -r requirements.txt

# Lancer l'application
streamlit run app.py
```

L'app s'ouvre automatiquement sur [http://localhost:8501](http://localhost:8501).

---

## Dépendances

| Package | Rôle |
|---------|------|
| `streamlit` | Interface web |
| `qrcode[pil]` | Génération du QR code |
| `Pillow` | Traitement d'image |

---

## Déploiement

L'application est déployée sur **Streamlit Community Cloud**.  
Tout push sur la branche `main` déclenche un redéploiement automatique.

---

## Structure du projet

```
.
├── app.py            # Application principale
├── requirements.txt  # Dépendances Python
└── README.md
```

---

© 2026 By DataSoft Solution
