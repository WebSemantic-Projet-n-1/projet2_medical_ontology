# search.py — Documentation

## Rôle du fichier

`search.py` contient la route de **recherche de termes GO** par mot-clé.
La recherche s'effectue sur les labels et les définitions des termes,
et retourne la version la plus récente (2026-01) de chaque résultat.

---

## Endpoint

### `GET /api/search?q={query}`

Recherche des termes GO par label ou définition (insensible à la casse).

**Exemple de requête :**
```
GET http://localhost:8000/api/search?q=repair
GET http://localhost:8000/api/search?q=nucleotide
GET http://localhost:8000/api/search?q=mismatch
```

**Exemple de réponse :**
```json
{
  "query": "repair",
  "count": 43,
  "results": [
    {
      "termID": "GO:0000012",
      "label": "single strand break repair",
      "definition": "...",
      "version": "http://example.org/go/version/2026-01"
    },
    {
      "termID": "GO:0006281",
      "label": "DNA repair",
      "definition": "The process of restoring DNA after damage...",
      "version": "http://example.org/go/version/2026-01"
    }
  ]
}
```

**Codes de retour :**
| Code | Signification |
|---|---|
| `200` | Recherche effectuée (peut retourner 0 résultats) |
| `400` | Paramètre `q` vide ou manquant |

---

## Paramètre `q`

| Contrainte | Valeur |
|---|---|
| Minimum | 2 caractères |
| Casse | Insensible |
| Champs recherchés | Label et définition |

---

## Déduplication

Si un terme existe dans les deux versions (2025-10 et 2026-01),
seule la version **2026-01** est retournée dans les résultats.
Cela évite les doublons et garantit que l'utilisateur voit
toujours les informations les plus récentes.