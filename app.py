import math
import io
import os
import base64
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__,
            template_folder=os.path.join(BASE_DIR, "templates"),
            static_folder=os.path.join(BASE_DIR, "static"))

# ─── Data Tables ──────────────────────────────────────────────────────────────

SAATGUT = [
    # (name, g_m2, kg_sac)
    ("—", None, None),
    ("430 (UFA) Trocken", 8, 10),
    ("431 (OH) Gras-Wiessklee", 8, 10),
    ("440 (OH) Gras-Weissklee", 8, 10),
    ("450 Humida Blumenwiese feucht", 8, 10),
    ("450 Salvia Blumenwiese trocken", 8, 10),
    ("481 Alpweide", 8, 10),
    ("OH Lento", 40, 10),
    ("OH Logro mit Klee", 30, 10),
    ("OH Piz Alpin", 15, 10),
    ("OH Pré Alpin", 25, 10),
    ("OH Schatten", 40, 10),
    ("OH Schotter", 25, 10),
    ("OH Sprint Turbo", 40, 10),
    ("OH Topsaat SUPRA (altitude)", 40, 10),
    ("OH Tabor Alexandriner", 5, 5),
    ("OH Top Alpin", 25, 10),
    ("OH-ch Swissflora", 10, 10),
    ("OH-ch Humiflora", 10, 10),
    ("OH-ch Miniflora", 20, 10),
    ("OH-ch Miniflora Myko", 20, 10),
    ("OH-ch Naturflora CH", 10, 10),
    ("OH-ch Schotterflora Myko", 20, 10),
    ("OH-ch Swissflora Myko", 20, 10),
    ("OH-ch Swissflora Myko // GE", 20, 10),
    ("OH-ch-Highway-Natur", 10, 10),
    ("OH-chg-Highway-Natur", 10, 10),
    ("OH-chg Swissflora // GE", 10, 10),
    ("OH-chg Humiflora", 10, 10),
    ("OH-chg Naturflora (Ersatz VSS Natur flach)", 10, 10),
    ("OH-chg-Wallis Trockenrasen Myko", 10, 10),
    ("OH-Highway / VSS A", 30, 10),
    ("OH-Montagna mit Saathelfer", 8, 10),
    ("OH-Rebberg", 10, 10),
    ("Roggentrespe", 2, 10),
    ("UFA Böschungsmischung humusiert CH", 10, 5),
    ("UFA Böschungsmischung trocken CH", 10, 5),
    ("UFA Flore Alpine CH", 10, 5),
    ("UFA Krautsaum (Ourlet) feucht CH-G", 4, 5),
    ("UFA Krautsaum (Ourlet) trocken CH-G", 4, 5),
    ("UFA Broma CH-G", 4, 5),
    ("UFA Remise en culture Gold", 5, 10),
    ("UFA Blumenrasen CH", 10, 5),
    ("UFA Blumenrasen CH-G", 10, 5),
    ("UFA Magerrasen CH-G (Rustic + fleurs)", 10, 5),
    ("UFA Rätia Eiger Alpin", 20, 10),
    ("UFA Rätia Eiger Hochalpin", 15, 10),
    ("UFA Ruderalflora CH", 10, 5),
    ("UFA Sedumsprossen CH (4 Sorten)", 10, 5),
    ("UFA Böschungsstabilisator artenreich", 1, 10),
    ("UFA Vertibord humusiert", 25, 10),
    ("UFA Vertibord trocken", 30, 10),
    ("UFA Wildblumenwiese CH", 10, 5),
    ("UFA Wildblumenwiese Original CH", 10, 5),
    ("UFA Wildblumenwiese orig. CH-G", 10, 5),
    ("UFA Wildblumenwiese orig. CH-i-G", 10, 5),
    ("UFA Bergblumenwiese CH-G", 10, 5),
    ("UFA Wildblumenwiese trocken CH-G", 10, 5),
    ("UFA Wildblumenwiese feucht CH-G", 10, 5),
    ("VSS Erosionsschutz ERO - OHS", 10, 10),
    ("VSS Minimal MIN - OHS", 10, 10),
    ("VSS Montan MON - OHS", 10, 10),
    ("VSS Natur Humusiert HUM - OHS", 10, 10),
    ("VSS Natur Rohboden ROH - OHS", 10, 10),
    ("VSS Pionier PIO - OHS", 10, 10),
    ("VSS Temporär TEM - OHS", 10, 10),
    ("UR3 - CH", 15, 10),
    ("Eurotec Soil Fix", 1.5, 10),
]

