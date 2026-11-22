# OsdagBridge — LaTeX Report Generator Refactoring & Enhancements

**FOSSEE Winter Internship 2026 | Software Engineering Screening Task**
**Applicant:** Jagadeesh Kota
**Repository:** https://github.com/Kota-Jagadeesh/OsdagBridge
**Implementation branch:** `feature/latex-report-enhancements`
**Report comparison:** `Report_Before.pdf` and `Report_After.pdf`
**Document date:** 22 November 2026

---

## 1. Executive Summary

The OsdagBridge design-report generator was improved with emphasis on long-document typesetting, clear structural-design presentation, dynamically generated visualization, and maintainable formatting configuration. The previous output exhibited long tables without consistently repeated headings, multirow labels extending into footer areas, combined vehicle and footway loading information, and a lack of graphical summaries for design utilization and material take-off.

The modified generator now constructs repeatable long-table headers, handles several problematic page breaks, separates vehicle and footway loading, and produces utilization-ratio and material-quantity figures from available report data. Document styling has been extracted into `styles.py`, and table normalization and plotting are isolated in `table_layout.py` and `charts.py` respectively. Later fixes addressed incorrect units and floating-point output and prevented the executive summary from reporting an unconditional PASS when the governing girder fatigue result failed.

**Evidence from the generated enhanced report:** the inspected `REP.pdf` contains 50 PDF pages (49 internally numbered report pages), four utilization-ratio figures in Section 5.5, three quantity figures in Chapter 7, repeated headings in multi-page girder tables, and separate vehicle and footway live-load tables. The document retains the calculated girder fatigue utilization ratio **2.45**, which is correctly classified as **FAIL**. These observations describe the submitted demonstration run, not a guarantee for all possible bridge configurations.

## 2. Scope and Engineering Constraints

The work is deliberately concentrated in `src/osdagbridge/core/reports/`. The design solver, code checks, demand/capacity calculations, and loading algorithms were not modified for the purpose of changing results. Existing structural results are displayed as received by the report workflow; unavailable data is identified rather than estimated. The report continues to use the project's established Python-generated LaTeX assembly and `pdflatex` compilation pipeline, with Matplotlib used to create figure assets. Although the screening task mentions PyLaTeX, the inspected implementation builds many chapter fragments as LaTeX strings; this refactoring preserves that architecture rather than representing it as a complete migration to PyLaTeX objects.

## 3. Architecture and Files Modified

| File | Responsibility / implemented change |
|---|---|
| `styles.py` **(new)** | Centralized LaTeX preamble, document geometry, header/footer treatment, global table spacing, and chart color constants. |
| `table_layout.py` **(new)** | Post-assembly normalization of simple `longtable` headers and continuation captions; skips table structures that already define headers or require special treatment. |
| `charts.py` **(new)** | Extracts valid numeric report values, creates Matplotlib bar charts, writes PNGs, and emits LaTeX figure markup. |
| `report_generator.py` | Uses centralized preamble, assembles chapter output, creates temporary image assets, applies table normalization, and compiles the complete LaTeX report. |
| `chap2.py` | Corrects metre-to-millimetre display of girder dimensions and formats selected geometry values consistently. |
| `chap3.py` | Separates vehicle live-load data from footway/footpath live-load data, including the vehicle selection passed to the report. |
| `chap4.py` | Avoids displaying empty demand/reaction tables as if they contained results; uses concise unavailable-data messages where source data or figures are absent. |
| `chap5.py` | Adds repeated headings and safer row grouping to selected long design tables; integrates utilization-ratio charts into Section 5.5. |
| `chap6.py` | Embeds CAD figures when actual image paths are available and produces compact availability notices instead of misleading placeholder figures when they are not. |
| `chap7.py` | Integrates quantity charts using the material-takeoff fields and identifies missing end-diaphragm weight. |
| `executive_summary.py` | Renders the design outcome based on available check results rather than an unconditional passing statement; improves displayed metadata/geometry. |
| `report_utils.py` | Supporting report formatting and figure-handling utilities. |

