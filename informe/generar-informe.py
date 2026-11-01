"""Genera informe/Informe-Final-Maestro.pdf a partir de los resultados REALES guardados en el repositorio.

Lee:
  resultados/entorno/versiones-entorno.txt
  resultados/ejecuciones/<ejecucion>-<fecha>/resumen.json   (la más reciente de cada tipo)
  resultados/reportes/*-junit.xml
  evidencias/**.png  (capturas de Maestro takeScreenshot y de la terminal)

Uso: python informe/generar-informe.py --commit <sha> [--fecha YYYY-MM-DD]
"""
import argparse
import json
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

RAIZ = Path(__file__).resolve().parents[1]
REPO = "https://github.com/javier2002guerra-lab/Automatizaci-n-de-recorridos-m-viles-con-Maestro"
FUENTES = Path("C:/Windows/Fonts")

pdfmetrics.registerFont(TTFont("Calibri", str(FUENTES / "calibri.ttf")))
pdfmetrics.registerFont(TTFont("Calibri-Bold", str(FUENTES / "calibrib.ttf")))
pdfmetrics.registerFont(TTFont("Calibri-Italic", str(FUENTES / "calibrii.ttf")))
pdfmetrics.registerFont(TTFont("Consolas", str(FUENTES / "consola.ttf")))
pdfmetrics.registerFontFamily("Calibri", normal="Calibri", bold="Calibri-Bold", italic="Calibri-Italic")

AZUL = colors.HexColor("#1F3A68")
GRIS = colors.HexColor("#F2F4F7")

base = getSampleStyleSheet()
E = {
    "normal": ParagraphStyle("n", parent=base["Normal"], fontName="Calibri", fontSize=11, leading=15,
                             alignment=TA_JUSTIFY, spaceAfter=6),
    "h1": ParagraphStyle("h1", parent=base["Heading1"], fontName="Calibri-Bold", fontSize=16, leading=20,
                         textColor=AZUL, spaceBefore=10, spaceAfter=8, keepWithNext=1),
    "h2": ParagraphStyle("h2", parent=base["Heading2"], fontName="Calibri-Bold", fontSize=13, leading=16,
                         textColor=AZUL, spaceBefore=8, spaceAfter=6, keepWithNext=1),
    "celda": ParagraphStyle("c", fontName="Calibri", fontSize=9, leading=11.5),
    "celdaB": ParagraphStyle("cb", fontName="Calibri-Bold", fontSize=9, leading=11.5, textColor=colors.white),
    "codigo": ParagraphStyle("code", fontName="Consolas", fontSize=8, leading=10.5, backColor=GRIS,
                             borderPadding=5, spaceBefore=4, spaceAfter=8),
    "pie": ParagraphStyle("pie", fontName="Calibri-Italic", fontSize=9.5, leading=12, alignment=TA_CENTER,
                          textColor=colors.HexColor("#444444"), spaceBefore=3, spaceAfter=10),
    "portada": ParagraphStyle("p", fontName="Calibri-Bold", fontSize=20, leading=26, alignment=TA_CENTER,
                              textColor=AZUL),
    "portada2": ParagraphStyle("p2", fontName="Calibri", fontSize=14, leading=20, alignment=TA_CENTER),
    "vineta": ParagraphStyle("v", fontName="Calibri", fontSize=11, leading=15, leftIndent=14, bulletIndent=4,
                             spaceAfter=3),
}


def P(t, s="normal"):
    return Paragraph(t, E[s])


def vinetas(items):
    return [Paragraph(i, E["vineta"], bulletText="•") for i in items]


