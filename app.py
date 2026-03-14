"""
QR Code Generator — Streamlit App
-----------------------------------
Dépendances :
    pip install streamlit "qrcode[pil]" Pillow numpy

Lancement :
    python -m streamlit run app.py
"""

import io
from datetime import datetime

import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers.pil import (
    CircleModuleDrawer,
    GappedSquareModuleDrawer,
    HorizontalBarsDrawer,
    RoundedModuleDrawer,
    SquareModuleDrawer,
    VerticalBarsDrawer,
)
import streamlit as st
from PIL import Image, ImageDraw

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="QR Code Generator",
    page_icon="⛩️",
    layout="wide",
)

st.title("Générateur de QR Code")

QR_SHAPES = {
    "Carré (défaut)":      SquareModuleDrawer,
    "Rond / Dots":         RoundedModuleDrawer,
    "Carré espacé":        GappedSquareModuleDrawer,
    "Cercle":              CircleModuleDrawer,
    "Barres verticales":   VerticalBarsDrawer,
    "Barres horizontales": HorizontalBarsDrawer,
}

SIZE     = 1200   # Haute résolution (vs 600 avant)
CORNER_R = 48     # Proportionnel à SIZE


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def hex_to_rgb(h: str) -> tuple:
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def generate_qr(url, logo_file, logo_ratio_pct, qr_color_hex, bg_color_hex,
                module_drawer_cls) -> Image.Image:

    qr_rgb = hex_to_rgb(qr_color_hex)
    bg_rgb  = hex_to_rgb(bg_color_hex)

    # 1. Génération du QR en noir/blanc (toujours fiable, toutes versions)
    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=20,  # 20px par module → image native ~2000px, pas d'upscaling flou
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)

    qr_bw = qr.make_image(
        image_factory=StyledPilImage,
        module_drawer=module_drawer_cls(),
    ).convert('L')  # L = niveaux de gris : 0=module, 255=fond
    qr_bw = qr_bw.resize((SIZE, SIZE), Image.LANCZOS)

    # 2. Colorisation : module→qr_color, fond→bg_color (gère l'anti-aliasing)
    front_img = Image.new('RGB', (SIZE, SIZE), qr_rgb)
    back_img  = Image.new('RGB', (SIZE, SIZE), bg_rgb)
    colored_qr = Image.composite(back_img, front_img, qr_bw)

    # 3. Application des coins arrondis via paste avec masque
    result = Image.new('RGB', (SIZE, SIZE), bg_rgb)
    mask_r = Image.new('L', (SIZE, SIZE), 0)
    ImageDraw.Draw(mask_r).rounded_rectangle([0, 0, SIZE, SIZE], radius=CORNER_R, fill=255)
    result.paste(colored_qr, (0, 0), mask_r)

    # 4. Logo optionnel
    if logo_file is not None:
        logo_size = int(SIZE * logo_ratio_pct / 100)
        logo = Image.open(logo_file).convert('RGBA').resize((logo_size, logo_size), Image.LANCZOS)
        lx = (SIZE - logo_size) // 2
        ly = (SIZE - logo_size) // 2
        pad = 12

        # Cercle blanc derrière le logo
        circle_mask = Image.new('L', (SIZE, SIZE), 0)
        ImageDraw.Draw(circle_mask).ellipse(
            [lx - pad, ly - pad, lx + logo_size + pad, ly + logo_size + pad],
            fill=255,
        )
        result.paste(Image.new('RGB', (SIZE, SIZE), (255, 255, 255)), (0, 0), circle_mask)

        # Masque circulaire forcé sur le logo (indépendant du canal alpha du PNG)
        logo_mask = Image.new('L', (logo_size, logo_size), 0)
        ImageDraw.Draw(logo_mask).ellipse([0, 0, logo_size, logo_size], fill=255)
        result.paste(logo.convert('RGB'), (lx, ly), logo_mask)

    return result


# ─────────────────────────────────────────────
# LAYOUT : gauche = paramètres | droite = résultat
# ─────────────────────────────────────────────
col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.subheader("Contenu")
    url = st.text_input(
        "Texte ou lien à encoder",
        value="",
        placeholder="https://",
    )

    st.subheader("Logo")
    logo_file  = st.file_uploader("Charger un logo (optionnel)", type=["png","jpg","jpeg","webp"])
    logo_ratio = st.slider("Taille du logo (% du QR)", 10, 35, 22, 1)

    st.subheader("Personnalisation")
    qr_shape = st.selectbox("Forme des modules", list(QR_SHAPES.keys()), index=1)

    c1, c2 = st.columns(2)
    with c1:
        qr_color = st.color_picker("Couleur QR", "#000000")
    with c2:
        bg_color = st.color_picker("Couleur fond", "#FFFFFF")

    generate = st.button("Générer le QR Code", type="primary", use_container_width=True)

# ─────────────────────────────────────────────
# GÉNÉRATION
# ─────────────────────────────────────────────
with col_right:
    st.subheader("Résultat")

    if generate:
        if not url.strip():
            st.error("Veuillez saisir un texte ou un lien.")
        else:
            with st.spinner("Génération..."):
                try:
                    img = generate_qr(
                        url=url,
                        logo_file=logo_file,
                        logo_ratio_pct=logo_ratio,
                        qr_color_hex=qr_color,
                        bg_color_hex=bg_color,
                        module_drawer_cls=QR_SHAPES[qr_shape],
                    )
                    st.session_state["qr_img"] = img

                except Exception as e:
                    st.error(f"Erreur : {e}")

    if "qr_img" in st.session_state:
        img = st.session_state["qr_img"]
        col_pad1, col_img, col_pad2 = st.columns([1, 2, 1])
        with col_img:
            st.image(img, use_container_width=True)

        buf = io.BytesIO()
        img.save(buf, format="PNG", dpi=(300, 300))
        buf.seek(0)
        filename = "QR_Code_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".png"
        st.download_button(
            "⬇ Télécharger (PNG 300dpi)",
            data=buf,
            file_name=filename,
            mime="image/png",
            use_container_width=True,
            type="primary",
        )
    else:
        st.info("Le QR code apparaîtra ici après génération.")

# ─────────────────────────────────────────────
# COPYRIGHT
# ─────────────────────────────────────────────
st.markdown(
    f"<div style='text-align:center; color:#888; font-size:0.8em; margin-top:2rem;'>"
    f"© {datetime.now().year} By DataSoft Solution"
    "</div>",
    unsafe_allow_html=True,
)