Other existing chapter modules remain part of the report assembly, but should not be described as changed unless confirmed by the final Git diff.

### 3.1 Report generation flow

```text
OsdagBridge design inputs + calculation outputs
                  |
                  v
         Report payload / metadata
                  |
                  v
  report_generator.py: assemble chapters
       |                    |
       v                    v
  Chapter tables       charts.py: PNG assets
       |                    |
       +---------+----------+
                 |
                 v
     table_layout.py: normalize simple longtables
                 |
                 v
       styles.py: preamble and page theme
                 |
                 v
            .tex -> pdflatex -> .pdf
```

The generator writes figure files into a temporary working directory and uses them during compilation. The PDFs and associated `.tex` output are the reproducible artifacts for visual review.

## 4. Changes by Screening Requirement

### 4.1 Repeating table headings on page breaks

**Problem.** Long design tables continued across pages without sufficient context. In particular, readers could lose track of the table identity and column meanings.

**Implementation.** The report uses LaTeX `longtable` continuation constructs, including `\endfirsthead` and `\endhead`, and unnumbered continuation captions (`\caption[]{... (continued)}`). `table_layout.py` inserts a repeated header only for simple tables that lack their own header declarations; it avoids treating existing multirow header layouts as ordinary one-row headers. Complex tables retain their explicit definitions. Changes to tables such as Girder Section Properties and the Overall Design Check Summary were preserved.

**Observed result.** The enhanced PDF repeats the caption and columns of Table 5.1 across its continuation pages, and similarly repeats the headings of Tables 5.4 and 5.29. The continuation caption does not introduce a new table number.

### 4.2 Footer clearance, pagination and row readability

**Problem.** Group labels using `\multirow` could extend beyond the region assigned to a page (particularly around the G4 stiffener rows), and tables could start too near a page boundary.

**Implementation.** Problematic stiffener and girder groups were refactored to display the girder identifier on independently breakable rows where needed. The centralized document style defines the A4 geometry, footer separation and table row spacing. The long-table normalization adds a controlled `\Needspace` check before eligible tables. These changes reduce page-break and footer collisions without globally forcing each large table onto a separate page.

**Observed result.** Table 5.7 continues onto the next page with its own heading, and the former G4/footer collision is not present in the inspected report. The 50-page result still contains page splits where necessary; pagination is not claimed to be perfect for every dataset.

### 4.3 Distinct vehicle live load and footway live load tables

**Problem.** Live-load and footway-load details were previously combined or insufficiently differentiated.

**Implementation.** Chapter 3 now contains **Table 3.3: Vehicle Live Loads (LL)** and **Table 3.4: Footway / Footpath Live Load**. The vehicle table reports selected vehicle classes plus impact, braking and centrifugal parameters where available. The footway table presents its own loading method and magnitude. The vehicle list is taken from the data passed by the existing input/report workflow rather than hardcoded as one fixed traffic case.

**Observed result.** The supplied enhanced report lists Class A, Class 70R (Wheeled/Tracked/Bogie), Class AA (Wheeled/Tracked), Class SV and Class Fatigue in Table 3.3, and a footway load of **4.905 kN/m²** in Table 3.4. Centrifugal force is marked unavailable when not supplied. A separate GUI-input variation test would be needed to claim the dynamic selection has been validated for every vehicle combination.

### 4.4 Utilization-ratio visual summaries

**Problem.** A large number of demand/capacity checks were difficult to compare quickly using tables alone.

**Implementation.** `charts.py` reads the utilization values used for the design summary, rejects absent or nonnumeric values, and groups the checks by Steel Plate Girders, Concrete Deck Slab, Cross Bracing and End Diaphragms. Matplotlib creates one bar chart per available category. The dashed **red line at UR = 1.0** is a decision reference; bars exceeding 1.0 are differentiated from bars below the limit. The generated figures are inserted in Section 5.5 using LaTeX figure markup.

