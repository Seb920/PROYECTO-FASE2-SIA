"""
Genera el informe PDF del proyecto Predicción de Precios de Viviendas.
Requiere que Flask esté corriendo en http://127.0.0.1:5000
"""
import urllib.request
import json
import base64
import io
import os
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, Image, KeepTogether, PageBreak
)
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily

# ─── Fuentes TTF ─────────────────────────────────────────────────────────────
_I = "/tmp/inter_fonts/extras/ttf"
_M = "/usr/share/fonts/Adwaita"

for _name, _path in {
    "Inter":          f"{_I}/Inter-Regular.ttf",
    "Inter-Medium":   f"{_I}/Inter-Medium.ttf",
    "Inter-SemiBold": f"{_I}/Inter-SemiBold.ttf",
    "Inter-Bold":     f"{_I}/Inter-Bold.ttf",
    "Inter-Italic":   f"{_I}/Inter-Italic.ttf",
    "Inter-BoldIta":  f"{_I}/Inter-BoldItalic.ttf",
    "Inter-Light":    f"{_I}/Inter-Light.ttf",
    "Mono":           f"{_M}/AdwaitaMono-Regular.ttf",
    "Mono-Bold":      f"{_M}/AdwaitaMono-Bold.ttf",
}.items():
    pdfmetrics.registerFont(TTFont(_name, _path))

registerFontFamily("Inter",
    normal="Inter", bold="Inter-SemiBold",
    italic="Inter-Italic", boldItalic="Inter-BoldIta")

# ─── Colores ──────────────────────────────────────────────────────────────────
DARK_BG = colors.HexColor("#0a0f1e")
SURFACE = colors.HexColor("#111827")
CARD    = colors.HexColor("#1a2235")
BORDER  = colors.HexColor("#1e2d45")
ACCENT  = colors.HexColor("#00e5ff")
ACCENT2 = colors.HexColor("#7c3aed")
GREEN   = colors.HexColor("#10b981")
YELLOW  = colors.HexColor("#f59e0b")
RED     = colors.HexColor("#ef4444")
TEXT    = colors.HexColor("#e2e8f0")
MUTED   = colors.HexColor("#64748b")

BASE_URL = "http://127.0.0.1:5000"

# ─── HTTP helpers ─────────────────────────────────────────────────────────────
def fetch_json(path):
    with urllib.request.urlopen(BASE_URL + path, timeout=120) as r:
        return json.loads(r.read())

def fetch_post_json(path, payload):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        BASE_URL + path, data=data,
        headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())

def b64_to_image(b64str, w_cm, h_ratio=0.38):
    buf = io.BytesIO(base64.b64decode(b64str))
    img = Image(buf)
    img.drawWidth  = w_cm * cm
    img.drawHeight = w_cm * h_ratio * cm
    return img

def fmt_usd(v):
    return f"${v:,.0f}"

# ─── Estilos ─────────────────────────────────────────────────────────────────
def make_styles(W):
    base = getSampleStyleSheet()

    cover_title = ParagraphStyle("cover_title",
        fontSize=28, leading=34, textColor=colors.white,
        fontName="Inter-Medium",                        # ← bajado de Bold
        alignment=TA_CENTER, spaceAfter=6)

    cover_sub = ParagraphStyle("cover_sub",
        fontSize=13, leading=17, textColor=ACCENT,
        fontName="Inter",                               # ← bajado de SemiBold
        alignment=TA_CENTER, spaceAfter=4)

    section = ParagraphStyle("section",
        fontSize=16, leading=21, textColor=ACCENT,
        fontName="Inter-Medium",                        # ← bajado de SemiBold
        spaceBefore=16, spaceAfter=7)

    subsection = ParagraphStyle("subsection",
        fontSize=11, leading=15, textColor=TEXT,
        fontName="Inter-Medium",                        # ← bajado de SemiBold
        spaceBefore=10, spaceAfter=5)

    body = ParagraphStyle("body",
        fontSize=10, leading=16, textColor=TEXT,
        fontName="Inter",
        alignment=TA_JUSTIFY, spaceAfter=6)

    body_center = ParagraphStyle("body_center",
        fontSize=10, leading=16, textColor=TEXT,
        fontName="Inter", alignment=TA_CENTER, spaceAfter=6)

    caption = ParagraphStyle("caption",
        fontSize=8, leading=12, textColor=MUTED,
        fontName="Inter-Italic", alignment=TA_CENTER, spaceAfter=4)

    return dict(cover_title=cover_title, cover_sub=cover_sub,
                section=section, subsection=subsection,
                body=body, body_center=body_center, caption=caption)

