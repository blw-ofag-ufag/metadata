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
        "inspector_ds_title": "Datensatz-Titel",
        
        # Recommendations - Titles
        "inspector_improve_title": "🚀 Verbesserungspotenzial",
        "inspector_improve_desc": "Erfüllen Sie folgende Kriterien, um den Score zu maximieren:",
        "inspector_perfect_score": "Perfekt! Dieser Datensatz erreicht die maximale Punktzahl.",
        
        # Recommendations - Messages (Strict Logic)
        "msg_missing_keywords": "Stichworte hinzufügen (`dcat:keyword`)",
        "msg_missing_themes": "Kategorien hinzufügen (`dcat:theme`)",
        "msg_missing_geo": "Geografische Abdeckung angeben (`dct:spatial`)",
        "msg_missing_time": "Zeitliche Abdeckung angeben (`dct:temporal`)",
        "msg_broken_links": "Defekte Links reparieren (`dcat:accessURL` / `dcat:downloadURL`)",
        "msg_missing_download": "Download-URL hinzufügen (`dcat:downloadURL`)",
        "msg_formats": "Offene Formate verwenden (`dct:format`, `dcat:mediaType`)",
        
        "msg_license": "Lizenz angeben (`dct:license`)",
        "msg_license_vocab": "Standard-Lizenz verwenden (opendata.swiss Vokabular)",
        
        "msg_contact": "Kontaktstelle erfassen (`dcat:contactPoint`)",
        "msg_publisher": "Herausgeber angeben (`dct:publisher`)",
        
        "msg_access_rights": "Zugangsbeschränkung angeben (`dct:accessRights`)",
        "msg_access_rights_vocab": "Standard-Zugangsbegriff verwenden (Public, etc.)",
        
        "msg_date_issued": "Erstellungsdatum angeben (`dct:issued`)",
        "msg_date_modified": "Änderungsdatum angeben (`dct:modified`)",
        
        "msg_rights": "Nutzungsrechte angeben (`dct:rights`)",
        "msg_byte_size": "Dateigröße angeben (`dcat:byteSize`)",
        
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
        
        "crit_keywords": "Stichworte vorhanden",
        "crit_themes": "Kategorien vorhanden",
        "crit_geo": "Geografische Abdeckung",
        "crit_time": "Zeitliche Abdeckung",
        "crit_access": "Access URL erreichbar",
        "crit_download": "Download URL vorhanden",
        "crit_download_valid": "Download URL erreichbar",
        "crit_format": "Format angegeben",
        "crit_media": "Media Type angegeben",
        "crit_vocab": "Format/Media kontrolliert",
        "crit_openfmt": "Offenes Format (CSV, etc.)",
        "crit_machine": "Maschinenlesbar",
        "crit_dcat": "DCAT-AP Konformität",
        "crit_license": "Lizenz vorhanden",
        "crit_lic_vocab": "Standard-Lizenz (Vokabular)",
        "crit_access_res": "Zugangsbeschränkung",
        "crit_access_vocab": "Standard-Zugangsbegriff",
        "crit_contact": "Kontaktangabe vollständig",
        "crit_publisher": "Herausgeber angegeben",
        "crit_rights": "Nutzungsrechte definiert",
        "crit_filesize": "Dateigrössen angegeben",
        "crit_issue": "Erstellungsdatum",
        "crit_mod": "Änderungsdatum"
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
        "inspector_ds_title": "Titre du jeu de données",

        # Recommendations
        "inspector_improve_title": "🚀 Potentiel d'amélioration",
        "inspector_improve_desc": "Remplissez les critères suivants pour maximiser le score :",
        "inspector_perfect_score": "Parfait ! Ce jeu de données atteint le score maximal.",
        
        # Recommendation Messages
        "msg_missing_keywords": "Ajouter des mots-clés (`dcat:keyword`)",
        "msg_missing_themes": "Ajouter des catégories (`dcat:theme`)",
        "msg_missing_geo": "Indiquer la couverture géographique (`dct:spatial`)",
        "msg_missing_time": "Indiquer la couverture temporelle (`dct:temporal`)",
        "msg_broken_links": "Réparer les liens cassés (`dcat:accessURL` / `dcat:downloadURL`)",
        "msg_missing_download": "Ajouter une URL de téléchargement (`dcat:downloadURL`)",
        "msg_formats": "Utiliser des formats ouverts (`dct:format`, `dcat:mediaType`)",
        
        "msg_license": "Indiquer une licence (`dct:license`)",
        "msg_license_vocab": "Utiliser une licence standard (Vocabulaire)",
        
        "msg_contact": "Saisir le point de contact (`dcat:contactPoint`)",
        "msg_publisher": "Indiquer l'éditeur (`dct:publisher`)",
        
        "msg_access_rights": "Indiquer les droits d'accès (`dct:accessRights`)",
        "msg_access_rights_vocab": "Utiliser un terme d'accès standard (Public, etc.)",
        
        "msg_date_issued": "Indiquer la date de création (`dct:issued`)",
        "msg_date_modified": "Indiquer la date de modification (`dct:modified`)",
        
        "msg_rights": "Indiquer les droits d'utilisation (`dct:rights`)",
        "msg_byte_size": "Indiquer la taille du fichier (`dcat:byteSize`)",
        
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
        "help_table_pts": "Punkte",
        
        "crit_keywords": "Mots-clés fournis",
        "crit_themes": "Catégories fournies",
        "crit_geo": "Couverture géographique",
        "crit_time": "Couverture temporelle",
        "crit_access": "URL d'accès fonctionnelle",
        "crit_download": "URL de téléchargement fournie",
        "crit_download_valid": "URL de téléchargement fonctionnelle",
        "crit_format": "Format déclaré",
        "crit_media": "Type de média déclaré",
        "crit_vocab": "Vocabulaire contrôlé (Format)",
        "crit_openfmt": "Format ouvert (CSV, etc.)",
        "crit_machine": "Lisible par machine",
        "crit_dcat": "Conformité DCAT-AP",
        "crit_license": "Licence fournie",
        "crit_lic_vocab": "Licence standard (Vocabulaire)",
        "crit_access_res": "Restriction d'accès",
        "crit_access_vocab": "Terme d'accès standard",
        "crit_contact": "Contact complet",
        "crit_publisher": "Éditeur déclaré",
        "crit_rights": "Droits d'utilisation définis",
        "crit_filesize": "Taille de fichier déclarée",
        "crit_issue": "Date de création",
        "crit_mod": "Date de modification"
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
        "inspector_ds_title": "Titolo del dataset",

        # Recommendations
        "inspector_improve_title": "🚀 Potenziale di miglioramento",
        "inspector_improve_desc": "Soddisfare i seguenti criteri per massimizzare il punteggio:",
        "inspector_perfect_score": "Perfetto! Questo dataset raggiunge il punteggio massimo.",
        
        # Recommendation Messages
        "msg_missing_keywords": "Aggiungere parole chiave (`dcat:keyword`)",
        "msg_missing_themes": "Aggiungere categorie (`dcat:theme`)",
        "msg_missing_geo": "Indicare la copertura geografica (`dct:spatial`)",
        "msg_missing_time": "Indicare la copertura temporale (`dct:temporal`)",
        "msg_broken_links": "Riparare i link interrotti (`dcat:accessURL` / `dcat:downloadURL`)",
        "msg_missing_download": "Aggiungere URL di download (`dcat:downloadURL`)",
        "msg_formats": "Utilizzare formati aperti (`dct:format`, `dcat:mediaType`)",
        
        "msg_license": "Indicare una licenza (`dct:license`)",
        "msg_license_vocab": "Utilizzare una licenza standard (Vocabolario)",
        
        "msg_contact": "Inserire il punto di contatto (`dcat:contactPoint`)",
        "msg_publisher": "Indicare l'editore (`dct:publisher`)",
        
        "msg_access_rights": "Indicare i diritti di accesso (`dct:accessRights`)",
        "msg_access_rights_vocab": "Utilizzare un termine di accesso standard (Public, etc.)",
        
        "msg_date_issued": "Indicare la data di creazione (`dct:issued`)",
        "msg_date_modified": "Indicare la data di modifica (`dct:modified`)",
        
        "msg_rights": "Indicare i diritti d'uso (`dct:rights`)",
        "msg_byte_size": "Indicare la dimensione del file (`dcat:byteSize`)",
        
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
        
        "crit_keywords": "Parole chiave fornite",
        "crit_themes": "Categorie fornite",
        "crit_geo": "Copertura geografica",
        "crit_time": "Copertura temporale",
        "crit_access": "URL di accesso funzionante",
        "crit_download": "URL di download fornito",
        "crit_download_valid": "URL di download funzionante",
        "crit_format": "Formato dichiarato",
        "crit_media": "Tipo di supporto dichiarato",
        "crit_vocab": "Vocabolario controllato (Formato)",
        "crit_openfmt": "Formato aperto (CSV, ecc.)",
        "crit_machine": "Leggibile da macchina",
        "crit_dcat": "Conformità DCAT-AP",
        "crit_license": "Licenza fornita",
        "crit_lic_vocab": "Licenza standard (Vocabolario)",
        "crit_access_res": "Restrizione di accesso",
        "crit_access_vocab": "Termine di accesso standard",
        "crit_contact": "Contatto completo",
        "crit_publisher": "Editore dichiarato",
        "crit_rights": "Diritti di utilizzo definiti",
        "crit_filesize": "Dimensione file dichiarata",
        "crit_issue": "Data di creazione",
        "crit_mod": "Data di modifica"
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
        "inspector_ds_title": "Dataset Title",

        # Recommendations
        "inspector_improve_title": "🚀 Improvement Opportunities",
        "inspector_improve_desc": "Fulfill the following criteria to maximize your score:",
        "inspector_perfect_score": "Perfect! This dataset achieves the maximum score.",
        
        # Recommendation Messages (Updated with Vocabulary)
        "msg_missing_keywords": "Add Keywords (`dcat:keyword`)",
        "msg_missing_themes": "Add Categories (`dcat:theme`)",
        "msg_missing_geo": "Define Geographical Coverage (`dct:spatial`)",
        "msg_missing_time": "Define Temporal Coverage (`dct:temporal`)",
        "msg_broken_links": "Fix broken links (`dcat:accessURL` / `dcat:downloadURL`)",
        "msg_missing_download": "Add Download URL (`dcat:downloadURL`)",
        "msg_formats": "Use open, machine-readable formats (`dct:format`, `dcat:mediaType`)",
        
        "msg_license": "Add License (`dct:license`)",
        "msg_license_vocab": "Use Standard License (Vocabulary)",
        
        "msg_contact": "Add Contact Point (`dcat:contactPoint`)",
        "msg_publisher": "Add Publisher (`dct:publisher`)",
        
        "msg_access_rights": "Define Access Rights (`dct:accessRights`)",
        "msg_access_rights_vocab": "Use Standard Access Term (Public, etc.)",
        
        "msg_date_issued": "Provide Issue Date (`dct:issued`)",
        "msg_date_modified": "Provide Modification Date (`dct:modified`)",
        
        "msg_rights": "Define Usage Rights (`dct:rights`)",
        "msg_byte_size": "Define File Size (`dcat:byteSize`)",
        
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
        
        "crit_keywords": "Keywords provided",
        "crit_themes": "Categories provided",
        "crit_geo": "Geographical Coverage",
        "crit_time": "Temporal Coverage",
        "crit_access": "Access URL works",
        "crit_download": "Download URL provided",
        "crit_download_valid": "Download URL works",
        "crit_format": "Format declared",
        "crit_media": "Media Type declared",
        "crit_vocab": "Controlled Vocabulary (Format)",
        "crit_openfmt": "Open Format (CSV, etc.)",
        "crit_machine": "Machine Readable",
        "crit_dcat": "DCAT-AP Compliance",
        "crit_license": "License provided",
        "crit_lic_vocab": "Standard License (Vocabulary)",
        "crit_access_res": "Access Restriction",
        "crit_access_vocab": "Standard Access Term",
        "crit_contact": "Contact Point provided",
        "crit_publisher": "Publisher declared",
        "crit_rights": "Rights defined",
        "crit_filesize": "File size declared",
        "crit_issue": "Issue Date",
        "crit_mod": "Modification Date"
    }
}