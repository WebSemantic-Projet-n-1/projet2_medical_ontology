# domain.py — Documentation

## Rôle du fichier

`domain.py` contient la route liée aux **statistiques d'évolution
d'un domaine GO**. Il compare les deux versions et retourne
un résumé chiffré des changements pour l'ensemble du domaine.

---

## Endpoint

### `GET /api/domain/{domain_id}/stats`

Retourne les statistiques d'évolution pour un domaine GO entre
les versions 2025-10 et 2026-01.

**Exemple de requête :**
```
GET http://localhost:8000/api/domain/GO:0006281/stats
```

**Exemple de réponse :**
```json
{
  "domain_id": "GO:0006281",
  "total_old": 44,
  "total_new": 46,
  "new_terms": ["GO:0106044", "GO:0106045", "GO:0106046"],
  "new_terms_count": 3,
  "deprecated_terms": ["GO:0010776"],
  "deprecated_count": 1,
  "modified_terms": [],
  "modified_count": 0,
  "stable_terms": ["GO:0000710", "GO:0006281", "..."],
  "stable_count": 43
}
```

**Codes de retour :**
| Code | Signification |
|---|---|
| `200` | Statistiques calculées |
| `404` | Domaine introuvable dans le triplestore |

---

## Résultats obtenus (test du 15 mars 2026)

| Métrique | Valeur |
|---|---|
| Termes version 2025-10 | 44 |
| Termes version 2026-01 | 46 |
| Termes nouveaux | 3 (`GO:0106044`, `GO:0106045`, `GO:0106046`) |
| Termes disparus | 1 (`GO:0010776`) |
| Termes modifiés | 0 |
| Termes stables | 43 |

---

## Note sur les performances

Cet endpoint est le plus lent de l'API car il appelle `get_term_diff()`
pour chaque terme commun aux deux versions afin de détecter les modifications.
Pour 43 termes communs, cela représente 43 requêtes SPARQL supplémentaires.