# ─── Estilo base para tablas ─────────────────────────────────────────────────
def base_table_style(header_bg=None):
    return TableStyle([
        ("BACKGROUND",    (0,0), (-1,0),  header_bg or SURFACE),
        ("BACKGROUND",    (0,1), (-1,-1), CARD),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [CARD, SURFACE]),
        ("TEXTCOLOR",     (0,0), (-1,0),  MUTED),
        ("TEXTCOLOR",     (0,1), (-1,-1), TEXT),
        ("FONTNAME",      (0,0), (-1,0),  "Inter"),      # header: regular
        ("FONTSIZE",      (0,0), (-1,0),  8),
        ("FONTNAME",      (0,1), (-1,-1), "Inter"),      # ← bajado de Bold
        ("FONTSIZE",      (0,1), (-1,-1), 10),
        ("ALIGN",         (0,0), (-1,-1), "LEFT"),
        ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ("GRID",          (0,0), (-1,-1), 0.4, BORDER),
        ("TOPPADDING",    (0,0), (-1,-1), 7),
        ("BOTTOMPADDING", (0,0), (-1,-1), 7),
        ("LEFTPADDING",   (0,0), (-1,-1), 9),
    ])

# ─── Callback de página ───────────────────────────────────────────────────────
def on_page(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(DARK_BG)
    canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
    canvas.setFillColor(ACCENT)
    canvas.rect(0, A4[1]-3, A4[0], 3, fill=1, stroke=0)
    if doc.page > 1:
        canvas.setFillColor(MUTED)
        canvas.setFont("Inter", 7)
        canvas.drawString(2*cm, 1.2*cm, "Predicción de Precios de Viviendas · SIA Fase 2")
        canvas.drawRightString(A4[0]-2*cm, 1.2*cm, f"Pág. {doc.page}")
        canvas.setFillColor(BORDER)
        canvas.rect(2*cm, 1.5*cm, A4[0]-4*cm, 0.3, fill=1, stroke=0)
    canvas.restoreState()

# ─── Main ─────────────────────────────────────────────────────────────────────
def generar_pdf():
    out = os.path.join(os.path.dirname(__file__), "Informe_Prediccion_Viviendas.pdf")
    doc = SimpleDocTemplate(out, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm)

    W  = A4[0] - 4*cm
    S  = make_styles(W)
    st = []

    def hr(color=BORDER, thick=0.5):
        return HRFlowable(width="100%", thickness=thick, color=color,
                          spaceAfter=6, spaceBefore=4)

    # ── PORTADA ───────────────────────────────────────────────────────────────
    st.append(Spacer(1, 3*cm))
    st.append(Paragraph("PREDICCIÓN DE PRECIOS", S["cover_title"]))
    st.append(Paragraph("DE VIVIENDAS", S["cover_title"]))
    st.append(Spacer(1, 0.4*cm))
    st.append(Paragraph("Sistema de Información · Fase 2", S["cover_sub"]))
    st.append(Spacer(1, 1.2*cm))

    info = [
        ["Tema",        "Predicción de Precios de Viviendas"],
        ["Tipo",        "Aprendizaje Supervisado — Regresión"],
        ["Algoritmos",  "Regresión Lineal · KNN · SVM · Árbol de Decisión"],
        ["Dataset",     "boston_housing_esp.csv (1,728 registros)"],
        ["Tecnologías", "Python 3 · Flask · scikit-learn · matplotlib"],
        ["Fecha",       datetime.today().strftime("%d de %B de %Y")],
    ]
    t = Table(info, colWidths=[4.5*cm, W-4.5*cm])
    t.setStyle(base_table_style())
    t.setStyle(TableStyle([
        ("ALIGN",       (0,0), (0,-1), "RIGHT"),
        ("TEXTCOLOR",   (0,0), (0,-1), MUTED),
        ("FONTNAME",    (0,0), (0,-1), "Inter"),
        ("FONTNAME",    (1,0), (1,-1), "Inter-Medium"),  # ← Medium en lugar de Bold
        ("FONTSIZE",    (0,0), (-1,-1), 10),
    ]))
    st.append(t)
    st.append(Spacer(1, 1.5*cm))
    st.append(Paragraph(
        "Repositorio: <font color='#00e5ff'>github.com/Rodrigoss06/PROYECTO-FASE2-SIA</font>",
        S["body_center"]))
    st.append(PageBreak())

    # ── 1. DESCRIPCIÓN ────────────────────────────────────────────────────────
    st.append(Paragraph("1. Descripción del Proyecto", S["section"]))
    st.append(hr())
    st.append(Paragraph(
        "El proyecto implementa un <b>Sistema de Información con aprendizaje supervisado</b> "
        "para predecir el precio de viviendas residenciales. Se aplican cuatro algoritmos de "
        "regresión sobre un dataset de propiedades inmobiliarias, comparando su rendimiento "
        "mediante métricas estándar (R², RMSE, MAE) y exponiendo los resultados a través de "
        "una interfaz web interactiva desarrollada con Flask.", S["body"]))
    st.append(Paragraph(
        "El usuario puede: (a) ejecutar cada algoritmo individualmente y visualizar métricas y "
        "gráficos, (b) comparar los cuatro modelos simultáneamente, y (c) ingresar los datos "
        "de una propiedad concreta mediante un formulario validado para obtener el precio "
        "estimado de todos los modelos.", S["body"]))

    st.append(Paragraph("1.1 Dataset", S["subsection"]))
    print("  Obteniendo info del dataset…")
    ds = fetch_json("/api/dataset_info")
    ds_rows = [
        ["Campo", "Valor"],
        ["Archivo",           "boston_housing_esp.csv"],
        ["Registros",         f"{ds['registros']:,}"],
        ["Características",   str(ds['caracteristicas'])],
        ["Variable objetivo", "precio (USD)"],
        ["Precio mínimo",     fmt_usd(ds['precio_min'])],
        ["Precio máximo",     fmt_usd(ds['precio_max'])],
        ["Precio promedio",   fmt_usd(ds['precio_promedio'])],
    ]
    t = Table(ds_rows, colWidths=[5*cm, W-5*cm])
    t.setStyle(base_table_style())
    st.append(t)
    st.append(Spacer(1, 0.3*cm))
    st.append(Paragraph(
        "Las 15 características incluyen variables numéricas (metros habitables, antigüedad, "
        "precio del terreno, dormitorios, baños, chimeneas, habitaciones totales, porcentaje "
        "de universitarios en la zona) y variables categóricas codificadas (tipo de calefacción, "
        "combustible, sistema de desagüe, vistas al lago, nueva construcción, aire acondicionado).",
        S["body"]))

    # ── 2. ARQUITECTURA ───────────────────────────────────────────────────────
    st.append(Paragraph("2. Arquitectura del Sistema", S["section"]))
    st.append(hr())
    st.append(Paragraph(
        "El sistema sigue una arquitectura cliente-servidor de tres capas:", S["body"]))

    arq = [
        ["Capa", "Tecnología", "Responsabilidad"],
        ["Presentación",      "HTML5 + CSS3 + JS",       "Interfaz web, formularios, validación front-end"],
        ["Lógica de negocio", "Python 3 · Flask",         "Endpoints REST, validación back-end, ML"],
        ["Datos",             "CSV + scikit-learn",        "Dataset, preprocesamiento, modelos en memoria"],
    ]
    t = Table(arq, colWidths=[3.5*cm, 4.5*cm, W-8*cm])
    t.setStyle(base_table_style())
    st.append(t)
    st.append(Spacer(1, 0.3*cm))

    st.append(Paragraph("Endpoints REST implementados:", S["subsection"]))
    eps = [
        ["Método", "Ruta", "Descripción"],
        ["GET",  "/api/regresion_lineal", "Métricas + gráficos de Regresión Lineal"],
        ["GET",  "/api/knn",              "Métricas + gráficos de KNN (k=5)"],
        ["GET",  "/api/svm",              "Métricas + gráficos de SVM (kernel RBF)"],
        ["GET",  "/api/arbol",            "Métricas + gráficos de Árbol de Decisión"],
        ["GET",  "/api/comparacion",      "Tabla comparativa de los 4 algoritmos"],
        ["POST", "/api/predecir",         "Predicción interactiva con datos de usuario"],
        ["GET",  "/api/dataset_info",     "Estadísticas del dataset"],
    ]
    t = Table(eps, colWidths=[1.5*cm, 5*cm, W-6.5*cm])
    t.setStyle(base_table_style())
    t.setStyle(TableStyle([
        ("TEXTCOLOR", (0,1), (0,-1), ACCENT),
        ("TEXTCOLOR", (1,1), (1,-1), YELLOW),
        ("FONTNAME",  (0,1), (-1,-1), "Mono"),
        ("FONTSIZE",  (0,1), (-1,-1), 8),
    ]))
    st.append(t)

    # ── 3. ALGORITMOS ─────────────────────────────────────────────────────────
    st.append(PageBreak())
    st.append(Paragraph("3. Algoritmos de Machine Learning", S["section"]))
    st.append(hr())

    algos = [
        ("Regresión Lineal", "regresion_lineal",
         "Modelo paramétrico que ajusta un hiperplano minimizando el error cuadrático medio (OLS). "
         "Asume linealidad entre características y precio. Rápido, interpretable y útil como línea base. "
         "Se aplica StandardScaler antes del ajuste para normalizar las magnitudes."),
        ("K-Nearest Neighbors (k=5)", "knn",
         "Algoritmo no paramétrico que predice el precio promediando los k=5 vecinos más similares "
         "en el espacio de características normalizado. No genera un modelo explícito: almacena todos "
         "los datos de entrenamiento."),
        ("Support Vector Machine (RBF)", "svm",
         "Busca el hiperplano que mejor se ajusta a los datos con un margen de tolerancia ε, "
         "usando el kernel RBF para capturar relaciones no lineales. Parámetros: C=100, γ=auto. "
         "Requiere escalado estricto de las características."),
        ("Árbol de Decisión (max_depth=10)", "arbol",
         "Construye un árbol binario de reglas de decisión basadas en umbrales de características. "
         "No requiere escalado. Altamente interpretable: cada nodo representa una regla sobre "
         "una característica. max_depth=10 controla el sobreajuste."),
    ]

    print("  Ejecutando los 4 algoritmos…")
    for idx, (nombre, endpoint, desc) in enumerate(algos, 1):
        print(f"    → {nombre}…", end=" ", flush=True)
        data = fetch_json(f"/api/{endpoint}")
        print(f"R²={data['r2']}%")

        st.append(KeepTogether([
            Paragraph(f"3.{idx} {nombre}", S["subsection"]),
            Paragraph(desc, S["body"]),
        ]))

        m_rows = [
            ["R² Score", "RMSE", "MAE"],
            [f"{data['r2']}%", fmt_usd(data['rmse']), fmt_usd(data['mae'])],
        ]
        t = Table(m_rows, colWidths=[W/3]*3)
        t.setStyle(base_table_style())
        r2_color = GREEN if data['r2'] >= 70 else (YELLOW if data['r2'] >= 50 else RED)
        t.setStyle(TableStyle([
            ("ALIGN",     (0,0), (-1,-1), "CENTER"),
            ("TEXTCOLOR", (0,1), (0,1),   r2_color),
            ("FONTNAME",  (0,1), (-1,-1), "Inter-Medium"),  # ← Medium para valores
            ("FONTSIZE",  (0,1), (-1,-1), 13),
        ]))
        st.append(t)
        st.append(Spacer(1, 0.2*cm))

        if data.get("metrics_chart"):
            st.append(b64_to_image(data["metrics_chart"], W/cm, 0.38))
            st.append(Paragraph(f"Figura: Métricas de rendimiento — {nombre}", S["caption"]))

        if data.get("prediction_chart"):
            st.append(b64_to_image(data["prediction_chart"], W/cm, 0.38))
            st.append(Paragraph("Figura: Predicciones vs Valores Reales / Distribución de Errores", S["caption"]))

        if data.get("regression_chart"):
            ratio = 0.55 if endpoint == "arbol" else 0.38
            st.append(b64_to_image(data["regression_chart"], W/cm, ratio))
            st.append(Paragraph(
                "Figura: Estructura del Árbol de Decisión e importancia de características"
                if endpoint == "arbol" else
                "Figura: Ajuste del modelo y correlación de características",
                S["caption"]))

        st.append(Spacer(1, 0.4*cm))

    # ── 4. COMPARACIÓN ────────────────────────────────────────────────────────
    st.append(PageBreak())
    st.append(Paragraph("4. Comparación de Algoritmos", S["section"]))
    st.append(hr())

    print("  Obteniendo comparación…")
    comp = fetch_json("/api/comparacion")

    escalado = {"Regresión Lineal": "Sí", "KNN (k=5)": "Sí",
                "SVM (RBF)": "Sí", "Árbol Decisión": "No"}
    comp_rows = [["Algoritmo", "R² Score", "RMSE", "MAE", "Escalado"]]
    for d in comp:
        comp_rows.append([d["nombre"], f"{d['r2']}%",
                          fmt_usd(d["rmse"]), fmt_usd(d["mae"]),
                          escalado.get(d["nombre"], "—")])

    t = Table(comp_rows, colWidths=[4.5*cm, 2.2*cm, 3*cm, 3*cm, 1.8*cm])
    t.setStyle(base_table_style())
    t.setStyle(TableStyle([("ALIGN", (1,0), (-1,-1), "CENTER")]))
    for i, d in enumerate(comp, 1):
        col = GREEN if d["r2"] >= 70 else (YELLOW if d["r2"] >= 50 else RED)
        t.setStyle(TableStyle([
            ("TEXTCOLOR", (1,i), (1,i), col),
            ("FONTNAME",  (1,i), (1,i), "Inter-Medium"),
        ]))
    st.append(t)
    st.append(Spacer(1, 0.3*cm))

    mejor = max(comp, key=lambda d: d["r2"])
    st.append(Paragraph(
        f"El algoritmo con mayor R² es <b>{mejor['nombre']}</b> ({mejor['r2']}%). "
        "La Regresión Lineal supera ligeramente a KNN en este dataset, ambos en torno al 58–60%. "
        "El SVM con parámetros actuales muestra bajo rendimiento; con grid search sobre C y γ "
        "podría mejorar. El Árbol de Decisión es el más interpretable aunque con R² menor.",
        S["body"]))

    drawing = Drawing(W, 120)
    bc = VerticalBarChart()
    bc.x = 40; bc.y = 20; bc.width = W - 80; bc.height = 85
    bc.data = [[d["r2"] for d in comp]]
    bc.categoryAxis.categoryNames = [d["nombre"] for d in comp]
    bc.bars[0].fillColor = ACCENT
    bc.valueAxis.valueMin = 0
    bc.valueAxis.valueMax = 100
    bc.valueAxis.valueStep = 20
    bc.valueAxis.labels.fontName = "Inter"
    bc.valueAxis.labels.fontSize = 8
    bc.valueAxis.labels.fillColor = MUTED
    bc.categoryAxis.labels.fontName = "Inter"
    bc.categoryAxis.labels.fontSize = 8
    bc.categoryAxis.labels.fillColor = MUTED
    drawing.add(bc)
    st.append(drawing)
    st.append(Paragraph("Figura: Comparación R² Score (%) entre los 4 algoritmos", S["caption"]))

    # ── 5. PREDICCIÓN INTERACTIVA ─────────────────────────────────────────────
    st.append(Paragraph("5. Predicción Interactiva (Caso de Uso)", S["section"]))
    st.append(hr())
    st.append(Paragraph(
        "Se ejecutó una predicción de ejemplo a través del endpoint "
        "<font color='#f59e0b'>POST /api/predecir</font> "
        "con los siguientes datos de una propiedad tipo:", S["body"]))

    input_rows = [
        ["Característica", "Valor", "Característica", "Valor"],
        ["Metros habitables", "1,800 sq ft",     "Dormitorios",        "3"],
        ["Metros totales",    "0.5 acres",        "Habitaciones",       "7"],
        ["Precio terreno",    "$60,000",           "Baños",              "2"],
        ["Antigüedad",        "15 años",           "Chimeneas",          "1"],
        ["Universitarios",    "50%",               "Aire acondicionado", "No"],
        ["Calefacción",       "Agua/vapor",        "Nueva construcción",  "No"],
        ["Combustible",       "Gas",               "Desagüe",            "Público"],
    ]
    t = Table(input_rows, colWidths=[3.5*cm]*4)
    t.setStyle(base_table_style())
    t.setStyle(TableStyle([
        ("TEXTCOLOR", (0,1), (0,-1), MUTED),
        ("TEXTCOLOR", (2,1), (2,-1), MUTED),
    ]))
    st.append(t)
    st.append(Spacer(1, 0.3*cm))

    print("  Ejecutando predicción de ejemplo…")
    pred = fetch_post_json("/api/predecir", {
        "metros_habitables": 1800, "metros_totales": 0.5,
        "precio_terreno": 60000,   "antiguedad": 15,
        "dormitorios": 3,          "habitaciones": 7,
        "banyos": 2.0,             "chimenea": 1,
        "universitarios": 50,
        "calefaccion": "hot water/steam", "consumo_calefacion": "gas",
        "desague": "public/commercial",   "vistas_lago": "No",
        "nueva_construccion": "No",       "aire_acondicionado": "No",
    })

    pred_rows = [["Algoritmo", "Precio Predicho"]]
    for nombre, val in pred["predicciones"].items():
        pred_rows.append([nombre, fmt_usd(val)])
    pred_rows.append(["PROMEDIO", fmt_usd(pred["promedio"])])

    t = Table(pred_rows, colWidths=[6*cm, W-6*cm])
    t.setStyle(base_table_style())
    t.setStyle(TableStyle([
        ("ALIGN",       (0,0), (-1,-1), "CENTER"),
        ("BACKGROUND",  (0,-1), (-1,-1), colors.HexColor("#0d2a1e")),
        ("TEXTCOLOR",   (0,-1), (-1,-1), GREEN),
        ("FONTNAME",    (0,-1), (-1,-1), "Inter-Medium"),
        ("FONTSIZE",    (0,-1), (-1,-1), 12),
    ]))
    st.append(t)
    st.append(Paragraph(f"Precio estimado promedio: {fmt_usd(pred['promedio'])}", S["body_center"]))

    # ── 6. VALIDACIONES ───────────────────────────────────────────────────────
    st.append(Paragraph("6. Validaciones y Buenas Prácticas", S["section"]))
    st.append(hr())
    st.append(Paragraph("6.1 Validación de datos (doble capa)", S["subsection"]))

    val_rows = [
        ["Capa", "Tipo", "Descripción"],
        ["Front-end (JS)", "Campos requeridos",  "Todos los campos deben completarse antes de enviar"],
        ["Front-end (JS)", "Rangos numéricos",    "Valida min/max por campo (metros, años, precio, etc.)"],
        ["Front-end (JS)", "Regla de negocio",    "Habitaciones totales ≥ dormitorios"],
        ["Front-end (JS)", "Selects vacíos",      "Los dropdowns deben tener opción seleccionada"],
        ["Back-end (Py)",  "Campos faltantes",    "Retorna 400 si falta algún campo requerido"],
        ["Back-end (Py)",  "Rangos numéricos",    "Retorna 422 con mensaje de error detallado"],
        ["Back-end (Py)",  "Opciones categóricas","Valida contra lista blanca de valores permitidos"],
    ]
    t = Table(val_rows, colWidths=[3*cm, 3.5*cm, W-6.5*cm])
    t.setStyle(base_table_style())
    t.setStyle(TableStyle([
        ("TEXTCOLOR", (0,1), (0,-1), ACCENT),
        ("TEXTCOLOR", (1,1), (1,-1), YELLOW),
    ]))
    st.append(t)

    st.append(Paragraph("6.2 Buenas prácticas implementadas", S["subsection"]))
    for bp in [
        "Separación de responsabilidades: lógica ML en backend, presentación en frontend.",
        "Caché de modelos: los 4 modelos se entrenan una sola vez al inicio y se reutilizan en cada request.",
        "Manejo de errores: try/except en todos los endpoints con respuestas JSON descriptivas.",
        "Preprocesamiento consistente: el mismo StandardScaler y LabelEncoders del entrenamiento se aplican en predicción.",
        "Valores nulos: np.nan_to_num() garantiza que el dataset no tenga NaN antes del entrenamiento.",
        "Respuestas HTTP semánticas: 400 (campos faltantes), 422 (validación fallida), 500 (error interno).",
    ]:
        st.append(Paragraph(f"• {bp}", S["body"]))

    # ── 7. CONCLUSIONES ───────────────────────────────────────────────────────
    st.append(PageBreak())
    st.append(Paragraph("7. Resultados y Conclusiones", S["section"]))
    st.append(hr())
    st.append(Paragraph(
        "Los cuatro algoritmos fueron evaluados sobre el 20% del dataset (346 registros) reservado "
        "para prueba, con el 80% restante (1,382 registros) para entrenamiento (random_state=42).",
        S["body"]))

    res_rows = [["Algoritmo", "R²", "RMSE", "MAE", "Interpretabilidad", "Velocidad"]]
    meta = {
        "Regresión Lineal": ("Alta",  "Muy rápido"),
        "KNN (k=5)":        ("Baja",  "Lento en prod."),
        "SVM (RBF)":        ("Baja",  "Lento en entreno"),
        "Árbol Decisión":   ("Alta",  "Rápido"),
    }
    for d in comp:
        interp, vel = meta.get(d["nombre"], ("—","—"))
        res_rows.append([d["nombre"], f"{d['r2']}%",
                         fmt_usd(d["rmse"]), fmt_usd(d["mae"]), interp, vel])

    t = Table(res_rows, colWidths=[3.8*cm, 1.6*cm, 2.6*cm, 2.4*cm, 2.2*cm, 2*cm])
    t.setStyle(base_table_style())
    t.setStyle(TableStyle([("ALIGN", (1,0), (-1,-1), "CENTER")]))
    st.append(t)
    st.append(Spacer(1, 0.4*cm))

    for i, txt in enumerate([
        "<b>Regresión Lineal es el mejor modelo</b> en este dataset (R²=60.05%, RMSE=$68,441, "
        "MAE=$45,475). Su simplicidad resulta ser una ventaja porque el precio tiene componentes "
        "aproximadamente lineales respecto a metros habitables, precio del terreno y antigüedad.",

        "<b>KNN obtuvo resultados similares</b> (R²=58.27%), confirmando que la similitud espacial "
        "captura bien los patrones locales de precios. Su mayor limitación es la velocidad en "
        "datasets grandes.",

        "<b>SVM (RBF) tuvo el rendimiento más bajo</b> (R²=2.25%), indicando que los hiperparámetros "
        "C=100 y γ=auto no son óptimos para este dataset. Con grid search podría mejorar significativamente.",

        "<b>Árbol de Decisión (R²=53.44%)</b> ofrece la mejor interpretabilidad con reglas explícitas. "
        "Es el modelo más útil para explicar decisiones a usuarios no técnicos.",

        "<b>Para producción</b> se recomienda usar Regresión Lineal como modelo principal y mostrar "
        "el promedio de los 4 algoritmos (como ya hace el sistema) para dar un rango más robusto.",
    ], 1):
        st.append(Paragraph(f"{i}. {txt}", S["body"]))

    st.append(Spacer(1, 1*cm))
    st.append(hr(ACCENT, 1))
    st.append(Paragraph(
        f"Informe generado automáticamente el {datetime.today().strftime('%d/%m/%Y')} "
        "mediante el sistema en producción.",
        S["caption"]))

    print("  Generando PDF…")
    doc.build(st, onFirstPage=on_page, onLaterPages=on_page)
    print(f"\n✓ PDF generado: {os.path.abspath(out)}")
    return out


if __name__ == "__main__":
    path = generar_pdf()
    print(f"Tamaño: {os.path.getsize(path)/1024:.1f} KB")