# Machine: eau_machine (L), capacity per erosion type (m²)
MACHINE_DATA = {
    "MAN FIX":   {"eau": 4500,  "SANS": 4500,  "AMU 1": 3000, "AMU 2": 1500, "AMECO": 450,   "PROTECT": 450},
    "MINI":      {"eau": 1050,  "SANS": 1050,  "AMU 1": 700,  "AMU 2": 350,  "AMECO": 80,    "PROTECT": 80},
    "MULI":      {"eau": 1500,  "SANS": 1500,  "AMU 1": 1000, "AMU 2": 500,  "AMECO": 110,   "PROTECT": 110},
    "A LA VOLEE":{"eau": 10000, "SANS": 10000, "AMU 1": 10000,"AMU 2": 10000,"AMECO": 10000, "PROTECT": 10000},
}

# Technique: g/m2 prescriptions for auxiliary products
TECHNIQUE_DATA = {
    "ASD":      {"mulch_hydrofibre": 20, "hydrogel": 20, "hydrorga_base": 0},
    "ASDC":     {"mulch_hydrofibre": 35, "hydrogel": 50, "hydrorga_base": 70},
    "Entretien":{"mulch_hydrofibre": 0,  "hydrogel": 0,  "hydrorga_base": 0},
}

# Erosion: g/m2 prescriptions
EROSION_DATA = {
    "SANS":    {"mulch_standard": 0,   "geotak": 7,  "verdyol": 0, "paille_longue": 0,   "protect_fibre": 0},
    "AMU 1":   {"mulch_standard": 80,  "geotak": 10, "verdyol": 0, "paille_longue": 0,   "protect_fibre": 0},
    "AMU 2":   {"mulch_standard": 0,   "geotak": 0,  "verdyol": 0, "paille_longue": 0,   "protect_fibre": 0},
    "AMECO":   {"mulch_standard": 0,   "geotak": 0,  "verdyol": 2, "paille_longue": 300, "protect_fibre": 0},
    "PROTECT": {"mulch_standard": 0,   "geotak": 0,  "verdyol": 0, "paille_longue": 0,   "protect_fibre": 390},
}

TECHNICIANS = [
    {"initials": "AC", "name": "Christophe Andres",  "phone": "079 555 45 25"},
    {"initials": "EC", "name": "Emilien Castella",   "phone": "079 333 65 85"},
    {"initials": "MM", "name": "Markus Müller",       "phone": "079 869 16 99"},
]

# ─── Calculation Helpers ──────────────────────────────────────────────────────

def roundup(v):
    return math.ceil(v) if v > 0 else 0

def mround(value, multiple):
    if value == 0 or multiple == 0:
        return 0
    return round(value / multiple) * multiple

def calc_row(supplier_g, kg_sac, used_g, m2_machine, machines):
    """Calculate one product row (mirrors Dispo columns B/C/D/K/L/M)."""
    if not supplier_g or not kg_sac or m2_machine == 0:
        return dict(supplier_g=supplier_g or 0, c=0, suggestion_g=0,
                    kg_sac=kg_sac or 0, k=0, total_sacs=0, total_kg=0)
    # C  = m2_machine * B / 1000 / kg_sac
    c = m2_machine * supplier_g / 1000 / kg_sac
    # D  = MROUND(C,0.5) * kg_sac / m2_machine * 1000
    suggestion_g = mround(c, 0.5) * kg_sac / m2_machine * 1000 if m2_machine else 0
    # K  = m2_machine * F / 1000 / kg_sac
    k = m2_machine * used_g / 1000 / kg_sac
    # L  = ROUNDUP(K * machines)
    total_sacs = roundup(k * machines)
    # M  = kg_sac * L
    total_kg = kg_sac * total_sacs
    return dict(
        supplier_g=round(supplier_g, 2),
        c=round(c, 3),
        suggestion_g=round(suggestion_g, 1),
        used_g=round(used_g, 2),
        kg_sac=kg_sac,
        k=round(k, 3),
        total_sacs=total_sacs,
        total_kg=round(total_kg, 1),
    )

