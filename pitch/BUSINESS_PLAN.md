# PlasticPatrol — Business Plan

---

## 1. Executive Summary

Eleven million tonnes of plastic enter the world's oceans every year (UNEP, 2023). Rivers, ports, and coastlines act as primary entry points, yet no operational system today can detect accumulations, dispatch citizens to clean them, and then independently confirm the cleanup happened — creating a verification gap that blocks governments and corporations from meeting their legal obligations. The result is a compliance bottleneck worth billions of euros annually.

PlasticPatrol closes that loop. The platform combines Copernicus Sentinel-2 satellite imagery to detect surface plastic hotspots at 10-metre resolution, a gamified mobile app that routes citizen cleanup crews to flagged sites, and a satellite re-pass 48 hours later to confirm the debris has been removed. Machine-learning photo verification via a MobileNetV2 classifier validates each citizen submission before the final satellite confirmation, creating a four-stage audit trail that is independently verifiable and legally defensible.

The business model is a hybrid of three revenue legs: B2G SaaS dashboards sold to port authorities and coastal municipalities, B2B verified-cleanup credits sold to plastic-EPR-obligated packaging producers, and a B2C citizen app that is free to use and functions as the unfair competitive moat — every citizen verification simultaneously trains the ML model and generates the ground-truth data that institutional buyers pay for.

PlasticPatrol is seeking €150k in seed funding or a non-dilutive grant equivalent, introductions to port authority and EMSA contacts for a first paid pilot, mentorship on positioning EPR credit pricing to large packaging producers, and continued Copernicus and ESA data access at scale beyond hackathon-tier quotas.

---

## 2. Problem & Market

Global plastic pollution is accelerating. UNEP estimates 11 million tonnes of plastic waste enter marine environments annually, a figure projected to triple by 2040 without intervention. Rivers, harbours, and coastal zones concentrate debris before it disperses into the open ocean, making them the highest-leverage and most economically viable intervention points.

Regulation is creating a compliance market of meaningful scale. The EU **Packaging and Packaging Waste Regulation (PPWR)**, entered into force in 2024, sets binding targets for recyclability and recycled content across all packaging placed on the EU market. Alongside it, national **Extended Producer Responsibility (EPR)** schemes legally require plastic packaging producers to fund and demonstrate verified cleanup activity proportional to the plastic they place on the market. Both frameworks demand auditable evidence — not estimates, not voluntary pledges, but verified records of plastic removed. That evidence does not currently exist at scale.

The **Total Addressable Market (TAM)** for EU plastic-EPR compliance services reaches €1.5 billion by 2027, driven by PPWR enforcement timelines and expanding national EPR mandates. The **Serviceable Addressable Market (SAM)** is the Black Sea and Mediterranean coastal zone — over 40,000 km of coastline across more than 20 EU and candidate-member port authorities. The **Serviceable Obtainable Market (SOM)**: one port pilot in Year 1, four monitored zones in Year 2, fifteen zones across three sea basins by Year 3.

---

## 3. Solution & Tech Moat

PlasticPatrol operates a closed-loop detection-and-verification architecture. Sentinel-2 imagery is ingested via the Copernicus Data Space Ecosystem and processed through a custom evalscript that combines four spectral indices: the Normalised Difference Water Index (NDWI) to isolate water surfaces, the Floating Debris Index (FDI) to identify surface anomalies consistent with plastic, the Normalised Difference Vegetation Index (NDVI) to exclude organic matter, and a SWIR band filter to further discriminate synthetic materials. This pipeline runs at 10-metre native resolution and flags candidate hotspots without human intervention.

Flagged hotspots are pushed to the citizen app as missions. Volunteers navigate to the site, execute the cleanup, and upload georeferenced photos. Each photo is classified by an on-device MobileNetV2 model fine-tuned on plastic-in-water imagery. Submissions that pass ML classification enter a verification queue; a satellite re-pass 48–72 hours later confirms surface-debris disappearance. Only completions that clear all four stages — satellite detection, citizen arrival, ML photo validation, satellite re-pass confirmation — generate a verified-cleanup record.

The defensibility of this system deepens over time. Each citizen verification adds a labelled data point to the training set, improving classifier accuracy in a loop no competitor can replicate without a comparable citizen network. First-mover EPR partnerships establish PlasticPatrol's data format as the reference standard for compliance reporting, raising switching costs for institutional buyers. Proprietary ground-truth dataset plus institutional lock-in constitutes the long-term moat.

---

## 4. Business Model

### B2G — Public Sector Dashboards

