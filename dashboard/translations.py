"""
Static translations for the Metadata Quality Dashboard.
Supported: DE (Default), FR, IT, EN.
"""

TRANSLATIONS = {
    "de": {
        "app_title": "BLW Metadaten-Qualitäts-Dashboard 🏆",
        "tab_worklist": "🔨 Arbeitsliste",
        "tab_overview": "📈 Übersicht",
        "tab_inspector": "🔍 Inspektor",
        "tab_help": "📚 Hilfe & Methodik",
        
        # Columns & Metrics
        "metric_total": "Anzahl Datensätze",
        "metric_score": "Ø Qualitäts-Score",
        "metric_violations": "Schema-Verstösse",
        "col_severity": "Schweregrad",
        "col_title": "Titel",
        "col_score": "Score",
        "col_violations": "Verstösse",
        "col_id": "ID",
        
        # Inspector
        "inspector_select": "Datensatz auswählen",
        "inspector_raw": "Rohdaten anzeigen",
        "inspector_details": "Qualitätsdetails",
        "inspector_no_data": "Keine Daten gefunden.",
        "inspector_improvement": "Verbesserungspotenzial",
        
        # Charts / Severity
        "severity_high": "Hoch",
        "severity_med": "Mittel",
        "severity_low": "Tief",
        "chart_score_dist": "Verteilung der Qualitäts-Scores",
        "chart_top_errors": "Häufigste Validierungsfehler",

        # --- HELP PAGE CONTENT ---
        "help_intro": "Das Dashboard unterscheidet zwei Arten von Qualitätsproblemen:",
        
        # Violations Section
        "help_vio_title": "1. Schema-Verstösse (Pflicht)",
        "help_vio_desc": """
        **Dies ist die Basis-Hygiene.** Ein Verstoss bedeutet, dass der Datensatz technisch ungültig ist oder gegen BLW-Regeln verstösst.
        * **Auswirkung:** Datensätze mit Verstössen werden rot markiert.
        * **Beispiele:** Fehlende ID, ungültiges Datumsformat, fehlender Kontakt.
        """,
        "help_vio_goal": "🎯 **Ziel:** 0 Verstösse (Zwingend erforderlich).",

        # Score Section
        "help_score_title": "2. Qualitäts-Score (Kür)",
        "help_score_desc": """
        **Dies ist ein Optimierungs-System (FAIRC).** Sobald das Schema validiert ist, können Sie Ihren Score verbessern, indem Sie die Daten nützlicher machen.
        
        * Der maximale Score beträgt **405 Punkte**.
        * Die Tabelle unten zeigt genau, wofür Punkte vergeben werden.
        """,
        "help_score_goal": "🎯 **Ziel:** Score maximieren (High Score).",

        # Calculator Table Headers
        "help_calc_title": "🧮 Wie wird der Score berechnet?",
        "help_table_dim": "Dimension",
        "help_table_crit": "Kriterium",
        "help_table_pts": "Punkte",
        "help_table_info": "Info / Definition",
        
        # Detailed Scoring Criteria
        "crit_keywords": "Stichworte (`dcat:keyword`)",
        "crit_themes": "Kategorien (`dcat:theme`)",
        "crit_geo": "Geografische Abdeckung (`dct:spatial`)",
        "crit_time": "Zeitliche Abdeckung (`dct:temporal`)",
        
        "crit_access": "Access URL erreichbar",
        "crit_download": "Download URL vorhanden",
        "crit_download_valid": "Download URL erreichbar",
        
        "crit_format": "Format angegeben",
        "crit_media": "Media Type angegeben",
        "crit_vocab": "Format/Media kontrolliert",
        "crit_openfmt": "Offenes Format",
        "crit_machine": "Maschinenlesbar",
        "crit_dcat": "DCAT-AP Konformität",
        
        "crit_license": "Lizenz vorhanden",
        "crit_lic_vocab": "Standard-Lizenz",
        "crit_access_res": "Zugangsbeschränkung",
        "crit_access_vocab": "Standard-Zugangsbegriff",
        "crit_contact": "Kontaktangabe vollständig",
        "crit_publisher": "Herausgeber angegeben",
        
        "crit_rights": "Nutzungsrechte definiert",
        "crit_filesize": "Dateigrössen angegeben",
        "crit_issue": "Erstellungsdatum",
        "crit_mod": "Änderungsdatum",

        # Definitions/Links (Plain text only)
        "def_machine": "CSV, JSON, XML, RDF, XLSX (Keine PDF/Bilder)",
        "def_access": "Vokabular: PUBLIC, CONFIDENTIAL...",
        "def_license": "Z.B. cc-by, terms_open",
        "def_open": "Kein proprietäres Format (wie DOC, XLS)",
        "def_http": "URL gibt HTTP Status 200 zurück"
    },
    "fr": {
        "app_title": "OFAG Tableau de bord Qualité des Métadonnées 🏆",
        "tab_worklist": "🔨 Liste de travail",
        "tab_overview": "📈 Vue d'ensemble",
        "tab_inspector": "🔍 Inspecteur",
        "tab_help": "📚 Aide & Méthodologie",

        "metric_total": "Jeux de données",
        "metric_score": "Ø Score de qualité",
        "metric_violations": "Violations de schéma",
        "col_severity": "Gravité",
        "col_title": "Titre",
        "col_score": "Score",
        "col_violations": "Violations",
        "col_id": "ID",
        
        "inspector_select": "Sélectionner un jeu de données",
        "inspector_raw": "Afficher les données brutes",
        "inspector_details": "Détails de qualité",
        "inspector_no_data": "Aucune donnée trouvée.",
        "inspector_improvement": "Opportunités d'amélioration",
        
        "severity_high": "Élevée",
        "severity_med": "Moyenne",
        "severity_low": "Faible",
        "chart_score_dist": "Distribution des scores de qualité",
        "chart_top_errors": "Erreurs de validation fréquentes",

        # --- HELP PAGE CONTENT ---
        "help_intro": "Le tableau de bord distingue deux types de problèmes :",
        
        "help_vio_title": "1. Violations du Schéma (Obligatoire)",
        "help_vio_desc": """
        **C'est l'hygiène de base.** Une violation signifie que le jeu de données est techniquement invalide.
        * **Impact:** Les jeux de données avec violations sont marqués en rouge.
        * **Exemples:** ID manquant, format de date invalide, contact manquant.
        """,
        "help_vio_goal": "🎯 **Objectif:** 0 Violations (Impératif).",

        "help_score_title": "2. Score de Qualité (Bonus)",
        "help_score_desc": """
        **C'est un système d'optimisation (FAIRC).**
        Une fois le schéma validé, vous pouvez améliorer votre score en rendant les données plus utiles.
        
        * Le score maximum est de **405 points**.
        * Le tableau ci-dessous montre exactement comment gagner des points.
        """,
        "help_score_goal": "🎯 **Objectif:** Maximiser les points.",

        "help_calc_title": "🧮 Comment le score est-il calculé ?",
        "help_table_dim": "Dimension",
        "help_table_crit": "Critère",
        "help_table_pts": "Points",
        "help_table_info": "Info / Définition",
        
        "crit_keywords": "Mots-clés (`dcat:keyword`)",
        "crit_themes": "Catégories (`dcat:theme`)",
        "crit_geo": "Couverture géographique (`dct:spatial`)",
        "crit_time": "Couverture temporelle (`dct:temporal`)",
        
        "crit_access": "URL d'accès fonctionnelle",
        "crit_download": "URL de téléchargement fournie",
        "crit_download_valid": "URL de téléchargement fonctionnelle",
        
        "crit_format": "Format déclaré",
        "crit_media": "Type de média déclaré",
        "crit_vocab": "Vocabulaire contrôlé",
        "crit_openfmt": "Format ouvert",
        "crit_machine": "Lisible par machine",
        "crit_dcat": "Conformité DCAT-AP",
        
        "crit_license": "Licence fournie",
        "crit_lic_vocab": "Licence standard",
        "crit_access_res": "Restriction d'accès",
        "crit_access_vocab": "Terme d'accès standard",
        "crit_contact": "Contact complet",
        "crit_publisher": "Éditeur déclaré",
        
        "crit_rights": "Droits d'utilisation définis",
        "crit_filesize": "Taille de fichier déclarée",
        "crit_issue": "Date de création",
        "crit_mod": "Date de modification",

        "def_machine": "CSV, JSON, XML, RDF, XLSX (Pas de PDF/Images)",
        "def_access": "Vocabulaire: PUBLIC, CONFIDENTIAL...",
        "def_license": "Ex. cc-by, terms_open",
        "def_open": "Non-propriétaire (comme CSV, JSON)",
        "def_http": "L'URL renvoie un statut HTTP 200"
    },
    "it": {
        "app_title": "UFAG Dashboard Qualità Metadati 🏆",
        "tab_worklist": "🔨 Lista di lavoro",
        "tab_overview": "📈 Panoramica",
        "tab_inspector": "🔍 Ispettore",
        "tab_help": "📚 Aiuto & Metodologia",

        "metric_total": "Dataset totali",
        "metric_score": "Ø Punteggio qualità",
        "metric_violations": "Violazioni dello schema",
        "col_severity": "Gravità",
        "col_title": "Titolo",
        "col_score": "Punteggio",
        "col_violations": "Violazioni",
        "col_id": "ID",
        
        "inspector_select": "Seleziona dataset",
        "inspector_raw": "Mostra dati grezzi",
        "inspector_details": "Dettagli qualità",
        "inspector_no_data": "Nessun dato trovato.",
        "inspector_improvement": "Opportunità di miglioramento",
        
        "severity_high": "Alta",
        "severity_med": "Media",
        "severity_low": "Bassa",
        "chart_score_dist": "Distribuzione dei punteggi",
        "chart_top_errors": "Errori di convalida frequenti",

        # --- HELP PAGE CONTENT ---
        "help_intro": "La dashboard distingue due tipi di problemi:",
        
        "help_vio_title": "1. Violazioni dello Schema (Obbligatorio)",
        "help_vio_desc": """
        **Questa è l'igiene di base.** Una violazione significa che il dataset non è tecnicamente valido.
        * **Impatto:** I dataset con violazioni sono segnati in rosso.
        * **Esempi:** ID mancante, formato data non valido, contatto mancante.
        """,
        "help_vio_goal": "🎯 **Obiettivo:** 0 Violazioni (Imperativo).",

        "help_score_title": "2. Punteggio di Qualità (Bonus)",
        "help_score_desc": """
        **Questo è un sistema di ottimizzazione (FAIRC).**
        Una volta validato lo schema, puoi migliorare il punteggio rendendo i dati più utili.
        
        * Il punteggio massimo è **405 punti**.
        * La tabella sottostante mostra esattamente come guadagnare punti.
        """,
        "help_score_goal": "🎯 **Obiettivo:** Massimizzare i punti.",

        "help_calc_title": "🧮 Come viene calcolato il punteggio?",
        "help_table_dim": "Dimensione",
        "help_table_crit": "Criterio",
        "help_table_pts": "Punti",
        "help_table_info": "Info / Definizione",
        
        "crit_keywords": "Parole chiave (`dcat:keyword`)",
        "crit_themes": "Categorie (`dcat:theme`)",
        "crit_geo": "Copertura geografica (`dct:spatial`)",
        "crit_time": "Copertura temporale (`dct:temporal`)",
        
        "crit_access": "URL di accesso funzionante",
        "crit_download": "URL di download fornito",
        "crit_download_valid": "URL di download funzionante",
        
        "crit_format": "Formato dichiarato",
        "crit_media": "Tipo di supporto dichiarato",
        "crit_vocab": "Vocabolario controllato",
        "crit_openfmt": "Formato aperto",
        "crit_machine": "Leggibile da macchina",
        "crit_dcat": "Conformità DCAT-AP",
        
        "crit_license": "Licenza fornita",
        "crit_lic_vocab": "Licenza standard",
        "crit_access_res": "Restrizione di accesso",
        "crit_access_vocab": "Termine di accesso standard",
        "crit_contact": "Contatto completo",
        "crit_publisher": "Editore dichiarato",
        
        "crit_rights": "Diritti di utilizzo definiti",
        "crit_filesize": "Dimensione file dichiarata",
        "crit_issue": "Data di creazione",
        "crit_mod": "Data di modifica",

        "def_machine": "CSV, JSON, XML, RDF, XLSX (No PDF/Immagini)",
        "def_access": "Vocabolario: PUBLIC, CONFIDENTIAL...",
        "def_license": "Es. cc-by, terms_open",
        "def_open": "Non proprietario (come CSV, JSON)",
        "def_http": "URL restituisce HTTP 200"
    },
    "en": {
        "app_title": "FOAG Metadata Quality Dashboard 🏆",
        "tab_worklist": "🔨 Worklist",
        "tab_overview": "📈 Overview",
        "tab_inspector": "🔍 Inspector",
        "tab_help": "📚 Help & Methodology",

        "metric_total": "Total Datasets",
        "metric_score": "Avg Quality Score",
        "metric_violations": "Schema Violations",
        "col_severity": "Severity",
        "col_title": "Title",
        "col_score": "Score",
        "col_violations": "Violations",
        "col_id": "ID",
        
        "inspector_select": "Select Dataset",
        "inspector_raw": "Show Raw Data",
        "inspector_details": "Quality Breakdown",
        "inspector_no_data": "No data found.",
        "inspector_improvement": "Improvement Opportunities",
        
        "severity_high": "High",
        "severity_med": "Medium",
        "severity_low": "Low",
        "chart_score_dist": "Quality Score Distribution",
        "chart_top_errors": "Top Validation Errors",

        # --- HELP PAGE CONTENT ---
        "help_intro": "The dashboard distinguishes between two types of data issues:",
        
        "help_vio_title": "1. Schema Violations (Mandatory)",
        "help_vio_desc": """
        **This is basic hygiene.** A violation means the dataset is technically invalid or breaks BLW rules.
        * **Impact:** Datasets with violations are flagged red.
        * **Examples:** Missing ID, invalid date format, missing contact email.
        """,
        "help_vio_goal": "🎯 **Goal:** 0 Violations (Mandatory).",

        "help_score_title": "2. Quality Score (Optimization)",
        "help_score_desc": """
        **This is an optimization system (FAIRC).**
        Once the schema is valid, you can improve your score by making the data more useful and accessible.
        
        * The maximum score is **405 points**.
        * The table below shows exactly how points are awarded.
        """,
        "help_score_goal": "🎯 **Goal:** Maximize points (High Score).",

        "help_calc_title": "🧮 Scoring Calculator",
        "help_table_dim": "Dimension",
        "help_table_crit": "Criteria",
        "help_table_pts": "Points",
        "help_table_info": "Info / Definition",
        
        # Detailed Scoring Criteria (Updated with Field Names)
        "crit_keywords": "Keywords provided (`dcat:keyword`)",
        "crit_themes": "Categories provided (`dcat:theme`)",
        "crit_geo": "Geographical Coverage (`dct:spatial`)",
        "crit_time": "Temporal Coverage (`dct:temporal`)",
        
        "crit_access": "Access URL works (`dcat:accessURL`)",
        "crit_download": "Download URL provided (`dcat:downloadURL`)",
        "crit_download_valid": "Download URL works",
        
        "crit_format": "Format declared (`dct:format`)",
        "crit_media": "Media Type declared (`dcat:mediaType`)",
        "crit_vocab": "Controlled Vocabulary (Format)",
        "crit_openfmt": "Open Format",
        "crit_machine": "Machine Readable",
        "crit_dcat": "DCAT-AP Compliance",
        
        "crit_license": "License provided (`dct:license`)",
        "crit_lic_vocab": "Standard License (Vocabulary)",
        "crit_access_res": "Access Restriction (`dct:accessRights`)",
        "crit_access_vocab": "Standard Access Term",
        "crit_contact": "Contact Point provided (`dcat:contactPoint`)",
        "crit_publisher": "Publisher declared (`dct:publisher`)",
        
        "crit_rights": "Rights defined (`dct:rights`)",
        "crit_filesize": "File size declared (`dcat:byteSize`)",
        "crit_issue": "Issue Date (`dct:issued`)",
        "crit_mod": "Modification Date (`dct:modified`)",

        # Definitions (Plain text only)
        "def_machine": "CSV, JSON, XML, RDF, XLSX (No PDF/Images)",
        "def_access": "Vocabulary: PUBLIC, CONFIDENTIAL...",
        "def_license": "E.g. cc-by, terms_open",
        "def_open": "Non-proprietary (like CSV, JSON)",
        "def_http": "URL returns HTTP Status 200"
    }
}