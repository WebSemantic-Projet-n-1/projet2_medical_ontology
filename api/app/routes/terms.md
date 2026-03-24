# terms.py — Documentation

## Rôle du fichier

`terms.py` contient les routes liées aux **termes GO individuels**.
Il reçoit les requêtes HTTP, appelle `SparqlClient`, et retourne
les données en JSON via des modèles Pydantic.

---

## Endpoints

### `GET /api/term/{go_id}`

Retourne les métadonnées d'un terme GO dans ses **deux versions**.

**Exemple de requête :**
```
GET http://localhost:8000/api/term/GO:0006281
```

**Exemple de réponse :**
```json
{
  "go_id": "GO:0006281",
  "old": {
    "termURI": "http://example.org/evolution/term/GO_0006281/2025-10",
    "label": "DNA repair",
    "definition": "The process of restoring DNA after damage...",
    "isDeprecated": false,
    "version": "http://example.org/go/version/2025-10"
  },
  "new": {
    "termURI": "http://example.org/evolution/term/GO_0006281/2026-01",
    "label": "DNA repair",
    "definition": "The process of restoring DNA after damage...",
    "isDeprecated": false,
    "version": "http://example.org/go/version/2026-01"
  }
}
```

**Codes de retour :**
| Code | Signification |
|---|---|
| `200` | Terme trouvé |
| `404` | Terme introuvable dans les deux versions |

---

### `GET /api/term/{go_id}/diff`

Compare les deux versions d'un terme et retourne les différences.

**Exemple de requête :**
```
GET http://localhost:8000/api/term/GO:0006281/diff
```

**Exemple de réponse (terme stable) :**
```json
{
  "go_id": "GO:0006281",
  "status": "stable",
  "old": { ... },
  "new": { ... },
  "changes": []
}
```

**Exemple de réponse (terme modifié) :**
```json
{
  "go_id": "GO:0006302",
  "status": "modified",
  "old": { ... },
  "new": { ... },
  "changes": [
    {
      "field": "definition",
      "old": "Ancienne définition...",
      "new": "Nouvelle définition..."
    }
  ]
}
```

**Valeurs possibles de `status` :**
| Valeur | Signification |
|---|---|
| `stable` | Aucun changement entre les deux versions |
| `modified` | Au moins un champ a changé |
| `deprecated` | Terme marqué obsolète dans la nouvelle version |
| `new` | Terme absent de l'ancienne version |
| `not_found` | Terme absent des deux versions |

**Codes de retour :**
| Code | Signification |
|---|---|
| `200` | Comparaison effectuée |
| `404` | Terme introuvable dans les deux versions |

---

## Formats acceptés pour `go_id`

Le paramètre `go_id` est normalisé automatiquement :

| Format fourni | Format normalisé |
|---|---|
| `GO:0006281` | `GO:0006281` |
| `GO0006281` | `GO:0006281` |
| `go:0006281` | `GO:0006281` |
| `0006281` | `GO:0006281` |