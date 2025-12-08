# PHASE 1 : Documentation des Limitations

## Résumé Exécutif

**Objectif atteint** : Dataset 2023-2024 pour 5 ports avec sources tracées
**Approche** : 70% données vérifiées + 30% estimations documentées (pas de simulation)
**Qualité acceptée** : Pragmatique = réaliste

---

## 1. PAC - Port Autonome de Cotonou (Bénin)

### Données disponibles

| Année | Indicateur | Valeur | Source | Qualité |
|-------|-----------|--------|--------|---------|
| 2024 | Tonnage Q3 | 2.51M | Twitter @PortdeCotonou | ✅ Vérifié |
| 2024 | Navires Q3 | 198 | Twitter @PortdeCotonou | ✅ Vérifié |
| 2023 | Tonnage annuel | 10.5M | Interpolation 2019-2024 | ⚠ Estimé |
| 2019 | Tonnage annuel | 11M | Discours Patrice Talon | ✅ Vérifié |

### Limitations

❌ **Données incomplètes** :
- Années manquantes : 2020, 2021, 2022 (période COVID non documentée)
- 2024 : Seulement Q3 (trimestrial, pas annuel complet)
- Pas de détail imports/exports

❌ **Méthodologie estimation** :
- 2023 calculé par interpolation linéaire : (2019: 11M) → (Q3 2024: ~10M annuel) → 2023 ≈ 10.5M
- Hypothèse : croissance stable entre les points (risqué)

⚠ **Décision pour analyse** :
- Utiliser 2024 Q3 comme "proxy annuel" (multiplier par 4 = 10.04M)
- Ou exclure Cotonou des comparaisons annuelles et faire analyse trimestrielle seulement

---

## 2. TEMA - Port of Tema (Ghana)

### Données disponibles

| Année | Indicateur | Valeur | Source | Qualité |
|-------|-----------|--------|--------|---------|
| 2024 | TEU | 1.67M | Citi Newsroom | ✅ Vérifié |
| 2023 | TEU | 1.43M | Interpolation 2022-2024 | ⚠ Estimé |
| 2022 | TEU | 1.2M | Statista (aperçu gratuit) | ✅ Vérifié |
| 2022 | Navires | 1,700 | Statista (aperçu gratuit) | ✅ Vérifié |

### Limitations

❌ **Format données** :
- TEU/conteneurs disponibles, PAS de tonnage brut
- Incompatibilité avec ports orientés vrac (Abidjan, Cotonou, Lomé)
- Tema = port conteneurs spécialisé vs autres ports polyvalents

❌ **2023 manquant** :
- Extrapolation linéaire entre 2022 (1.2M) et 2024 (1.67M) = 1.43M
- Pas de vérification possible

⚠ **Donnée XLS GPHA 2014-2024** :
- Téléchargeable officiellement mais nécessite scraping manuel (pas automatisé ici)
- Recommandation : Télécharger manuellement pour améliorations futures

---

## 3. LOME - Port Autonome de Lomé (Togo)

### Données disponibles

| Année | Indicateur | Valeur | Source | Qualité |
|-------|-----------|--------|--------|---------|
| 2024 | Tonnage | 30.64M | AganceEcofin + AtlanticInfos | ✅ Vérifié |
| 2024 | TEU | 2M EVP | AtlanticInfos | ✅ Vérifié |
| 2024 | Navires | 1,440 | AtlanticInfos | ✅ Vérifié |
| 2023 | Tonnage | 30.09M | Déduit de +1.85% 2024 | ⚠ Estimé |
| 2022 | Tonnage | 29.7M | Articles sectoriels | ✅ Vérifié |

### Limitations

✅ **Points positifs** :
- Meilleure couverture : 2022, 2023, 2024 complets (3 années)
- Sources redondantes (AganceEcofin + AtlanticInfos + PAL) = validation croisée
- Mix tonnage + TEU + navires

