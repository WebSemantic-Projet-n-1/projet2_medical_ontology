# sparql_client.py — Documentation

## Rôle du fichier

`sparql_client.py` est la **couche d'accès aux données** du projet.
Il fait le lien entre le triplestore Fuseki et l'API REST.
Concrètement, chaque fois que l'API reçoit une requête HTTP,
elle appelle une méthode de `SparqlClient` qui interroge Fuseki en SPARQL
et retourne les données en Python pur (dicts/listes).

---

## Méthodes disponibles

### `query(sparql_str)` — méthode de base
Exécute n'importe quelle requête SPARQL SELECT et retourne
une liste de dicts Python.

```python
client = SparqlClient()
rows = client.query("SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 5")
```

---

### `get_term_info(go_id)` — endpoint `/api/term/{go_id}`
Retourne les métadonnées d'un terme GO dans ses **deux versions**.

```python
info = client.get_term_info("GO:0006281")
# {
#   "old": { "label": "DNA repair", "definition": "...", "isDeprecated": false, ... },
#   "new": { "label": "DNA repair", "definition": "...", "isDeprecated": false, ... }
# }
```

---

### `get_term_diff(go_id)` — endpoint `/api/term/{go_id}/diff`
Compare les deux versions d'un terme et retourne les différences.
Le champ `status` peut valoir : `stable`, `modified`, `deprecated`, `new`.

```python
diff = client.get_term_diff("GO:0006281")
# {
#   "go_id": "GO:0006281",
#   "status": "stable",
#   "changes": []
# }
```

---

### `get_domain_stats(domain_id)` — endpoint `/api/domain/{domain_id}/stats`
Statistiques d'évolution pour tout le domaine DNA repair.

```python
stats = client.get_domain_stats("GO:0006281")
# {
#   "total_old": 44,
#   "total_new": 46,
#   "new_terms": ["GO:0106044", "GO:0106045", "GO:0106046"],
#   "deprecated_terms": ["GO:0010776"],
#   "modified_count": 0,
#   "stable_count": 43
# }
```

---

### `search(q)` — endpoint `/api/search?q={query}`
Recherche par label ou définition (insensible à la casse).
Retourne la version la plus récente de chaque terme trouvé.

```python
results = client.search("repair")
# [
#   { "termID": "GO:0000012", "label": "single strand break repair", ... },
#   { "termID": "GO:0006281", "label": "DNA repair", ... },
#   ...
# ]
```

---

## Résultats obtenus (test du 15 mars 2026)

```
=== get_term_info(GO:0006281) ===
→ Terme trouvé dans les deux versions, label "DNA repair", non déprécié

=== get_term_diff(GO:0006281) ===
→ status: stable — aucun changement sur la racine du domaine

=== get_domain_stats(GO:0006281) ===
→ 44 termes (2025-10)  vs  46 termes (2026-01)
→ 3 nouveaux  : GO:0106044, GO:0106045, GO:0106046
→ 1 disparu   : GO:0010776
→ 0 modifié
→ 43 stables

=== search('repair') ===
→ 43 termes retournés
```

---

## Configuration

Le endpoint SPARQL est lu depuis le fichier `.env` :

```env
SPARQL_ENDPOINT=http://localhost:3030/ds/sparql
```

Si la variable n'est pas définie, la valeur par défaut est utilisée :
`http://localhost:3030/ds/sparql`