Port authorities and coastal municipalities need real-time situational awareness of plastic accumulation within their jurisdictions. They face liability exposure under national environmental law, pressure from EU port-state directives, and growing public scrutiny. PlasticPatrol sells them an annual SaaS subscription that includes: a live Sentinel-2-powered debris map for their zone, automated cleanup-dispatch integration with citizen crews, and monthly regulatory-grade verification reports.

Target buyers in the near term are **Constanța Port** (Romania's primary Black Sea commercial port), the municipality of **Galați** (Danube corridor gateway), **Varna** port authority (Bulgaria), **Piraeus** (Greece, the largest EU Mediterranean port), and **EMSA** (the European Maritime Safety Agency) as a supranational framework customer. Pricing is tiered by coastline length and monitoring frequency: **€20,000–€80,000 per zone per year**. The sales motion is pilot → reference customer → regional rollout. A single verified reference — Constanța Port — unlocks credibility across the Black Sea basin.

### B2B — Verified-Cleanup Credits

Plastic packaging producers subject to EPR schemes must demonstrate funded cleanup activity to national compliance registers. Today they rely on self-reported tonnage estimates or opaque third-party schemes. PlasticPatrol sells them auditable, satellite-verified cleanup records — each record backed by four-stage evidence — that can be submitted directly to EPR compliance registers and ESG disclosure frameworks.

Target buyers are **Coca-Cola HBC**, **Nestlé**, **Unilever**, **Mars**, and **Romaqua**, all of which carry EPR obligations in at least one Black Sea or Mediterranean market and have public plastic-reduction commitments. Pricing follows a per-kilogram verified-plastic-removed model, analogous to voluntary carbon credits: **€0.50–€2.00/kg** depending on site difficulty and regional EPR registry requirements. The sales motion begins with branded sponsorship pilots — a "Coca-Cola Black Sea Zone" campaign attaches corporate branding to a monitored cleanup region, generating marketing value alongside compliance value — and converts into multi-year credit purchase contracts as EPR enforcement intensifies.

### B2C — Citizen App (the Moat)

The citizen app is free. There is no advertising, no data-brokerage monetisation, and no dark-pattern engagement mechanics. Monetisation through degraded engagement would destroy the one asset the platform depends on: a motivated, high-quality citizen contributor base.

Revenue from the consumer layer is modest by design. A **premium tier at €2/month** provides advanced personal stats, deeper impact analytics, and exclusive badge tiers — a retention signal, not a growth driver. Affiliate links to reusable bottles, beach-cleanup kits, and ocean-safe sunscreen generate commission income. NGO co-branded campaigns with **Plastic Soup Foundation**, **WWF**, and **Ocean Conservancy** drive app downloads and media coverage at no paid-acquisition cost.

The strategic value of B2C dwarfs its direct revenue contribution. Citizens are the verification layer. Without citizen submissions, the platform detects plastic but cannot confirm removal — the closed loop breaks. Every active citizen volunteer reduces verification cost, improves ML accuracy, and generates the auditable evidence that institutional buyers pay for. The citizen network is the unfair advantage no competitor currently possesses.

### Sponsors and Non-Dilutive Funding

Corporates can pay to attach their logo and sustainability narrative to a specific monitored cleanup zone — **branded cleanup zones** functioning as a sponsorship product. EU **Horizon Europe** grant funding is targeted for the first 9 months to cover satellite API costs and initial BD overhead. **ESA BIC** (ESA Business Incubation Centre) participation provides non-dilutive support, credibility, and access to Copernicus data infrastructure beyond standard quotas.

---

## 5. Go-to-Market

**Year 1** is defined by a single proof point: a paid or in-kind pilot with **Constanța Port**, generating the first verified-cleanup report issued to a real institutional customer. Simultaneously, a first corporate sponsor — target: **Coca-Cola HBC Romania** — is brought on for a branded Black Sea cleanup zone, providing revenue and a consumer-facing campaign. A Horizon Europe application is submitted in the first six months.

**Year 2** expands across the Black Sea basin. Romania, Bulgaria, and Turkey come online as monitored zones, with three to five corporate sponsors across EPR and branded-zone products. EMSA engagement begins for a pan-European monitoring framework.

**Year 3** targets the Mediterranean and Adriatic coastlines, reaching 15 monitored zones and 8 corporate sponsors. EPR-credit volume at scale drives revenue to €1.8M. Premium-tier adoption grows proportionally with the app user base, reflecting three years of compounding citizen network growth.

---

## 6. Competitive Landscape

| | PlasticPatrol | Plastic Pirates | The Ocean Cleanup | OceanScan / Marine Litter Watch |
|---|---|---|---|---|
| Satellite detection | ✅ Sentinel-2 10m | ❌ | ❌ | ✅ |
| ML photo verification | ✅ MobileNetV2 | ❌ | ❌ | ❌ |
| Citizen engagement | ✅ Gamified app | ✅ School programmes | ❌ | ⚠️ Reporting only |
| Closed-loop verification | ✅ Re-pass confirms | ❌ | ❌ | ❌ |

**Plastic Pirates** runs school-based citizen science programmes across Germany and Northern Europe. They generate litter survey data but have no satellite detection layer, no ML classifier, and no mechanism to verify that a flagged site was cleaned. **The Ocean Cleanup** deploys physical collection systems in the open ocean — complementary in intent but operating at a different scale, with no citizen engagement and no feedback loop. **OceanScan and Marine Litter Watch** (EEA/JRC-affiliated) provide satellite-derived litter observation dashboards but do not dispatch cleanup crews, do not verify removal, and do not generate compliance-grade evidence.

No competitor closes the loop end-to-end. Detection without verified removal is an observation platform. Cleanup without satellite confirmation is unauditable. The four-stage pipeline — satellite detection, citizen dispatch, ML verification, satellite re-pass — is what converts environmental data into a legally defensible compliance product.

---

## 7. Financial Projection

| Year | Revenue | Drivers |
|---|---|---|
| Y1 | €50k | 1 port pilot + 1 corporate sponsor + Horizon grant slice |
| Y2 | €400k | 4 zones × ~€40k + 3 corporate sponsors × ~€80k |
| Y3 | €1.8M | 15 zones + 8 corporate sponsors + premium-tier scaling + EPR-credit volume |

Dominant costs are the four-person development team (4 FTE), Copernicus satellite API quota, and business development headcount for B2G and B2B sales cycles. Infrastructure (cloud compute, PostGIS hosting, ML serving) is modest relative to personnel. Gross margin is approximately **40% in Year 1**, climbing to **70% by Year 3** as fixed costs amortise across an expanding customer base and EPR-credit revenue scales without proportional cost growth.

The Year 1 figure is conservative: one Constanța Port contract at the B2G low end (€20k) plus one branded corporate zone (€20k) plus a Horizon grant tranche (€10k) reaches €50k. Year 2 growth is driven by replicating across three additional zones, a process that is operationally templated after Year 1.

---

## 8. Team & Ask

**Rares Neacsu — Backend & Satellite Pipeline Lead.** Rares designed and built the full Copernicus integration stack, from Sentinel-2 scene ingestion through the custom evalscript spectral pipeline to PostGIS-backed hotspot persistence. He brings deep experience in geospatial data engineering and distributed backend systems, and owns the satellite-to-database reliability that the platform's verification guarantees depend on.

**Matei Necula — Full-Stack & ML Developer.** Matei built the MobileNetV2 photo-classification pipeline and integrated it end-to-end with the citizen app and backend verification queue. He owns the ML training loop, the mobile app's core logic, and the data pipeline that connects citizen submissions to the satellite re-pass trigger. His work is the technical centrepiece of the closed-loop verification system.

**Andrei Stan — Frontend & Map Developer.** Andrei owns the citizen-facing Angular application and the Leaflet-based interactive map that visualises active cleanup missions and verified hotspots. He designed the gamification layer — mission cards, badge systems, personal impact dashboards — that drives citizen retention and submission quality.

**Swiorx — Backend & API Developer.** Swiorx built and maintains the REST API surface, authentication layer, and the automated scheduler that triggers satellite re-pass verification jobs. He owns the system's operational reliability and the API contracts that allow future integration with EPR registries and municipal data systems.

### The Ask

PlasticPatrol is seeking:

- **€150,000** in seed investment or a non-dilutive grant equivalent (Horizon Europe, ESA BIC, national innovation fund) to fund 9 months of operations through the first paid pilot and first corporate sponsor contract.
- **Pilot partner introductions** — specifically to port authority procurement contacts at Constanța and to EMSA's maritime environment division.
- **Mentorship on EPR compliance sales** — how to price verified-cleanup credits relative to national EPR register requirements, and how to position the product to sustainability and compliance teams at Coca-Cola HBC, Nestlé, Unilever, Mars, and Romaqua.
- **Continued Copernicus and ESA data access** at operational scale — scene frequency and area-of-interest coverage beyond the quotas available under the hackathon environment.

The market window is open now. PPWR enforcement timelines are fixed. EPR compliance deadlines are approaching across every major EU market. PlasticPatrol is the only system that can generate the verified-cleanup evidence that both governments and producers need — and it is ready to pilot.
