"""
Static translations for the Metadata Quality Dashboard.
Supported: DE (Default), FR, IT, EN.
"""

TRANSLATIONS = {
    "de": {
        "app_title": "BLW Metadaten-Qualitäts-Dashboard",
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
        
        # Inspector - General
        "inspector_select": "Datensatz auswählen",
        "inspector_raw": "Rohdaten anzeigen",
        "inspector_details": "Qualitätsdetails (FAIRC)",
        "inspector_no_data": "Keine Daten gefunden.",
        "inspector_improvement": "Verbesserungspotenzial",
        "inspector_id": "ID",
        "inspector_overall_score": "Gesamt-Score",

        # Inspector - Sections & Messages
        "sec_schema_violations": "Schema-Verstösse",
        "sec_link_health": "Link-Verfügbarkeit",
        
        "msg_valid_title": "Gültig",
        "msg_valid_body": "Schema-Validierung erfolgreich bestanden.",
        "msg_schema_violation": "Schema-Verstoss",
        
        "msg_no_dists": "Keine Distributionen für diesen Datensatz gefunden.",
        "msg_all_ok_title": "Alles in Ordnung",
        "msg_all_ok_body": "✅ Alle **{count}** Distributionen sind erreichbar.",
        "msg_broken_detected": "{count} Defekte Distribution(en) erkannt",
        "msg_view_healthy": "✅ {count} funktionierende Distributionen anzeigen",
        
        "lbl_access_url": "Zugriffs-URL",
        "lbl_download_url": "Download-URL",
        "lbl_unknown_fmt": "Unbekanntes Format",
        
        "msg_perfect_title": "Perfekter Score!",
        "msg_perfect_body": "Alle FAIRC-Kriterien erfüllt. 🏆",
        "msg_info_title": "Info",
        "msg_no_sug_body": "Keine spezifischen Vorschläge verfügbar.",
        
        # Charts / Severity
        "severity_high": "Hoch",
        "severity_med": "Mittel",
        "severity_low": "Tief",
        "chart_score_dist": "Verteilung der Qualitäts-Scores",
        "chart_top_errors": "Häufigste Validierungsfehler",

        # --- HELP PAGE CONTENT ---
        "help_overview": "Übersicht", 
        "help_goal": "Ziel",          
        "help_intro": "Das Dashboard unterscheidet zwei Arten von Qualitätsproblemen:",

        # NEW: Severity Help Section
        "help_sev_title": "🚦 Bedeutung der Schweregrade",
        "help_sev_desc": "Die Arbeitsliste kategorisiert Datensätze basierend auf ihrer Dringlichkeit:",
        "help_sev_high": "Ungültig (Schema-Verstösse vorhanden). Muss sofort korrigiert werden.",
        "help_sev_med": "Gültig, aber niedrige Qualität (Score < 200).",
        "help_sev_low": "Gute Qualität (Score ≥ 200). Kein dringender Handlungsbedarf.",
        
        # Violations Section
        "help_vio_title": "Schema-Verstösse (Pflicht)",
        "help_vio_desc": """
        Ein Verstoss bedeutet, dass der Datensatz technisch ungültig ist oder gegen BLW-Regeln verstösst.
        * **Auswirkung:** Datensätze mit Verstössen werden rot markiert.
        * **Beispiele:** Fehlende ID, ungültiges Datumsformat, fehlender Kontakt.
        """,
        "help_vio_goal": "🎯 0 Verstösse (Zwingend erforderlich).",

        # Score Section
        "help_score_title": "Qualitäts-Score (Verbesserung)",
        "help_score_desc": """
        **Dies ist ein Optimierungssystem basierend auf den FAIRC-Prinzipien** (Auffindbarkeit, Zugänglichkeit, Interoperabilität, Wiederverwendbarkeit, Kontextualität), das dem [opendata.swiss Dashboard Scoring](https://dashboard.opendata.swiss/de/) entspricht.
        Sobald das Schema validiert ist, können Sie Ihren Score verbessern, indem Sie die Daten nützlicher und zugänglicher machen.
        * Der maximale Score beträgt **405 Punkte**.
        * Die Tabelle unten zeigt genau, wofür Punkte vergeben werden.
        """,
        "help_score_goal": "🎯 Score maximieren (High Score).",

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
        
        "crit_access": "Access URL erreichbar (`dcat:accessURL`)",
        "crit_download": "Download URL vorhanden (`dcat:downloadURL`)",
        "crit_download_valid": "Download URL erreichbar",
        
        "crit_format": "Format angegeben (`dct:format`)",
        "crit_media": "Media Type angegeben (`dcat:mediaType`)",
        "crit_vocab": "Format/Media kontrolliert",
        "crit_openfmt": "Offenes Format",
        "crit_machine": "Maschinenlesbar",
        "crit_dcat": "DCAT-AP Konformität",
        
        "crit_license": "Lizenz vorhanden (`dct:license`)",
        "crit_lic_vocab": "Standard-Lizenz",
        "crit_access_res": "Zugangsbeschränkung (`dct:accessRights`)",
        "crit_access_vocab": "Standard-Zugangsbegriff",
        "crit_contact": "Kontaktangabe vollständig (`dcat:contactPoint`)",
        "crit_publisher": "Herausgeber angegeben (`dct:publisher`)",
        
        "crit_rights": "Nutzungsrechte definiert (`dct:rights`)",
        "crit_filesize": "Dateigrössen angegeben (`dcat:byteSize`)",
        "crit_issue": "Erstellungsdatum (`dct:issued`)",
        "crit_mod": "Änderungsdatum (`dct:modified`)",

        # Definitions/Links (Plain text only)
        "def_machine": "CSV, JSON, XML, RDF, XLSX (Keine PDF/Bilder)",
        "def_access": "Vokabular: PUBLIC, CONFIDENTIAL...",
        "def_license": "Z.B. cc-by, terms_open",
        "def_open": "Kein proprietäres Format (wie DOC, XLS)",
        "def_http": "URL gibt HTTP Status 200 zurück"
    },
    "fr": {
        "app_title": "OFAG Tableau de bord Qualité des Métadonnées",
        "tab_overview": "📈 Vue d'ensemble",
        "tab_inspector": "🔍 Inspecteur",
        "tab_help": "📚 Aide & Méthodologie",

        # Columns & Metrics
        "metric_total": "Jeux de données",
        "metric_score": "Ø Score de qualité",
        "metric_violations": "Violations de schéma",
        "col_severity": "Gravité",
        "col_title": "Titre",
        "col_score": "Score",
        "col_violations": "Violations",
        "col_id": "ID",
        
        # Inspector - General
        "inspector_select": "Sélectionner un jeu de données",
        "inspector_raw": "Afficher les données brutes",
        "inspector_details": "Détails de qualité (FAIRC)",
        "inspector_no_data": "Aucune donnée trouvée.",
        "inspector_improvement": "Opportunités d'amélioration",
        "inspector_id": "ID",
        "inspector_overall_score": "Score Global",

        # Inspector - Sections & Messages
        "sec_schema_violations": "Violations de Schéma",
        "sec_link_health": "Disponibilité des liens",
        
        "msg_valid_title": "Valide",
        "msg_valid_body": "Validation du schéma réussie.",
        "msg_schema_violation": "Violation de Schéma",
        
        "msg_no_dists": "Aucune distribution trouvée pour ce jeu de données.",
        "msg_all_ok_title": "Tout est opérationnel",
        "msg_all_ok_body": "✅ Les **{count}** distributions sont accessibles.",
        "msg_broken_detected": "{count} Distribution(s) défectueuse(s) détectée(s)",
        "msg_view_healthy": "✅ Voir {count} distributions saines",
        
        "lbl_access_url": "URL d'accès",
        "lbl_download_url": "URL de téléchargement",
        "lbl_unknown_fmt": "Format Inconnu",
        
        "msg_perfect_title": "Score Parfait !",
        "msg_perfect_body": "Tous les critères FAIRC sont remplis. 🏆",
        "msg_info_title": "Info",
        "msg_no_sug_body": "Aucune suggestion spécifique disponible.",
        
        # Charts / Severity
        "severity_high": "Élevée",
        "severity_med": "Moyenne",
        "severity_low": "Faible",
        "chart_score_dist": "Distribution des scores de qualité",
        "chart_top_errors": "Erreurs de validation fréquentes",

        # --- HELP PAGE CONTENT ---
        "help_overview": "Vue d'ensemble",
        "help_goal": "Objectif",          
        "help_intro": "Le tableau de bord distingue deux types de problèmes :",
        
        # NEW: Severity Help Section
        "help_sev_title": "🚦 Signification des niveaux de gravité",
        "help_sev_desc": "La liste de travail catégorise les jeux de données selon leur urgence :",
        "help_sev_high": "Invalide (Violations du schéma). À corriger immédiatement.",
        "help_sev_med": "Valide, mais qualité faible (Score < 200).",
        "help_sev_low": "Bonne qualité (Score ≥ 200). Pas d'action urgente requise.",

        # Violations Section
        "help_vio_title": "Violations du Schéma (Obligatoire)",
        "help_vio_desc": """
        Une violation signifie que le jeu de données est techniquement invalide.
        * **Impact:** Les jeux de données avec violations sont marqués en rouge.
        * **Exemples:** ID manquant, format de date invalide, contact manquant.
        """,
        "help_vio_goal": "🎯 0 Violations (Impératif).",

        "help_score_title": "Score de Qualité (Bonus)",
        "help_score_desc": """
        **C'est un système d'optimisation basé sur les principes FAIRC** (Trouvabilité, Accessibilité, Interopérabilité, Réutilisabilité, Contextualité), équivalent au [scoring du tableau de bord opendata.swiss](https://dashboard.opendata.swiss/fr/).
        Une fois le schéma validé, vous pouvez améliorer votre score en rendant les données plus utiles et accessibles.
        * Le score maximum est de **405 points**.
        * Le tableau ci-dessous montre exactement comment gagner des points.
        """,
        "help_score_goal": "🎯 Maximiser les points.",

        "help_calc_title": "🧮 Comment le score est-il calculé ?",
        "help_table_dim": "Dimension",
        "help_table_crit": "Critère",
        "help_table_pts": "Points",
        "help_table_info": "Info / Définition",
        
        "crit_keywords": "Mots-clés (`dcat:keyword`)",
        "crit_themes": "Catégories (`dcat:theme`)",
        "crit_geo": "Couverture géographique (`dct:spatial`)",
        "crit_time": "Couverture temporelle (`dct:temporal`)",
        
        "crit_access": "URL d'accès fonctionnelle (`dcat:accessURL`)",
        "crit_download": "URL de téléchargement fournie (`dcat:downloadURL`)",
        "crit_download_valid": "URL de téléchargement fonctionnelle",
        
        "crit_format": "Format déclaré (`dct:format`)",
        "crit_media": "Type de média déclaré (`dcat:mediaType`)",
        "crit_vocab": "Vocabulaire contrôlé",
        "crit_openfmt": "Format ouvert",
        "crit_machine": "Lisible par machine",
        "crit_dcat": "Conformité DCAT-AP",
        
        "crit_license": "Licence fournie (`dct:license`)",
        "crit_lic_vocab": "Licence standard",
        "crit_access_res": "Restriction d'accès (`dct:accessRights`)",
        "crit_access_vocab": "Terme d'accès standard",
        "crit_contact": "Contact complet (`dcat:contactPoint`)",
        "crit_publisher": "Éditeur déclaré (`dct:publisher`)",
        
        "crit_rights": "Droits d'utilisation définis (`dct:rights`)",
        "crit_filesize": "Taille de fichier déclarée (`dcat:byteSize`)",
        "crit_issue": "Date de création (`dct:issued`)",
        "crit_mod": "Date de modification (`dct:modified`)",

        "def_machine": "CSV, JSON, XML, RDF, XLSX (Pas de PDF/Images)",
        "def_access": "Vocabulaire: PUBLIC, CONFIDENTIAL...",
        "def_license": "Ex. cc-by, terms_open",
        "def_open": "Non-propriétaire (comme CSV, JSON)",
        "def_http": "L'URL renvoie un statut HTTP 200"
    },
    "it": {
        "app_title": "UFAG Dashboard Qualità Metadati",
        "tab_overview": "📈 Panoramica",
        "tab_inspector": "🔍 Ispettore",
        "tab_help": "📚 Aiuto & Metodologia",

        # Columns & Metrics
        "metric_total": "Dataset totali",
        "metric_score": "Ø Punteggio qualità",
        "metric_violations": "Violazioni dello schema",
        "col_severity": "Gravità",
        "col_title": "Titolo",
        "col_score": "Punteggio",
        "col_violations": "Violazioni",
        "col_id": "ID",
        
        # Inspector - General
        "inspector_select": "Seleziona dataset",
        "inspector_raw": "Mostra dati grezzi",
        "inspector_details": "Dettagli qualità (FAIRC)",
        "inspector_no_data": "Nessun dato trovato.",
        "inspector_improvement": "Opportunità di miglioramento",
        "inspector_id": "ID",
        "inspector_overall_score": "Punteggio Complessivo",

        # Inspector - Sections & Messages
        "sec_schema_violations": "Violazioni dello Schema",
        "sec_link_health": "Disponibilità dei link",
        
        "msg_valid_title": "Valido",
        "msg_valid_body": "Convalida dello schema superata con successo.",
        "msg_schema_violation": "Violazione dello Schema",
        
        "msg_no_dists": "Nessuna distribuzione trovata per questo dataset.",
        "msg_all_ok_title": "Tutto ok",
        "msg_all_ok_body": "✅ Tutte le **{count}** distribuzioni sono raggiungibili.",
        "msg_broken_detected": "{count} Distribuzione/i interrotta/e rilevata/e",
        "msg_view_healthy": "✅ Vedi {count} distribuzioni funzionanti",
        
        "lbl_access_url": "URL di accesso",
        "lbl_download_url": "URL di download",
        "lbl_unknown_fmt": "Formato Sconosciuto",
        
        "msg_perfect_title": "Punteggio Perfetto!",
        "msg_perfect_body": "Tutti i criteri FAIRC soddisfatti. 🏆",
        "msg_info_title": "Info",
        "msg_no_sug_body": "Nessun suggerimento specifico disponibile.",
        
        # Charts / Severity
        "severity_high": "Alta",
        "severity_med": "Media",
        "severity_low": "Bassa",
        "chart_score_dist": "Distribuzione dei punteggi",
        "chart_top_errors": "Errori di convalida frequenti",

        # --- HELP PAGE CONTENT ---
        "help_overview": "Panoramica",
        "help_goal": "Obiettivo",     
        "help_intro": "La dashboard distingue due tipi di problemi:",
        
        # NEW: Severity Help Section
        "help_sev_title": "🚦 Significato dei livelli di gravità",
        "help_sev_desc": "La lista di lavoro classifica i dataset in base alla loro urgenza:",
        "help_sev_high": "Non valido (Violazioni dello schema). Da correggere subito.",
        "help_sev_med": "Valido, ma bassa qualità (Punteggio < 200).",
        "help_sev_low": "Buona qualità (Punteggio ≥ 200). Nessuna azione urgente.",

        # Violations Section
        "help_vio_title": "Violazioni dello Schema (Obbligatorio)",
        "help_vio_desc": """
        Una violazione significa che il dataset non è tecnicamente valido.
        * **Impatto:** I dataset con violazioni sono segnati in rosso.
        * **Esempi:** ID mancante, formato data non valido, contatto mancante.
        """,
        "help_vio_goal": "🎯 0 Violations (Imperativo).",

        "help_score_title": "Punteggio di Qualità (Bonus)",
        "help_score_desc": """
        **Questo è un sistema di ottimizzazione basato sui principi FAIRC** (Reperibilità, Accessibilità, Interoperabilità, Riutilizzabilità, Contestualità), equivalente al [punteggio della dashboard di opendata.swiss](https://dashboard.opendata.swiss/it/).
        Una volta validato lo schema, è possibile migliorare il punteggio rendendo i dati più utili e accessibili.
        * Il punteggio massimo è **405 punti**.
        * La tabella sottostante mostra esattamente come guadagnare punti.
        """,
        "help_score_goal": "🎯 Massimizzare i punti.",

        "help_calc_title": "🧮 Come viene calcolato il punteggio?",
        "help_table_dim": "Dimensione",
        "help_table_crit": "Criterio",
        "help_table_pts": "Punti",
        "help_table_info": "Info / Definizione",
        
        "crit_keywords": "Parole chiave (`dcat:keyword`)",
        "crit_themes": "Categorie (`dcat:theme`)",
        "crit_geo": "Copertura geografica (`dct:spatial`)",
        "crit_time": "Copertura temporale (`dct:temporal`)",
        
        "crit_access": "URL di accesso funzionante (`dcat:accessURL`)",
        "crit_download": "URL di download fornito (`dcat:downloadURL`)",
        "crit_download_valid": "URL di download funzionante",
        
        "crit_format": "Formato dichiarato (`dct:format`)",
        "crit_media": "Tipo di supporto dichiarato (`dcat:mediaType`)",
        "crit_vocab": "Vocabolario controllato",
        "crit_openfmt": "Formato aperto",
        "crit_machine": "Leggibile da macchina",
        "crit_dcat": "Conformità DCAT-AP",
        
        "crit_license": "Licenza fornita (`dct:license`)",
        "crit_lic_vocab": "Licenza standard",
        "crit_access_res": "Restrizione di accesso (`dct:accessRights`)",
        "crit_access_vocab": "Termine di accesso standard",
        "crit_contact": "Contatto completo (`dcat:contactPoint`)",
        "crit_publisher": "Editore dichiarato (`dct:publisher`)",
        
        "crit_rights": "Diritti di utilizzo definiti (`dct:rights`)",
        "crit_filesize": "Dimensione file dichiarata (`dcat:byteSize`)",
        "crit_issue": "Data di creazione (`dct:issued`)",
        "crit_mod": "Data di modifica (`dct:modified`)",

        "def_machine": "CSV, JSON, XML, RDF, XLSX (No PDF/Immagini)",
        "def_access": "Vocabolario: PUBLIC, CONFIDENTIAL...",
        "def_license": "Es. cc-by, terms_open",
        "def_open": "Non proprietario (come CSV, JSON)",
        "def_http": "URL restituisce HTTP 200"
    },
    "en": {
        "app_title": "FOAG Metadata Quality Dashboard",
        "tab_overview": "📈 Overview",
        "tab_inspector": "🔍 Inspector",
        "tab_help": "📚 Help & Methodology",

        # Columns & Metrics
        "metric_total": "Total Datasets",
        "metric_score": "Avg Quality Score",
        "metric_violations": "Schema Violations",
        "col_severity": "Severity",
        "col_title": "Title",
        "col_score": "Score",
        "col_violations": "Violations",
        "col_id": "ID",
        
        # Inspector - General
        "inspector_select": "Select Dataset",
        "inspector_raw": "Show Raw Data",
        "inspector_details": "Quality Breakdown (FAIRC)",
        "inspector_no_data": "No data found.",
        "inspector_improvement": "Improvement Opportunities",
        "inspector_id": "ID",
        "inspector_overall_score": "Overall Score",

        # Inspector - Sections & Messages
        "sec_schema_violations": "Schema Violations",
        "sec_link_health": "Link Health (Accessibility)",
        
        "msg_valid_title": "Valid",
        "msg_valid_body": "Schema validation passed successfully.",
        "msg_schema_violation": "Schema Violation",
        
        "msg_no_dists": "No distributions found for this dataset.",
        "msg_all_ok_title": "All Systems Go",
        "msg_all_ok_body": "✅ All **{count}** distributions are reachable.",
        "msg_broken_detected": "{count} Broken Distribution(s) Detected",
        "msg_view_healthy": "✅ View {count} Healthy Distributions",
        
        "lbl_access_url": "Access URL",
        "lbl_download_url": "Download URL",
        "lbl_unknown_fmt": "Unknown Format",
        
        "msg_perfect_title": "Perfect Score!",
        "msg_perfect_body": "All FAIRC criteria met. 🏆",
        "msg_info_title": "Info",
        "msg_no_sug_body": "No specific suggestions available.",
        
        # Charts / Severity
        "severity_high": "High",
        "severity_med": "Medium",
        "severity_low": "Low",
        "chart_score_dist": "Quality Score Distribution",
        "chart_top_errors": "Top Validation Errors",

        # --- HELP PAGE CONTENT ---
        "help_overview": "Overview",
        "help_goal": "Goal",        
        "help_intro": "The dashboard distinguishes between two types of data issues:",
        
        # NEW: Severity Help Section
        "help_sev_title": "🚦 Severity Levels Explained",
        "help_sev_desc": "The worklist categorizes datasets based on urgency:",
        "help_sev_high": "Invalid (Schema violations present). Fix immediately.",
        "help_sev_med": "Valid, but low quality (Score < 200).",
        "help_sev_low": "Good quality (Score ≥ 200). No urgent action needed.",

        # Violations Section
        "help_vio_title": "Schema Violations (Mandatory)",
        "help_vio_desc": """
        A violation means the dataset is technically invalid or breaks FOAG rules.
        * **Impact:** Datasets with violations are flagged red.
        * **Examples:** Missing ID, invalid date format, missing contact email.
        """,
        "help_vio_goal": "🎯 0 Violations (Mandatory).",

        "help_score_title": "Quality Score (Optimization)",
        "help_score_desc": """
        **This is an optimization system based on the FAIRC principles** (Findability, Accessibility, Interoperability, Reusability, Contextuality), equivalent to the [opendata.swiss dashboard scoring](https://dashboard.opendata.swiss/en/).
        Once the schema is valid, you can improve your score by making the data more useful and accessible.
        * The maximum score is **405 points**.
        * The table below shows exactly how points are awarded.
        """,
        "help_score_goal": "🎯 Maximize points (High Score).",

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