def do_calculate(data):
    surface   = float(data.get("surface", 0) or 0)
    technique = data.get("technique", "ASD")
    erosion   = data.get("erosion", "SANS")
    seeder    = data.get("seeder", "MAN FIX")
    rincer    = bool(data.get("rincer", False))
    humus     = data.get("humus", "SANS")

    machine  = MACHINE_DATA.get(seeder, MACHINE_DATA["MAN FIX"])
    eau      = machine["eau"]
    max_m2   = machine.get(erosion, machine["SANS"])
    machines = roundup(surface / max_m2) if max_m2 > 0 and surface > 0 else 0
    m2_mach  = (surface / machines) if machines > 0 else 0

    tech = TECHNIQUE_DATA.get(technique, TECHNIQUE_DATA["ASD"])
    ero  = EROSION_DATA.get(erosion, EROSION_DATA["SANS"])

    # Mulch Hydrofibre: 0 when erosion=PROTECT
    mulch_h_g = tech["mulch_hydrofibre"] if erosion != "PROTECT" else 0
    # Hydrorga: 0 when humus=AVEC (Daten logic)
    hydrorga_g = tech["hydrorga_base"] if humus != "AVEC" else 0

    # Build overrideable products
    seeds = data.get("seeds", [])  # [{name, g_m2, kg_sac, used_g}, ...]
    seed_rows = []
    for s in seeds:
        if not s.get("name") or s["name"] == "—":
            continue
        sg  = float(s.get("g_m2") or 0)
        kps = float(s.get("kg_sac") or 0)
        ug  = float(s.get("used_g") or sg)
        if sg and kps:
            seed_rows.append({
                "name": s["name"],
                **calc_row(sg, kps, ug, m2_mach, machines),
            })

    # Fixed auxiliary products – used_g comes from form or defaults to supplier_g
    def aux(key, supplier_g, kg_sac, label):
        ug = float(data.get(f"used_g_{key}") or supplier_g or 0)
        r  = calc_row(supplier_g, kg_sac, ug, m2_mach, machines)
        return {"name": label, "key": key, **r}

    aux_rows = [
        aux("mulch_hydrofibre", mulch_h_g,           23,  "Mulch Hydrofibre (cellulose)"),
        aux("cellulose_hunn",   float(data.get("used_g_cellulose_hunn") or 0), 120, "Cellulose (Hunn)"),
        aux("hydrogel",         tech["hydrogel"],     25,  "Hydrogel (engrais de départ)"),
        aux("hydrorga",         hydrorga_g,           25,  "Hydrorga (engrais longue durée)"),
        aux("mulch_standard",   ero["mulch_standard"],25,  "Mulch standard (paille hachée)"),
        aux("verdyol",          ero["verdyol"],        15, "Verdyol Super (collant)"),
        aux("geotak",           ero["geotak"],         15, "Geotak (collant organique)"),
        aux("protect_fibre",    ero["protect_fibre"],  23, "Protect (fibre de bois)"),
        aux("paille_longue",    ero["paille_longue"],  15, "Paille longue"),
    ]
    # Gartenhumus-Substrat only when humus=SUBSTRAT
    if humus == "SUBSTRAT":
        substrat_g = float(data.get("used_g_substrat") or 10)
        aux_rows.append({
            "name": "Gartenhumus - Substrat",
            "key": "substrat",
            **calc_row(substrat_g, 30, substrat_g, m2_mach, machines),
        })

    return {
        "eau_machine": eau,
        "max_m2": max_m2,
        "machines": machines,
        "m2_machine": round(m2_mach, 1),
        "seed_rows": seed_rows,
        "aux_rows": aux_rows,
    }

# ─── Routes ──────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template(
        "index.html",
        saatgut=SAATGUT,
        machine_keys=list(MACHINE_DATA.keys()),
        technicians=TECHNICIANS,
        today=datetime.today().strftime("%Y-%m-%d"),
    )

@app.route("/calculate", methods=["POST"])
def calculate():
    return jsonify(do_calculate(request.get_json()))

@app.route("/generate-pdf", methods=["POST"])
def generate_pdf():
    data = request.get_json()
    pdf_buf = create_dispo_pdf(data)
    proj = (data.get("projet_no") or "dispo").replace(" ", "_")
    return send_file(
        pdf_buf,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"Dispo_{proj}.pdf",
    )

# ─── PDF Generation ──────────────────────────────────────────────────────────

