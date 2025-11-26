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
        
        # Charts / Severity
        "severity_high": "Hoch",
        "severity_med": "Mittel",
        "severity_low": "Tief",
        "chart_score_dist": "Verteilung der Qualitäts-Scores",
        "chart_top_errors": "Häufigste Validierungsfehler",

        # --- HELP PAGE CONTENT ---
        "help_intro": """
        **Kernkonzept:**
        * 🚨 **Verstösse** messen die *Legalität* (Wurde eine Regel verletzt?)
        * ⭐ **Score** misst die *Qualität* (Wie nützlich sind die Daten?)
        """,
        
        "help_vio_title": "🚨 Schema-Verstösse",
        "help_vio_desc": """
        Dies sind **Binäre Fehler**. Entweder man besteht oder fällt durch.
        Basierend auf dem offiziellen BLW JSON-Schema.
        * **Fehlende ID**: `dct:identifier` ist leer.
        * **Fehlender Kontakt**: Keine E-Mail angegeben.
        * **Falsches Format**: Datum ist `2023/30/30` statt `YYYY-MM-DD`.
        """,
        "help_vio_goal": "🎯 **Ziel:** 0 Verstösse.",

        "help_score_title": "⭐ Qualitäts-Score (FAIRC)",
        "help_score_desc": """
        Dies ist ein **Punktesystem**.
        Sie erhalten Punkte, wenn Sie *mehr* tun.
        
        * **Auffindbarkeit:** Stichworte, Kategorien, Geografie, Zeit
        * **Zugänglichkeit:** Funktionierende Links, Direktdownloads
        * **Interoperabilität:** Offene Formate, DCAT-AP
        * **Wiederverwendbarkeit:** Lizenzen, Kontakt, Herausgeber
        * **Kontextualität:** Datumsangaben, Rechte
        """,
        "help_score_goal": "🎯 **Ziel:** Punkte maximieren (High Score).",

        "help_calc_title": "🧮 Score-Rechner",
        "help_table_dim": "Dimension",
        "help_table_crit": "Kriterium",
        "help_table_pts": "Punkte",
        
        # Detailed Scoring Criteria (Updated with Field Names)
        "crit_keywords": "Stichworte vorhanden (`dcat:keyword`)",
        "crit_themes": "Kategorien vorhanden (`dcat:theme`)",
        "crit_geo": "Geografische Abdeckung (`dct:spatial`)",
        "crit_time": "Zeitliche Abdeckung (`dct:temporal`)",
        
        "crit_access": "Access URL erreichbar (`dcat:accessURL`)",
        "crit_download": "Download URL vorhanden (`dcat:downloadURL`)",
        "crit_download_valid": "Download URL erreichbar (HTTP 200)",
        
        "crit_format": "Format angegeben (`dct:format`)",
        "crit_media": "Media Type angegeben (`dcat:mediaType`)",
        "crit_vocab": "Format/Media kontrolliert (Vokabular)",
        "crit_openfmt": "Offenes Format (CSV, JSON, etc.)",
        "crit_machine": "Maschinenlesbar",
        "crit_dcat": "DCAT-AP Konformität",
        
        "crit_license": "Lizenz vorhanden (`dct:license`)",
        "crit_lic_vocab": "Standard-Lizenz (Vokabular)",
        "crit_access_res": "Zugangsbeschränkung (`dct:accessRights`)",
        "crit_access_vocab": "Standard-Zugangsbegriff",
        "crit_contact": "Kontaktangabe vollständig (`dcat:contactPoint`)",
        "crit_publisher": "Herausgeber angegeben (`dct:publisher`)",
        
        "crit_rights": "Nutzungsrechte definiert (`dct:rights`)",
        "crit_filesize": "Dateigrössen angegeben (`dcat:byteSize`)",
        "crit_issue": "Erstellungsdatum (`dct:issued`)",
        "crit_mod": "Änderungsdatum (`dct:modified`)"
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
        
        "severity_high": "Élevée",
        "severity_med": "Moyenne",
        "severity_low": "Faible",
        "chart_score_dist": "Distribution des scores de qualité",
        "chart_top_errors": "Erreurs de validation fréquentes",

        "help_intro": """
        **Concept clé:**
        * 🚨 **Les Violations** mesurent la *Légalité* (Une règle a-t-elle été enfreinte ?)
        * ⭐ **Le Score** mesure la *Qualité* (Quelle est l'utilité des données ?)
        """,
        
        "help_vio_title": "🚨 Violations du Schéma",
        "help_vio_desc": """
        Ce sont des **Erreurs Binaires**. Soit ça passe, soit ça casse.
        Basé sur le schéma JSON officiel de l'OFAG.
        * **ID manquant**: `dct:identifier` est vide.
        * **Contact manquant**: Aucune adresse e-mail fournie.
        * **Mauvais format**: La date est `2023/30/30` au lieu de `YYYY-MM-DD`.
        """,
        "help_vio_goal": "🎯 **Objectif:** 0 Violations.",

        "help_score_title": "⭐ Score de Qualité (FAIRC)",
        "help_score_desc": """
        C'est un **Système de Points**.
        Vous gagnez des points en faisant *plus*.
        
        * **Retrouvabilité:** Mots-clés, Catégories, Géographie, Temps
        * **Accessibilité:** Liens fonctionnels, Téléchargements directs
        * **Interopérabilité:** Formats ouverts, DCAT-AP
        * **Réutilisabilité:** Licences, Contact, Éditeur
        * **Contextualité:** Dates, Droits
        """,
        "help_score_goal": "🎯 **Objectif:** Maximiser les points (High Score).",

        "help_calc_title": "🧮 Calculateur de Score",
        "help_table_dim": "Dimension",
        "help_table_crit": "Critère",
        "help_table_pts": "Points",
        
        # Detailed Scoring Criteria
        "crit_keywords": "Mots-clés fournis (`dcat:keyword`)",
        "crit_themes": "Catégories fournies (`dcat:theme`)",
        "crit_geo": "Couverture géographique (`dct:spatial`)",
        "crit_time": "Couverture temporelle (`dct:temporal`)",
        
        "crit_access": "URL d'accès fonctionnelle (`dcat:accessURL`)",
        "crit_download": "URL de téléchargement fournie (`dcat:downloadURL`)",
        "crit_download_valid": "URL de téléchargement fonctionnelle (HTTP 200)",
        
        "crit_format": "Format déclaré (`dct:format`)",
        "crit_media": "Type de média déclaré (`dcat:mediaType`)",
        "crit_vocab": "Vocabulaire contrôlé (Format)",
        "crit_openfmt": "Format ouvert (CSV, etc.)",
        "crit_machine": "Lisible par machine",
        "crit_dcat": "Conformité DCAT-AP",
        
        "crit_license": "Licence fournie (`dct:license`)",
        "crit_lic_vocab": "Licence standard (Vocabulaire)",
        "crit_access_res": "Restriction d'accès (`dct:accessRights`)",
        "crit_access_vocab": "Terme d'accès standard",
        "crit_contact": "Contact complet (`dcat:contactPoint`)",
        "crit_publisher": "Éditeur déclaré (`dct:publisher`)",
        
        "crit_rights": "Droits d'utilisation définis (`dct:rights`)",
        "crit_filesize": "Taille de fichier déclarée (`dcat:byteSize`)",
        "crit_issue": "Date de création (`dct:issued`)",
        "crit_mod": "Date de modification (`dct:modified`)"
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
        
        "severity_high": "Alta",
        "severity_med": "Media",
        "severity_low": "Bassa",
        "chart_score_dist": "Distribuzione dei punteggi",
        "chart_top_errors": "Errori di convalida frequenti",

        "help_intro": """
        **Concetto chiave:**
        * 🚨 **Le Violazioni** misurano la *Legalità* (È stata infranta una regola?)
        * ⭐ **Il Punteggio** misura la *Qualità* (Quanto sono utili i dati?)
        """,
        
        "help_vio_title": "🚨 Violazioni dello Schema",
        "help_vio_desc": """
        Questi sono **Errori Binari**. O si passa o si fallisce.
        Basato sullo schema JSON ufficiale dell'UFAG.
        * **ID mancante**: `dct:identifier` è vuoto.
        * **Contatto mancante**: Nessuna e-mail fornita.
        * **Formato errato**: La data è `2023/30/30` invece di `YYYY-MM-DD`.
        """,
        "help_vio_goal": "🎯 **Obiettivo:** 0 Violazioni.",

        "help_score_title": "⭐ Punteggio di Qualità (FAIRC)",
        "help_score_desc": """
        Questo è un **Sistema a Punti**.
        Ottieni punti facendo *di più*.
        
        * **Reperibilità:** Parole chiave, Categorie, Geografia, Tempo
        * **Accessibilità:** Link funzionanti, Download diretti
        * **Interoperabilità:** Formati aperti, DCAT-AP
        * **Riutilizzabilità:** Licenze, Contatto, Editore
        * **Contestualità:** Date, Diritti
        """,
        "help_score_goal": "🎯 **Obiettivo:** Massimizzare i punti (Punteggio Alto).",

        "help_calc_title": "🧮 Calcolatore del Punteggio",
        "help_table_dim": "Dimensione",
        "help_table_crit": "Criterio",
        "help_table_pts": "Punti",
        
        # Detailed Scoring Criteria
        "crit_keywords": "Parole chiave fornite (`dcat:keyword`)",
        "crit_themes": "Categorie fornite (`dcat:theme`)",
        "crit_geo": "Copertura geografica (`dct:spatial`)",
        "crit_time": "Copertura temporale (`dct:temporal`)",
        
        "crit_access": "URL di accesso funzionante (`dcat:accessURL`)",
        "crit_download": "URL di download fornito (`dcat:downloadURL`)",
        "crit_download_valid": "URL di download funzionante (HTTP 200)",
        
        "crit_format": "Formato dichiarato (`dct:format`)",
        "crit_media": "Tipo di supporto dichiarato (`dcat:mediaType`)",
        "crit_vocab": "Vocabolario controllato (Formato)",
        "crit_openfmt": "Formato aperto (CSV, ecc.)",
        "crit_machine": "Leggibile da macchina",
        "crit_dcat": "Conformità DCAT-AP",
        
        "crit_license": "Licenza fornita (`dct:license`)",
        "crit_lic_vocab": "Licenza standard (Vocabolario)",
        "crit_access_res": "Restrizione di accesso (`dct:accessRights`)",
        "crit_access_vocab": "Termine di accesso standard",
        "crit_contact": "Contatto completo (`dcat:contactPoint`)",
        "crit_publisher": "Editore dichiarato (`dct:publisher`)",
        
        "crit_rights": "Diritti di utilizzo definiti (`dct:rights`)",
        "crit_filesize": "Dimensione file dichiarata (`dcat:byteSize`)",
        "crit_issue": "Data di creazione (`dct:issued`)",
        "crit_mod": "Data di modifica (`dct:modified`)"
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
        
        "severity_high": "High",
        "severity_med": "Medium",
        "severity_low": "Low",
        "chart_score_dist": "Quality Score Distribution",
        "chart_top_errors": "Top Validation Errors",

        "help_intro": """
        **Core Concept:**
        * 🚨 **Violations** measure *Legality* (Did you break a rule?)
        * ⭐ **Score** measures *Quality* (How useful is the data?)
        """,
        
        "help_vio_title": "🚨 Schema Violations",
        "help_vio_desc": """
        These are **Binary Errors**. You either pass or fail.
        Based on the official BLW JSON Schema.
        * **Missing ID**: `dct:identifier` is empty.
        * **Missing Contact**: No email provided.
        * **Bad Format**: Date is `2023/30/30` instead of `YYYY-MM-DD`.
        """,
        "help_vio_goal": "🎯 **Goal:** 0 Violations.",

        "help_score_title": "⭐ Quality Score (FAIRC)",
        "help_score_desc": """
        This is a **Points System**.
        You gain points for doing *more*.
        Based on the `opendata.swiss` quality model.
        * **Findability:** Keywords, Categories, Geo, Time
        * **Accessibility:** Working Links, Direct Downloads
        * **Interoperability:** Open Formats, DCAT-AP
        * **Reusability:** Licenses, Contact, Publisher
        * **Contextuality:** Dates, Rights
        """,
        "help_score_goal": "🎯 **Goal:** Maximize points (High Score).",

        "help_calc_title": "🧮 Scoring Calculator",
        "help_table_dim": "Dimension",
        "help_table_crit": "Criteria",
        "help_table_pts": "Points",
        
        # Detailed Scoring Criteria (Updated with Field Names)
        "crit_keywords": "Keywords provided (`dcat:keyword`)",
        "crit_themes": "Categories provided (`dcat:theme`)",
        "crit_geo": "Geographical Coverage (`dct:spatial`)",
        "crit_time": "Temporal Coverage (`dct:temporal`)",
        
        "crit_access": "Access URL works (`dcat:accessURL`)",
        "crit_download": "Download URL provided (`dcat:downloadURL`)",
        "crit_download_valid": "Download URL works (HTTP 200)",
        
        "crit_format": "Format declared (`dct:format`)",
        "crit_media": "Media Type declared (`dcat:mediaType`)",
        "crit_vocab": "Controlled Vocabulary (Format)",
        "crit_openfmt": "Open Format (CSV, etc.)",
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
        "crit_mod": "Modification Date (`dct:modified`)"
    }
}