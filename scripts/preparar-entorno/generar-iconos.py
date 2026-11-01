"""Genera los iconos de TaskFlow Mobile (tarjeta con marca de verificación) en app/assets.

Uso:  python scripts/preparar-entorno/generar-iconos.py
"""
from pathlib import Path
from PIL import Image, ImageDraw

ASSETS = Path(__file__).resolve().parents[2] / "app" / "assets"
INDIGO = (79, 70, 229, 255)
BLANCO = (255, 255, 255, 255)
VERDE = (16, 185, 129, 255)
N = 1024


def glifo(draw: ImageDraw.ImageDraw, escala: float, color_tarjeta, color_check, cx=N / 2, cy=N / 2):
    w = 520 * escala
    h = 600 * escala
    x0, y0 = cx - w / 2, cy - h / 2
    draw.rounded_rectangle([x0, y0, x0 + w, y0 + h], radius=70 * escala, fill=color_tarjeta)
    # Líneas de "tareas"
    for i in range(3):
        y = y0 + 150 * escala + i * 130 * escala
        draw.rounded_rectangle([x0 + 70 * escala, y, x0 + w - 70 * escala, y + 36 * escala],
                               radius=18 * escala, fill=(199, 210, 254, 255) if color_tarjeta == BLANCO else color_check)
    # Círculo con check
    r = 150 * escala
    ccx, ccy = x0 + w - 20 * escala, y0 + h - 20 * escala
    draw.ellipse([ccx - r, ccy - r, ccx + r, ccy + r], fill=color_check)
    lw = int(42 * escala)
    draw.line([(ccx - 70 * escala, ccy + 5 * escala), (ccx - 15 * escala, ccy + 60 * escala),
               (ccx + 80 * escala, ccy - 55 * escala)], fill=BLANCO if color_check != BLANCO else INDIGO,
              width=lw, joint="curve")


def main():
    # Icono general
    img = Image.new("RGBA", (N, N), INDIGO)
    glifo(ImageDraw.Draw(img), 1.0, BLANCO, VERDE, cx=N / 2 - 40, cy=N / 2 - 40)
    img.save(ASSETS / "icon.png")

    # Adaptive icon: fondo sólido + primer plano dentro de la zona segura (66 %)
    Image.new("RGBA", (N, N), INDIGO).save(ASSETS / "android-icon-background.png")
    fg = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    glifo(ImageDraw.Draw(fg), 0.62, BLANCO, VERDE, cx=N / 2 - 25, cy=N / 2 - 25)
    fg.save(ASSETS / "android-icon-foreground.png")

    mono = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    glifo(ImageDraw.Draw(mono), 0.62, BLANCO, BLANCO, cx=N / 2 - 25, cy=N / 2 - 25)
    mono.save(ASSETS / "android-icon-monochrome.png")

    splash = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    glifo(ImageDraw.Draw(splash), 0.8, INDIGO, VERDE, cx=N / 2 - 30, cy=N / 2 - 30)
    splash.save(ASSETS / "splash-icon.png")
    print("Iconos generados en", ASSETS)


if __name__ == "__main__":
    main()