def create_dispo_pdf(data):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm, mm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, HRFlowable
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=1.5*cm, rightMargin=1.5*cm,
        topMargin=1.5*cm, bottomMargin=1.5*cm,
    )

    styles = getSampleStyleSheet()
    GREEN  = colors.HexColor("#1a6b1a")
    LGREY  = colors.HexColor("#f2f2f2")
    DGREY  = colors.HexColor("#555555")

    h1 = ParagraphStyle("h1", fontSize=13, fontName="Helvetica-Bold", textColor=GREEN, spaceAfter=4)
    h2 = ParagraphStyle("h2", fontSize=9,  fontName="Helvetica-Bold", textColor=GREEN, spaceAfter=2)
    normal = ParagraphStyle("normal", fontSize=8, fontName="Helvetica", spaceAfter=1)
    small  = ParagraphStyle("small",  fontSize=7, fontName="Helvetica", textColor=DGREY)

    story = []

    # ── Logo + Title ──────────────────────────────────────────────────────────
    logo_path = os.path.join(os.path.dirname(__file__), "static", "logo.png")
    logo_img  = Image(logo_path, width=6*cm, height=0.9*cm) if os.path.exists(logo_path) else Paragraph("Begrünungen Hunn", h1)

    header_data = [[
        Paragraph("<b>DISPOSITION</b>", ParagraphStyle("tit", fontSize=15, fontName="Helvetica-Bold", textColor=GREEN)),
        "",
        logo_img,
    ]]
    header_tbl = Table(header_data, colWidths=[7*cm, 2*cm, 7*cm])
    header_tbl.setStyle(TableStyle([
        ("ALIGN", (2,0), (2,0), "RIGHT"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ]))
    story.append(header_tbl)
    story.append(HRFlowable(width="100%", thickness=2, color=GREEN, spaceAfter=6))

    # ── Project Info ─────────────────────────────────────────────────────────
    proj_data = [
        [Paragraph("<b>Projet N°:</b>", normal), Paragraph(str(data.get("projet_no","") or ""), normal),
         Paragraph("<b>Date prévue:</b>", normal), Paragraph(str(data.get("date_prevue","") or ""), normal)],
        [Paragraph("<b>Chantier:</b>", normal), Paragraph(str(data.get("chantier","") or ""), normal),
         Paragraph("<b>Technicien:</b>", normal), Paragraph(str(data.get("technicien","") or ""), normal)],
        [Paragraph("<b>Contact:</b>", normal), Paragraph(str(data.get("contact","") or ""), normal),
         Paragraph("<b>Entreprise:</b>", normal), Paragraph(str(data.get("entreprise","") or ""), normal)],
        [Paragraph("<b>Téléphone:</b>", normal), Paragraph(str(data.get("telephone","") or ""), normal),
         Paragraph("<b>Remarque:</b>", normal), Paragraph(str(data.get("remarque","") or ""), normal)],
    ]
    proj_tbl = Table(proj_data, colWidths=[3*cm, 6.5*cm, 2.5*cm, 6.5*cm])
    proj_tbl.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 0.3, colors.lightgrey),
        ("BACKGROUND", (0,0), (0,-1), LGREY),
        ("BACKGROUND", (2,0), (2,-1), LGREY),
        ("FONTSIZE", (0,0), (-1,-1), 8),
        ("TOPPADDING", (0,0), (-1,-1), 3),
        ("BOTTOMPADDING", (0,0), (-1,-1), 3),
    ]))
    story.append(proj_tbl)
    story.append(Spacer(1, 8))

    # ── Machine Config ────────────────────────────────────────────────────────
    calc = do_calculate(data)
    story.append(Paragraph("Configuration machine", h2))

    cfg_data = [
        ["Surface", f"{data.get('surface','')} m²",
         "Technique", data.get("technique",""),
         "Erosion", data.get("erosion","")],
        ["Seeder", data.get("seeder",""),
         "Rincer", "Oui" if data.get("rincer") else "Non",
         "Humus/Sub.", data.get("humus","")],
        ["Géotextile", data.get("geotextile","—"),
         "Nb. machines", str(calc["machines"]),
         "m²/machine", f"{calc['m2_machine']} m²"],
        ["Eau/machine", f"{calc['eau_machine']} L",
         "Max m²/machine", f"{calc['max_m2']} m²",
         "", ""],
    ]
    cfg_tbl = Table(cfg_data, colWidths=[2.5*cm, 3*cm, 2.5*cm, 3*cm, 2.5*cm, 5*cm])
    cfg_tbl.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 0.3, colors.lightgrey),
        ("BACKGROUND", (0,0), (0,-1), LGREY),
        ("BACKGROUND", (2,0), (2,-1), LGREY),
        ("BACKGROUND", (4,0), (4,-1), LGREY),
        ("FONTSIZE", (0,0), (-1,-1), 8),
        ("TOPPADDING", (0,0), (-1,-1), 3),
        ("BOTTOMPADDING", (0,0), (-1,-1), 3),
    ]))
    story.append(cfg_tbl)
    story.append(Spacer(1, 8))

    # ── Products Table ────────────────────────────────────────────────────────
    story.append(Paragraph("Matériaux / Produits", h2))

    col_hdrs = ["Produit", "g/m²\nFournisseur", "g/m²\nUtilisé", "kg/sac", "Sac/machine", "Total sacs", "Total kg"]
    tbl_data  = [col_hdrs]

    all_rows = calc["seed_rows"] + [r for r in calc["aux_rows"] if r.get("supplier_g") or r.get("used_g")]

    total_sacs_sum = 0
    total_kg_sum   = 0

    for r in all_rows:
        if not r.get("total_sacs") and not r.get("used_g"):
            continue
        tbl_data.append([
            r["name"],
            str(r.get("supplier_g", "")),
            str(r.get("used_g", "")),
            str(r.get("kg_sac", "")),
            f"{r.get('k', 0):.2f}",
            str(r.get("total_sacs", "")),
            str(r.get("total_kg", "")),
        ])
        total_sacs_sum += r.get("total_sacs", 0) or 0
        total_kg_sum   += r.get("total_kg", 0) or 0

    # Total row
    tbl_data.append(["TOTAL", "", "", "", "", str(total_sacs_sum), f"{total_kg_sum:.1f}"])

    col_w = [6.5*cm, 2*cm, 2*cm, 1.5*cm, 2*cm, 2*cm, 2.5*cm]
    prod_tbl = Table(tbl_data, colWidths=col_w, repeatRows=1)
    n = len(tbl_data)
    prod_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), GREEN),
        ("TEXTCOLOR",  (0,0), (-1,0), colors.white),
        ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",   (0,0), (-1,-1), 8),
        ("ALIGN",      (1,0), (-1,-1), "CENTER"),
        ("GRID",       (0,0), (-1,-1), 0.3, colors.lightgrey),
        ("ROWBACKGROUNDS", (0,1), (-1, n-2), [colors.white, LGREY]),
        ("BACKGROUND", (0,n-1), (-1,n-1), colors.HexColor("#d4edda")),
        ("FONTNAME",   (0,n-1), (-1,n-1), "Helvetica-Bold"),
        ("TOPPADDING", (0,0), (-1,-1), 3),
        ("BOTTOMPADDING",(0,0),(-1,-1), 3),
    ]))
    story.append(prod_tbl)
    story.append(Spacer(1, 10))

    # ── Accessories ───────────────────────────────────────────────────────────
    nattes = data.get("nattes", {})
    crochets = data.get("crochets", {})
    hpq = data.get("hpq", {})
    divers = data.get("divers", "")

    acc_items = [(k, v) for k, v in {**nattes, **crochets, **hpq}.items() if v]
    if acc_items or divers:
        story.append(Paragraph("Nattes / Crochets / Divers", h2))
        acc_data = [[Paragraph("<b>Article</b>", normal), Paragraph("<b>Quantité</b>", normal)]]
        for k, v in acc_items:
            acc_data.append([k, str(v)])
        if divers:
            acc_data.append(["Divers", divers])
        acc_tbl = Table(acc_data, colWidths=[8*cm, 10.5*cm])
        acc_tbl.setStyle(TableStyle([
            ("GRID", (0,0), (-1,-1), 0.3, colors.lightgrey),
            ("BACKGROUND", (0,0), (-1,0), LGREY),
            ("FONTSIZE", (0,0), (-1,-1), 8),
            ("TOPPADDING",(0,0),(-1,-1), 3),
            ("BOTTOMPADDING",(0,0),(-1,-1), 3),
        ]))
        story.append(acc_tbl)
        story.append(Spacer(1, 8))

    # ── Site Info ─────────────────────────────────────────────────────────────
    site_items = [
        ("Hydrante N°", data.get("hydrante", "")),
        ("Pomper", data.get("pomper", "")),
        ("Accès", data.get("acces", "")),
        ("Tuyaux", data.get("tuyaux", "")),
        ("Responsable", data.get("responsable", "")),
    ]
    if any(v for _, v in site_items):
        story.append(Paragraph("Informations chantier", h2))
        site_data = [[Paragraph(f"<b>{k}:</b>", normal), Paragraph(str(v or ""), normal)] for k, v in site_items if v]
        site_tbl = Table(site_data, colWidths=[4*cm, 14.5*cm])
        site_tbl.setStyle(TableStyle([
            ("GRID", (0,0), (-1,-1), 0.3, colors.lightgrey),
            ("BACKGROUND", (0,0), (0,-1), LGREY),
            ("FONTSIZE", (0,0), (-1,-1), 8),
            ("TOPPADDING",(0,0),(-1,-1), 3),
            ("BOTTOMPADDING",(0,0),(-1,-1), 3),
        ]))
        story.append(site_tbl)
        story.append(Spacer(1, 8))

    # ── Rapport chantier ──────────────────────────────────────────────────────
    rapport = data.get("rapport", [])
    if rapport:
        story.append(Paragraph("Rapport chantier", h2))
        names = data.get("rapport_names", ["", "", "", ""])
        rpt_hdrs = ["Date", "Travail (h)", "Trajet (h)", "Régie (h)"] + names[:4]
        rpt_data = [rpt_hdrs]
        for row in rapport:
            rpt_data.append([
                row.get("date",""), row.get("travail",""), row.get("trajet",""), row.get("regie",""),
                row.get("n1",""), row.get("n2",""), row.get("n3",""), row.get("n4",""),
            ])
        rpt_tbl = Table(rpt_data, colWidths=[2.5*cm]*8)
        rpt_tbl.setStyle(TableStyle([
            ("GRID", (0,0), (-1,-1), 0.3, colors.lightgrey),
            ("BACKGROUND", (0,0), (-1,0), LGREY),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,-1), 8),
            ("TOPPADDING",(0,0),(-1,-1), 3),
            ("BOTTOMPADDING",(0,0),(-1,-1), 3),
        ]))
        story.append(rpt_tbl)
        story.append(Spacer(1, 8))

    # ── Vehicles ──────────────────────────────────────────────────────────────
    vehicles = data.get("vehicles", {})
    if any(vehicles.values()):
        story.append(Paragraph("Véhicules / Machines / Seeder", h2))
        veh_items = [(k, v) for k, v in vehicles.items() if v]
        veh_data  = [["Véhicule/Machine", "Heures"]]
        for k, v in veh_items:
            veh_data.append([k, str(v)])
        veh_tbl = Table(veh_data, colWidths=[10*cm, 8.5*cm])
        veh_tbl.setStyle(TableStyle([
            ("GRID", (0,0), (-1,-1), 0.3, colors.lightgrey),
            ("BACKGROUND", (0,0), (-1,0), LGREY),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,-1), 8),
            ("TOPPADDING",(0,0),(-1,-1), 3),
            ("BOTTOMPADDING",(0,0),(-1,-1), 3),
        ]))
        story.append(veh_tbl)
        story.append(Spacer(1, 8))

    # ── Signatures ────────────────────────────────────────────────────────────
    story.append(Spacer(1, 10))
    sig_data = [
        ["Date + Visa Conseiller:", "", "Date + Visa EC:", ""],
        ["", "", "", ""],
    ]
    sig_tbl = Table(sig_data, colWidths=[4*cm, 6*cm, 4*cm, 4.5*cm])
    sig_tbl.setStyle(TableStyle([
        ("LINEBELOW", (1,1), (1,1), 1, colors.black),
        ("LINEBELOW", (3,1), (3,1), 1, colors.black),
        ("FONTSIZE", (0,0), (-1,-1), 8),
    ]))
    story.append(sig_tbl)

    # ── Footer ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=0.5, color=GREEN))
    story.append(Paragraph(
        f"<font size='6' color='grey'>Begrünungen Hunn  —  généré le {datetime.today().strftime('%d.%m.%Y')}</font>",
        ParagraphStyle("footer", alignment=TA_CENTER)
    ))

    doc.build(story)
    buf.seek(0)
    return buf

# ─── Entry point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