def tabla(filas, anchos, cabecera=True):
    datos = [[c if not isinstance(c, str) else Paragraph(c, E["celdaB" if (cabecera and i == 0) else "celda"])
              for c in fila] for i, fila in enumerate(filas)]
    t = Table(datos, colWidths=anchos, repeatRows=1 if cabecera else 0)
    estilo = [("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#B0B7C3")),
              ("VALIGN", (0, 0), (-1, -1), "TOP"),
              ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]
    if cabecera:
        estilo.append(("BACKGROUND", (0, 0), (-1, 0), AZUL))
        estilo.append(("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, GRIS]))
    t.setStyle(TableStyle(estilo))
    return t


def recorte_terminal(ruta: Path) -> Path:
    """Copia de la captura de terminal recortada al área que contiene texto (solo para el PDF).
    El archivo original completo permanece sin cambios en evidencias/."""
    im = PILImage.open(ruta).convert("RGB")
    w, h = im.size
    gris = im.convert("L").point(lambda v: 255 if v > 60 else 0)
    ultima = 60
    for y in range(h - 12, 40, -1):
        if gris.crop((12, y, w - 45, y + 1)).getbbox():
            ultima = y
            break
    destino = RAIZ / "informe" / ".tmp" / ruta.name
    destino.parent.mkdir(exist_ok=True)
    im.crop((0, 0, w, min(h, ultima + 24))).save(destino)
    return destino


class Figuras:
    def __init__(self):
        self.n = 0

    def img(self, ruta: Path, pie: str, alto_max=11 * cm, ancho_max=15.5 * cm):
        self.n += 1
        w, h = PILImage.open(ruta).size
        esc = min(ancho_max / w, alto_max / h)  # mantiene la proporción original
        im = Image(str(ruta), width=w * esc, height=h * esc)
        return KeepTogether([im, P(f"Figura {self.n}. {pie}", "pie")])

    def fila(self, rutas_pies, alto=10.5 * cm):
        """Varias capturas de móvil lado a lado (mismo alto, proporción conservada)."""
        celdas, pies = [], []
        for ruta, pie in rutas_pies:
            self.n += 1
            w, h = PILImage.open(ruta).size
            esc = alto / h
            celdas.append(Image(str(ruta), width=w * esc, height=alto))
            pies.append(P(f"Figura {self.n}. {pie}", "pie"))
        t = Table([celdas, pies], colWidths=[16.5 * cm / len(celdas)] * len(celdas))
        t.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
        return KeepTogether([t])


def ultima_ejecucion(nombre):
    dirs = sorted((RAIZ / "resultados" / "ejecuciones").glob(f"{nombre}-*"))
    for d in reversed(dirs):
        r = d / "resumen.json"
        if r.exists():
            return json.loads(r.read_text(encoding="utf-8-sig")), d
    raise SystemExit(f"No hay ejecución registrada para {nombre}")


def junit(nombre):
    ruta = RAIZ / "resultados" / "reportes" / f"{nombre}-junit.xml"
    raiz = ET.parse(ruta).getroot()
    casos = []
    for tc in raiz.iter("testcase"):
        fallo = tc.find("failure") is not None or tc.find("error") is not None
        casos.append({"nombre": tc.get("name"), "tiempo": tc.get("time"), "ok": not fallo})
    return casos


def entorno():
    datos = {}
    for linea in (RAIZ / "resultados" / "entorno" / "versiones-entorno.txt").read_text(encoding="utf-8-sig").splitlines():
        if ":" in linea:
            k, v = linea.split(":", 1)
            datos[k.strip()] = v.strip()
        elif "=" in linea:
            k, v = linea.split("=", 1)
            datos[k.strip()] = v.strip()
    return datos


def unir_titulos(h):
    """Mantiene cada título (o grupo de títulos seguidos) en la misma página que el bloque siguiente."""
    salida, grupo = [], []
    for f in h:
        if isinstance(f, Paragraph) and f.style.name in ("h1", "h2"):
            grupo.append(f)
        elif grupo:
            salida.append(KeepTogether(grupo + [f]))
            grupo = []
        else:
            salida.append(f)
    return salida + grupo


def pie_pagina(canvas, doc):
    canvas.saveState()
    canvas.setFont("Calibri", 9)
    canvas.setFillColor(colors.HexColor("#666666"))
    if doc.page > 1:
        canvas.drawString(2.2 * cm, 1.3 * cm, "Automatización de recorridos móviles con Maestro — TaskFlow Mobile")
        canvas.drawRightString(LETTER[0] - 2.2 * cm, 1.3 * cm, f"Página {doc.page}")
    canvas.restoreState()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--commit", required=True, help="SHA del commit de código/pruebas que documenta el informe")
    ap.add_argument("--fecha", default=date.today().isoformat())
    ap.add_argument("--apk-url", required=True)
    args = ap.parse_args()

    env = entorno()
    ejec = {k: ultima_ejecucion(k) for k in ["escenario-01", "escenario-02", "escenario-03", "ejecucion-conjunta"]}
    jun = {k: junit(k) for k in ejec}
    ev = RAIZ / "evidencias"
    fig = Figuras()
    sha_corto = args.commit[:7]
    url_commit = f"{REPO}/commit/{args.commit}"

    def estado(k):
        return ejec[k][0]["resultado"]

    h = []
    # ---------------- Portada ----------------
    h += [Spacer(1, 3 * cm), P("Universidad Mariano Gálvez de Guatemala", "portada"), Spacer(1, 0.4 * cm),
          P("Ingeniería en Sistemas", "portada2"), Spacer(1, 3 * cm),
          P("Automatización de recorridos móviles con Maestro", "portada"), Spacer(1, 0.5 * cm),
          P("Proyecto final: TaskFlow Mobile – Gestor de Tareas", "portada2"), Spacer(1, 4 * cm),
          P("<b>Estudiante:</b> Javier Alejandro Guerra Zepeda", "portada2"), Spacer(1, 0.3 * cm),
          P(f"<b>Fecha:</b> {args.fecha}", "portada2"), PageBreak()]

    # ---------------- 1. Descripción ----------------
    h += [P("1. Descripción de la aplicación", "h1"),
          P("<b>TaskFlow Mobile</b> es una aplicación Android nativa, desarrollada con React Native 0.88, Expo SDK 58 "
            "y TypeScript, que permite gestionar tareas personales. Se distribuye como un APK <i>release</i> que "
            "incluye el código JavaScript empaquetado (motor Hermes), por lo que no depende de Expo Go ni de un "
            "servidor Metro en ejecución."),
          P("Funciones disponibles:")]
    h += vinetas([
        "Pantalla principal con el listado de tareas y un contador de pendientes y completadas.",
        "Formulario de nueva tarea con título obligatorio (máx. 80 caracteres) y descripción opcional.",
        "Validación: si el título está vacío o solo contiene espacios se muestra «El título es obligatorio» y no se guarda nada.",
        "Confirmación visible «Tarea guardada correctamente» tras un guardado exitoso.",
        "Marcar o desmarcar una tarea como completada (estado «Pendiente» / «Completada» y texto tachado).",
        "Persistencia local con AsyncStorage: las tareas se conservan al cerrar y reabrir la aplicación.",
        "Navegación entre pantallas con el botón «Volver», «Cancelar» y el botón atrás de Android; el formulario se adapta al teclado.",
    ])
    h += [P("La aplicación no usa backend ni servicios externos: todos los datos se guardan en el almacenamiento "
            "privado de la app en el dispositivo. Esto la hace adecuada para probar recorridos móviles, porque "
            "incluye entrada de texto con el teclado de Android, validaciones, navegación, cambios de estado y "
            "un comportamiento propio del móvil: la recuperación de datos tras cerrar el proceso. Todos los "
            "controles tienen <i>testID</i> estables (por ejemplo <font face='Consolas'>btn-nueva-tarea</font>, "
            "<font face='Consolas'>input-titulo</font>, <font face='Consolas'>btn-guardar</font>, "
            "<font face='Consolas'>error-titulo</font>), que Maestro localiza sin usar coordenadas.")]

    # ---------------- 2. Entorno ----------------
    e1 = ejec["escenario-01"][0]
    fechas = sorted(ejec[k][0]["inicio"][:10] for k in ejec)
    h += [P("2. Entorno utilizado", "h1"), tabla([
        ["Elemento", "Valor"],
        ["Sistema operativo", env.get("Sistema operativo", "")],
        ["Equipo", f"{env.get('CPU', '')}, {env.get('RAM', '')} de RAM"],
        ["Plataforma", "Android (emulador oficial de Android SDK, aceleración WHPX)"],
        ["Versión de Android", f"Android {e1['android']} (API {e1['api']})"],
        ["Emulador", f"AVD «TaskFlow_API35», perfil Pixel 6, imagen google_apis x86_64, 1080×2400, 420 dpi, 2 GB RAM "
                     f"— serial ADB {e1['dispositivo']}, modelo {e1['modelo']}"],
        ["Maestro CLI", env.get("Maestro CLI", "")],
        ["Node.js / npm", f"Node.js v22.23.4 (compilación) y {env.get('Node.js', '')} (sistema) / npm {env.get('npm', '')}"],
        ["Java / Android", f"{env.get('Java', '')}; {env.get('ADB', '')}; Android Emulator {env.get('Android Emulator', '').replace('Android emulator version ', '')}"],
        ["Framework", f"Expo SDK 58 (CLI {env.get('Expo CLI', '')}), React Native 0.88.1, TypeScript 6, Gradle 9.4.1"],
        ["Versión de la app", "1.0.0 (versionCode 1)"],
        ["Identificador de paquete", "gt.edu.umg.taskflow"],
        ["Almacenamiento", "Local con @react-native-async-storage/async-storage 2.2.0 (sin backend)"],
        ["Fecha de ejecución", ", ".join(sorted(set(fechas)))],
    ], [4.2 * cm, 12.3 * cm])]

    # ---------------- 3. Escenarios ----------------
    def obs(k, texto):
        r = ejec[k][0]
        if r["resultado"] != "APROBADO":
            texto = "Maestro devolvió errores; ver el registro de la ejecución en resultados/ejecuciones."
        return f"<b>{r['resultado']}</b> (código de salida {r['codigoSalida']}). {texto}"

    h += [P("3. Escenarios automatizados", "h1"), tabla([
        ["Escenario", "Objetivo", "Precondiciones", "Acciones principales", "Resultado esperado", "Resultado observado"],
        ["01 – Registro exitoso<br/><font face='Consolas' size='7'>01-registro-exitoso.yaml</font>",
         "Crear una tarea y verla en el listado.",
         "App instalada; datos borrados con clearState; sin sesiones previas.",
         "Abrir app, verificar pantalla principal, abrir formulario, escribir título y descripción, guardar.",
         "Confirmación visible y tarea listada con el título correcto, estado Pendiente.",
         obs("escenario-01", "Se mostró «Tarea guardada correctamente» y la tarea «Preparar informe de pruebas» "
                             "apareció como Pendiente; contador «1 pendiente · 0 completadas».")],
        ["02 – Validación<br/><font face='Consolas' size='7'>02-validacion-entrada.yaml</font>",
         "Rechazar una tarea sin título.",
         "App instalada; listado vacío (clearState); formulario disponible.",
         "Abrir formulario, dejar título vacío, escribir descripción, guardar; repetir con título de solo espacios; cancelar.",
         "Mensaje de error, sin confirmación y sin registro inválido.",
         obs("escenario-02", "Apareció «El título es obligatorio» en ambos intentos, no hubo confirmación y "
                             "el listado siguió vacío («0 pendientes · 0 completadas»).")],
        ["03 – Persistencia<br/><font face='Consolas' size='7'>03-persistencia-reapertura.yaml</font>",
         "Conservar datos tras cerrar y reabrir.",
         "App instalada; limpieza solo al inicio; almacenamiento local operativo.",
         "Crear tarea, stopApp, launchApp sin clearState, verificar, marcar completada, reabrir otra vez.",
         "La tarea sigue tras reabrir y su estado Completada se refleja y se conserva.",
         obs("escenario-03", "«Tarea persistente reapertura» siguió visible tras reabrir; al marcarla cambió a "
                             "Completada («0 pendientes · 1 completada») y lo conservó tras una segunda reapertura.")],
    ], [2.6 * cm, 2.4 * cm, 2.6 * cm, 3.4 * cm, 2.6 * cm, 3.4 * cm])]

    # ---------------- 4. Ejecución ----------------
    def fila_ej(k, titulo):
        r = ejec[k][0]
        casos = jun[k]
        ok = sum(c["ok"] for c in casos)
        dur = sum(float(c["tiempo"] or 0) for c in casos)
        return [titulo, r["inicio"][:19].replace("T", " "), f"{ok}/{len(casos)} aprobados", f"{dur:.1f} s",
                str(r["codigoSalida"]), r["resultado"]]

    h += [P("4. Ejecución y resultados", "h1"),
          P("<b>Instalación.</b> El APK se compiló localmente con <font face='Consolas'>scripts\\compilar-apk.ps1</font> "
            "(<font face='Consolas'>expo prebuild</font> + <font face='Consolas'>gradlew assembleRelease</font>) y se "
            "instaló en el emulador con <font face='Consolas'>adb install -r</font>. Se verificó con "
            "<font face='Consolas'>dumpsys package</font> que el paquete instalado es "
            "<font face='Consolas'>gt.edu.umg.taskflow</font>, versionName 1.0.0 y versionCode 1, el mismo "
            "<font face='Consolas'>appId</font> de los flujos."),
          P("<b>Datos.</b> Cada escenario comienza con <font face='Consolas'>helpers/iniciar-limpio.yaml</font>, que "
            "abre la app con <font face='Consolas'>clearState: true</font> y comprueba que el listado está vacío. "
            "Los datos de prueba (títulos y descripciones) están definidos en la sección <font face='Consolas'>env</font> de cada YAML."),
          P("<b>Ejecución.</b> Cada escenario se ejecutó por separado y después los tres juntos con "
            "<font face='Consolas'>scripts\\ejecutar-pruebas.ps1</font>, que llama a Maestro con reporte JUnit y "
            "guarda la salida de la terminal, el código de salida y las capturas:"),
          P("maestro test maestro/01-registro-exitoso.yaml --format JUNIT --output resultados/reportes/escenario-01-junit.xml "
            "--test-output-dir resultados/ejecuciones/... --udid emulator-5554<br/>"
            "maestro test maestro --format JUNIT --output resultados/reportes/ejecucion-conjunta-junit.xml --udid emulator-5554",
            "codigo"),
          P("<b>Verificaciones.</b> Además de los toques, cada flujo usa <font face='Consolas'>assertVisible</font> y "
            "<font face='Consolas'>assertNotVisible</font> sobre identificadores y textos (pantalla visible, formulario "
            "abierto, contenido de los campos, mensaje de confirmación o de error, título y estado de la tarea, "
            "contador), y <font face='Consolas'>extendedWaitUntil</font> como espera condicionada en lugar de pausas fijas."),
          P("<b>Resultados devueltos por Maestro</b> (tomados de los reportes JUnit y de los registros):"),
          tabla([["Ejecución", "Inicio", "Flujos", "Duración", "Código salida", "Resultado"],
                 fila_ej("escenario-01", "Escenario 01"), fila_ej("escenario-02", "Escenario 02"),
                 fila_ej("escenario-03", "Escenario 03"), fila_ej("ejecucion-conjunta", "Conjunta (3 flujos)")],
                [3.5 * cm, 3.4 * cm, 2.6 * cm, 2.0 * cm, 2.2 * cm, 2.8 * cm]),
          Spacer(1, 6),
          P("Además de las ejecuciones de la tabla, hubo una primera ejecución del escenario 01 "
            "(<font face='Consolas'>resultados/ejecuciones/escenario-01-20261031-193356</font>), también aprobada con código 0; "
            "se repitió solo para corregir la codificación del registro y la captura de la terminal, y se conserva en el repositorio. "
            "En total, los siete archivos <font face='Consolas'>commands.json</font> de Maestro (uno por flujo ejecutado) registran todos sus comandos con estado "
            "COMPLETED (<font face='Consolas'>resultados/resumen-comandos-maestro.txt</font>)."),
          P("En la ejecución conjunta Maestro corrió los tres flujos en orden (definido en "
            "<font face='Consolas'>maestro/config.yaml</font>) sobre la misma instalación. Como cada flujo limpia "
            "su propio estado al comenzar, ninguno depende de los datos que deja el anterior.")]

    # ---------------- 5. Evidencias ----------------
    h += [P("5. Evidencias gráficas", "h1"),
          P("Todas las capturas del dispositivo se tomaron con el comando <font face='Consolas'>takeScreenshot</font> de "
            "Maestro durante las ejecuciones registradas. Las capturas de terminal son imágenes de la ventana real de "
            "PowerShell en la que corrió cada ejecución."),
          P("5.1 Escenario 01 – Registro exitoso", "h2")]
    e = ev / "escenario-01"
    h.append(fig.fila([(e / "escenario-01_01_pantalla-inicial.png", "Pantalla principal de TaskFlow Mobile (estado limpio)."),
                       (e / "escenario-01_02_formulario-completado.png", "Formulario completado."),
                       (e / "escenario-01_03_confirmacion-y-tarea-creada.png", "Confirmación y tarea registrada.")]))
    h.append(fig.img(recorte_terminal(e / "terminal-escenario-01.png"), "Resultado de Maestro para el escenario 01: ventana de PowerShell de la ejecución (área con texto; original completo en evidencias/escenario-01/)."))

    h += [P("5.2 Escenario 02 – Validación de campo obligatorio", "h2")]
    e = ev / "escenario-02"
    h.append(fig.fila([(e / "escenario-02_01_formulario-titulo-vacio.png", "Formulario con el título vacío."),
                       (e / "escenario-02_02_mensaje-validacion.png", "Mensaje de validación."),
                       (e / "escenario-02_03_estado-posterior-rechazo.png", "Listado sin registros tras el rechazo.")]))
    h.append(fig.img(recorte_terminal(e / "terminal-escenario-02.png"), "Resultado de Maestro para el escenario 02: ventana de PowerShell de la ejecución (área con texto; original completo en evidencias/escenario-02/)."))

    h += [P("5.3 Escenario 03 – Reapertura y recuperación del estado", "h2")]
    e = ev / "escenario-03"
    h.append(fig.fila([(e / "escenario-03_01_tarea-creada-antes-del-cierre.png", "Tarea creada antes del cierre."),
                       (e / "escenario-03_02_app-reabierta-tarea-conservada.png", "App reabierta: tarea conservada."),
                       (e / "escenario-03_03_tarea-completada.png", "Tarea marcada como completada."),
                       (e / "escenario-03_04_completada-tras-segunda-reapertura.png", "Estado conservado tras otra reapertura.")],
                      alto=9 * cm))
    h.append(fig.img(recorte_terminal(e / "terminal-escenario-03.png"), "Resultado de Maestro para el escenario 03: ventana de PowerShell de la ejecución (área con texto; original completo en evidencias/escenario-03/)."))

    h += [P("5.4 Ejecución conjunta", "h2")]
    h.append(fig.img(recorte_terminal(ev / "ejecucion-conjunta" / "terminal-ejecucion-conjunta.png"),
                     "Resultado de Maestro para la ejecución conjunta de los tres escenarios: ventana de PowerShell "
                     "(área con texto; original completo en evidencias/ejecucion-conjunta/).", alto_max=13 * cm))

    # ---------------- 6. Preparación y limpieza ----------------
    h += [P("6. Preparación y limpieza", "h1")]
    h += vinetas([
        "<b>Independencia:</b> los tres escenarios empiezan con <font face='Consolas'>runFlow: helpers/iniciar-limpio.yaml</font>. "
        "Ese helper usa <font face='Consolas'>launchApp</font> con <font face='Consolas'>clearState: true</font> y comprueba "
        "que se ve «Aún no tienes tareas» y «0 pendientes · 0 completadas». Así cada escenario se puede ejecutar solo, en "
        "cualquier orden y varias veces.",
        "<b>Alcance de la limpieza:</b> <font face='Consolas'>clearState</font> borra únicamente los datos privados del paquete "
        "<font face='Consolas'>gt.edu.umg.taskflow</font> en el emulador de pruebas (igual que «Borrar datos» en Ajustes). "
        "La aplicación no tiene ninguna función oculta de restablecimiento que pudiera afectar a usuarios reales.",
        "<b>Persistencia (escenario 03):</b> la limpieza se hace solo una vez, antes de crear la tarea. Las reaperturas usan "
        "<font face='Consolas'>stopApp</font> y <font face='Consolas'>launchApp</font> con <font face='Consolas'>clearState: false</font>, "
        "de modo que el proceso se cierra pero los datos de AsyncStorage se conservan.",
        "<b>Datos de prueba:</b> títulos y descripciones ficticios definidos en el bloque <font face='Consolas'>env</font> de cada flujo; "
        "no se usan datos personales.",
        "<b>Limpieza manual opcional:</b> <font face='Consolas'>scripts\\limpiar-datos.ps1</font> ejecuta "
        "<font face='Consolas'>adb shell pm clear gt.edu.umg.taskflow</font>.",
    ])

    # ---------------- 7. Dependencias y limitaciones ----------------
    h += [P("7. Dependencias y limitaciones", "h1"),
          P("La aplicación usa <b>almacenamiento local</b> (AsyncStorage). No hay backend real ni simulado y no requiere "
            "conexión a Internet para funcionar. Limitaciones identificadas:")]
    h += vinetas([
        "Las pruebas se ejecutaron solo en el emulador descrito (Android 15, API 35, x86_64). No se probó en un dispositivo "
        "físico ni en otras versiones de Android, ni en iOS.",
        "El APK incluye las arquitecturas arm64-v8a y x86_64 (no armeabi-v7a ni x86), para reducir tiempo de compilación.",
        "El APK release está firmado con la clave de depuración que genera Expo; sirve para instalarlo directamente, "
        "pero no para publicarlo en Google Play, que exige una clave de subida propia.",
        "Los datos que Maestro teclea con <font face='Consolas'>inputText</font> se escribieron sin tildes por precaución, "
        "ya que la escritura de caracteres no ASCII en Android puede no ser fiable; no se probó la entrada con acentos. "
        "Los textos de la interfaz y las aserciones sí usan tildes (por ejemplo «El título es obligatorio»).",
        "La carpeta <font face='Consolas'>app/android</font> no se versiona: se genera con <font face='Consolas'>expo prebuild</font> "
        "a partir de <font face='Consolas'>app.json</font>.",
    ])

    # ---------------- 8. Enlaces ----------------
    h += [P("8. Enlaces de entrega", "h1"), tabla([
        ["Recurso", "Enlace"],
        ["Repositorio GitHub", f"<link href='{REPO}' color='blue'>{REPO}</link>"],
        ["Commit documentado", f"<link href='{url_commit}' color='blue'>{url_commit}</link>"],
        ["APK instalable (Release v1.0.0)", f"<link href='{args.apk_url}' color='blue'>{args.apk_url}</link>"],
        ["Flujos YAML", f"<link href='{REPO}/tree/main/maestro' color='blue'>{REPO}/tree/main/maestro</link>"],
        ["Evidencias (capturas)", f"<link href='{REPO}/tree/main/evidencias' color='blue'>{REPO}/tree/main/evidencias</link>"],
        ["Registros y reportes JUnit", f"<link href='{REPO}/tree/main/resultados' color='blue'>{REPO}/tree/main/resultados</link>"],
    ], [4.2 * cm, 12.3 * cm])]

    # ---------------- 9. Resultado final ----------------
    ind = [estado(k) for k in ["escenario-01", "escenario-02", "escenario-03"]]
    aprob = ind.count("APROBADO")
    conj = jun["ejecucion-conjunta"]
    h += [P("9. Resultado final", "h1"),
          P(f"En las ejecuciones individuales se aprobaron <b>{aprob} de 3</b> escenarios "
            f"(01: {ind[0]}, 02: {ind[1]}, 03: {ind[2]}). En la ejecución conjunta Maestro informó "
            f"<b>{sum(c['ok'] for c in conj)} de {len(conj)}</b> flujos aprobados, con resultado "
            f"<b>{estado('ejecucion-conjunta')}</b> (código de salida {ejec['ejecucion-conjunta'][0]['codigoSalida']}).")]
    if aprob == 3 and estado("ejecucion-conjunta") == "APROBADO":
        h.append(P("Con estos resultados se comprueba, en el emulador indicado, que TaskFlow Mobile permite registrar "
                   "tareas, rechaza entradas sin título sin crear registros inválidos y conserva los datos y su estado "
                   "después de cerrar y reabrir la aplicación. Los registros originales, los reportes JUnit y todas las "
                   f"capturas están publicados en el repositorio (commit {sha_corto})."))

    doc = SimpleDocTemplate(str(RAIZ / "informe" / "Informe-Final-Maestro.pdf"), pagesize=LETTER,
                            leftMargin=2.2 * cm, rightMargin=2.2 * cm, topMargin=2 * cm, bottomMargin=2 * cm,
                            title="Automatización de recorridos móviles con Maestro",
                            author="Javier Alejandro Guerra Zepeda", subject="Informe final – TaskFlow Mobile")
    doc.build(unir_titulos(h), onFirstPage=pie_pagina, onLaterPages=pie_pagina)
    print("PDF generado:", RAIZ / "informe" / "Informe-Final-Maestro.pdf")


if __name__ == "__main__":
    main()
