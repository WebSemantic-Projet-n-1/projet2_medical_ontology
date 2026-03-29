# SPARQL UPDATE — Matérialisation de l'inférence evo:previousVersion
#
# Ce script utilise les capacités d'inférence du triplestore Fuseki/Jena :
# à partir des données factuelles déjà chargées (evo:termID, evo:belongsToVersion,
# evo:versionDate), il génère automatiquement les triplets evo:previousVersion
# en comparant les identifiants GO entre les deux graphes nommés.
#
# Les triplets inférés sont stockés dans un graphe nommé dédié :
#   <http://example.org/go/inferred>
#
# TODO Add this step to run.py
#
# Exécution via l'endpoint SPARQL Update de Fuseki :
#   POST http://localhost:3030/ds/update
#
# Ou via curl :
#   curl -X POST "http://localhost:3030/ds/update" \
#        --user admin:${ADMIN_PASSWORD}            \
#        --header "Content-Type: application/sparql-update" \
#        --data-binary @materialize_previous_version.ru

PREFIX evo: <http://example.org/evolution/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

INSERT {
    # Graphe nommé dédié aux triplets inférés — séparé des données sources
    GRAPH <http://example.org/go/inferred> {
        ?termNouveau evo:previousVersion ?termAncien .
    }
}
WHERE {
    # Terme dans la version récente
    GRAPH ?gNouveau {
        ?termNouveau a evo:TermVersion ;
                     evo:termID ?id ;
                     evo:belongsToVersion ?vNouveau .
    }

    # Terme dans l'ancienne version avec le même identifiant GO
    GRAPH ?gAncien {
        ?termAncien a evo:TermVersion ;
                    evo:termID ?id ;
                    evo:belongsToVersion ?vAncien .
    }

    # Dates de version (dans leurs graphes respectifs)
    ?vNouveau evo:versionDate ?dateNouveau .
    ?vAncien  evo:versionDate ?dateAncien  .

    # Contraintes : graphes distincts, direction récent → ancien
    FILTER ( ?gNouveau != ?gAncien )
    FILTER ( ?dateNouveau > ?dateAncien )
}