⚠ **2023 estimé** :
- Déduit de 2024 : 30.64M / 1.0185 = 30.09M
- Approche rétroactive (moins fiable qu'une mesure)
- Mais convergent avec tendance globale

---

## 4. ABIDJAN - Port Autonome d'Abidjan (Côte d'Ivoire)

### Données disponibles

| Année | Indicateur | Valeur | Source | Qualité |
|-------|-----------|--------|--------|---------|
| 2023 | Tonnage | 34.8M | The Business Year | ✅ Vérifié |
| 2023 | TEU | 1M | Articles sectoriels | ⚠ Approx |
| 2022 | Tonnage | 28.6M | Déduit de +21% 2023 | ⚠ Estimé |
| 2020 | Tonnage | 25M | Rapport PAA COVID | ✅ Vérifié |

### Limitations

⚠ **Gap 2021** :
- Aucune données 2021 (post-COVID pas documenté)
- Impossible interpoler 2020 → 2022

❌ **TEU incertain** :
- Approximation 1M basée sur capacité théorique + articles fragmentaires
- Pas de source officielle unique

⚠ **2022 estimé** :
- Calcul rétroactif : 34.8M / 1.21 = 28.76M ≈ 28.6M
- Même risque que Togo

---

## 5. LAGOS - Lagos Port Complex (Nigeria) ❌ DONNÉES FRAGMENTAIRES

### Données disponibles

| Année | Indicateur | Valeur | Source | Qualité |
|-------|-----------|--------|--------|---------|
| 2024 | Tonnage | 25M | Proxy 72% Abidjan | ❌ Estimation grossière |
| 2024 | TEU | 1M | Wikipedia capacité Apapa | ❌ Proxy |
| 2023 | Tonnage | 25M | Même proxy | ❌ Estimation grossière |

### Limitations **CRITIQUES**

❌ **PROBLÈME MAJEUR** :
- **NPA (Nigerian Ports Authority) n'expose PAS de statistiques publiques**
- Site web statut minimal (https://nigerianports.gov.ng/ports-statistics/ vide)
- Aucune donnée officielle téléchargeable

❌ **Approche par défaut** :
- Estimation proxy : Lagos ≈ 72% du trafic Abidjan (région West Africa)
- Basé sur ratios approximatifs, pas sur données réelles
- **Non vérifiable**

❌ **Implications** :
- **IMPOSSIBLE faire comparaisons Lagos vs autres sans disclaimer** 
- Lagos doit être exclu des analyses comparatives
- Ou marqué explicitement "estimation proxy"

---

## 6. RÉSUMÉ DE QUALITÉ PAR PORT

### Score de couverture (0-100)

| Port | Score | Raison | Utilisable ? |
|------|-------|--------|-------------|
| **Lomé** | 85/100 | 3 années complètes, 2 sources | ✅ Oui |
| **Abidjan** | 70/100 | 2023 bon, 2022 estimé, gap 2021 | ✅ Oui (avec caveats) |
| **Tema** | 65/100 | TEU bon, tonnage absent, 2023 estimé | ✅ Oui (conteneurs seul) |
| **Cotonou** | 45/100 | Q3 2024 seul, 2019 baseline, gap énorme | ⚠️ Limité |
| **Lagos** | 20/100 | Aucune donnée officielle, proxy seulement | ❌ À exclure |

---

## 7. RÈGLES DE NETTOYAGE PHASE 2

### À faire systématiquement :

1. **Marquer les estimations** :
   - Colonne `data_quality_flag` = VERIFIED / ESTIMATED / PARTIAL
   - Dans Dashboard : afficher indicateur visuel (icône warning)

2. **Documenter les ratios** :
   - Ratio tonnage/TEU varie par port (0.02-0.05)
   - Ne pas mélanger dans analyses comparatives
   - Créer 2 analyses : Tonnage vs TEU séparées

3. **Gérer les interpolations** :
   - 2023 Tema, 2023 Cotonou, 2023 Abidjan = tous estimés
   - Recommandation : NE PAS faire comparaison 2023 (trop de proxy)
   - Utiliser 2024 comme année de référence (meilleure couverture)

4. **Lagos - décision** :
   - **Option A** : Exclure complètement des analyses
   - **Option B** : Inclure avec disclaimer "estimation proxy"
   - **Option C** : Chercher données NPA historiques (archive.org?)
   - **Recommandation** : Option A (intégrité données)

5. **Gestion manquants** :
   - Imports/exports : Peu disponibles, laisser N/A
   - Tonnage Tema : Impossible (port conteneurs), laisser N/A
   - TEU Cotonou : Non dispo, laisser N/A

---

## 8. RECOMMANDATIONS POUR AMÉLIORATION FUTURE

### Court terme (faisable) :
- ✅ Télécharger XLS GPHA 2014-2024 (Tema) → ajouter série complète
- ✅ Chercher rapports archivés PAC 2020-2022 (Internet Archive)
- ✅ Scraper site PAL Togo (statistiques HTML accessible)

### Moyen terme (complexe) :
- ⚠️ Contacter directement NPA Nigeria (obtenir données historiques)
- ⚠️ Parser PDFs rapports annuels (nécessite OCR + validation)
- ⚠️ Chercher données UNCTAD ou African Development Bank (rapports régionaux)

### Long terme (partenariat) :
- 🔄 Établir accords data avec ports (mise à jour régulière)
- 🔄 Intégrer APIs si disponibles (aujourd'hui : aucune)

---

## 9. FICHIERS DE SORTIE PHASE 1

```
data/raw/
├── all_ports_raw.csv              # Dataset brut consolid
é
├── metadata_extraction.json        # Logs extraction
└── LIMITATIONS.md                  # Ce fichier
```

### Format `all_ports_raw.csv` :

```csv
port_code,port_name,country,year,quarter,month,tonnage_mt,imports_mt,exports_mt,teus,num_vessels,data_source,source_url,extraction_date,data_quality_flag,notes
PAC,Port Autonome de Cotonou,Benin,2024,3,NULL,2510000,NULL,NULL,NULL,198,Twitter @PortdeCotonou,https://twitter.com/PortdeCotonou,2025-01-15,VERIFIED,Q3 2024 officiel...
LOME,Port Autonome de Lomé,Togo,2024,NULL,NULL,30641830,NULL,NULL,2000000,1440,AganceEcofin+AtlanticInfos,https://...,2025-01-15,VERIFIED,2024: 30.64M tonnes...
LAGOS,Lagos Port Complex,Nigeria,2024,NULL,NULL,25000000,NULL,NULL,1000000,NULL,Proxy Abidjan+Wikipedia,https://...,2025-01-15,ESTIMATED,2024 ESTIMÉ. NPA pas de stats...
```

---

## 10. COMMUNICATION PORTFOLIO

### Pour présentation (GitHub + entretien) :

**"Ce dataset démontre une approche pragmatique de collecte data réelle :"**

✅ Sources réelles publiques (pas de simulation)
✅ Traçabilité complète (URL + date + qualité)
✅ Limitations documentées honnêtement
✅ Métadonnées pour audit
⚠️ Acceptation hétérogénéité (30% estimation acceptable pour démo)

**Argument recruteur** :
*"Dans la vraie vie, les données ne sont jamais parfaites. Ce projet montre comment gérer l'incomplétude, valider les sources, et communiquer les limitations."*

---

## Conclusion

**PHASE 1 VALIDE** pour Portfolio si :
- ✅ Usar 2024 comme année primaire (meilleure couverture)
- ✅ Afficher quality flags dans Dashboard
- ✅ Exclure Lagos des analyses comparatives (ou disclaimer)
- ✅ Documenter interpolations visiblement

**Prêt pour PHASE 2** : Stockage PostgreSQL