**Observed result.** Figures 5.1–5.4 appear in the enhanced PDF. Girder fatigue has **UR = 2.45**, shown above the limit. Other displayed example checks include cross-bracing compression **0.81**, deck cantilever overhang **0.92**, and end-diaphragm check **0.81**. The figures present existing report values; no design check is recalculated by the plotting module.

### 4.5 Material quantity charts with distinct units

**Problem.** Material quantities were only tabulated and incompatible units could be confusing if combined into one comparison graph.

**Implementation.** `charts.py` reads the quantity summary and produces separate plots for structural steel weight **(MT)**, concrete volume **(m³)** and reinforcement-steel weight **(MT)**. Values are read from the same report input dictionary used for Chapter 7. End-diaphragm steel is included only when a valid quantity is explicitly present under its expected key; otherwise the report adds an availability note. Generated PNG figures are embedded dynamically during report compilation.

**Observed result.** Figures 7.1–7.3 display the three material categories. In the supplied report, the girder steel total is **16.98 MT**, the deck concrete volume **70.65 m³**, and the reinforcement-steel total **8.48 MT**. End-diaphragm tonnage remains unavailable in this run; it has **not** been inferred from member dimensions.

### 4.6 Centralized configuration and consistent styling

**Problem.** Margins, headings, footer definitions and table spacing were scattered through the report generation logic.

**Implementation.** A shared `styles.py` contains the report-wide LaTeX preamble and constants used for plotting. The final page geometry uses A4 paper with **1 in left/right, 1.08 in top, 1.12 in bottom margins**, `headheight=28pt` and `footskip=32pt`. Header metadata is arranged in a two-line full-width block rather than packing project name, job number, date and revision into competing left/right header areas. Global table rules and coloring are defined centrally, while a few chapter-specific column widths remain local because their structures differ.

**Observed result.** The enhanced report consistently displays project identification, job/reference metadata, and page numbering. The visual output is less crowded in the header and no longer shows the original footer collision.

## 5. Additional Data-Integrity and Presentation Corrections

- **Unit conversion:** Chapter 2 now presents girder depth, web thickness and flange dimensions in millimetres. In the demonstration report, Table 2.7 shows **1340 mm**, **8 mm**, and **410 mm × 18 mm** flange dimensions.
- **Floating-point formatting:** the overall bridge width is displayed as **11.775 m** rather than a raw floating-point representation.
- **Outcome consistency:** the executive summary identifies the overall result as **FAIL** and reports the girder fatigue utilization ratio **2.45**, consistent with the Section 5 checks.
- **Analysis omissions:** Chapter 4 uses explicit text such as “results were not supplied for this report” instead of presenting blank analysis tables as computed evidence.
- **CAD availability:** Chapter 6 uses a compact “CAD image not exported in this run” notice for missing views. It does not imply that a CAD drawing was successfully exported when no image exists.

## 6. Validation and Evidence

### 6.1 Testing procedure

1. Establish the original report from OsdagBridge using the Design → Generate Report workflow and preserve it as `Report_Before.pdf`.
2. Apply report-generator changes on the dedicated Git feature branch.
3. Run Python syntax checks for the report package (`python -m compileall -q src/osdagbridge/core/reports`).
4. Run `git diff --check` to detect whitespace problems and correct identified issues.
5. Launch OsdagBridge through `python -m osdagbridge.desktop` in the `osdagbridge-env` Conda environment.
6. Generate a revised LaTeX source and PDF from the bridge design; examine chapter tables, pagination, figures, displayed results, and the table of contents.
7. Retain the final result as `Report_After.pdf` for side-by-side comparison.

### 6.2 Verified report observations

| Verification point | Evidence in inspected `REP.pdf` (PDF page numbering) | Result |
|---|---|---|
| Revised header and cover metadata | Pages 1–2 | Header arranged without the former crowded single-line metadata grouping |
| Correct girder dimensions | Page 8, Table 2.7 | 1340 mm depth, 8 mm web, 410 mm / 18 mm flanges |
| Vehicle and footway tables | Pages 12–13, Tables 3.3–3.4 | Separate tables |
| Missing analysis data handled honestly | Page 16, Chapter 4 | Explanatory notices and no fabricated maxima/reactions |
| Multi-page repeated headings | Pages 17–19, Table 5.1; pages 38–39, Table 5.29 | Repeated headings visible |
| Stiffener continuation | Pages 25–26, Table 5.7 | Continued caption and no G4 footer collision observed |
| Four utilization figures | Pages 40–41, Figures 5.1–5.4 | Four plots, UR = 1.0 reference |
| CAD asset fallback | Page 42, Chapter 6 | Missing exports disclosed |
| Material bill and three charts | Pages 43–45, Table 7.1 and Figures 7.1–7.3 | Distinct steel / concrete / reinforcement plots |

**Interpretation:** successful compilation and visual inspection demonstrate that the refactored workflow generates a readable report for this demonstration input. They do not independently validate bridge engineering calculations or prove that all possible GUI combinations and report configurations have been exercised.

## 7. Known Limitations / Future Work

1. **CAD exports:** the supplied run did not provide Chapter 6 image assets (and introductory bridge plan/cross-section/3D figures were also unavailable). The generator now handles missing assets clearly, but the upstream CAD-image export/integration remains to be completed or tested.
2. **Analysis result coverage:** Chapter 4 lacks maximum-demand, reaction and some deflection results in the supplied report payload. Rendering a descriptive availability note is not a substitute for connecting the corresponding solver results.
3. **End-diaphragm steel tonnage:** the current material take-off payload does not provide a verified total, so the steel chart omits this item. A future backend quantity calculation and payload mapping are necessary to fully satisfy this chart requirement.
4. **Remaining field gaps:** a few input/load fields in Chapter 2/3 and some individual design-check cells are blank or unavailable; these should be resolved at the data-source boundary rather than filled with assumptions.
5. **Automated regression coverage:** the tested output is a representative bridge run. Future work should add fixture-based report tests for long tables, empty/full datasets, alternate vehicle selections, variable girder counts, image availability and PDF visual regressions.
6. **Source architecture:** full conversion to structured PyLaTeX object APIs could be considered separately; this change set intentionally retains the existing LaTeX-string assembly system to limit regression risk.

## 8. Reproducibility

From the repository root on the documented Ubuntu/Conda setup:

```bash
conda activate osdagbridge-env
python -m compileall -q src/osdagbridge/core/reports
git diff --check
cd src
python -m osdagbridge.desktop
```

In the application, open the bridge design, run **Design**, select **Generate Report**, and produce the PDF using the report options. For a valid visual before/after comparison, the same bridge input configuration and report options should be used in both runs. Generated `.tex` files can be retained when troubleshooting pagination or LaTeX compilation errors.

## 9. Submission Artifacts

```text
screening_submission/
├── Report_Before.pdf
├── Report_After.pdf
└── Technical_Changes.md

src/osdagbridge/core/reports/
├── styles.py
├── table_layout.py
├── charts.py
├── report_generator.py
├── report_utils.py
├── executive_summary.py
├── chap2.py
├── chap3.py
├── chap4.py
├── chap5.py
├── chap6.py
└── chap7.py
```

The complete Git repository is the authoritative deliverable for the Python implementation. The PDFs demonstrate the generated output and this document provides a traceable record of changes and verification.

## 10. Conclusion

The screening task demonstrates a maintainable improvement to OsdagBridge's automated design-report workflow. Its principal outcomes are reliable continuation headings in many long tables, corrected pagination in problematic sections, clearer loading data, report-data-driven utilization and quantity charts, centralized page styling, and more transparent handling of missing backend assets. The supplied PDF shows the intended features working together while preserving the reported **failing** girder fatigue result. The remaining gaps—especially CAD export integration and end-diaphragm material quantity calculation—are explicitly disclosed so that formatting improvements are not confused with completed structural analysis or data generation.
