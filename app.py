"""
QR Code Generator — Streamlit App
-----------------------------------
Dépendances :
    pip install streamlit "qrcode[pil]" Pillow

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

SIZE     = 1200
CORNER_R = 48
BOX_SIZE = 20     # Taille d'un module en pixels (image native)
BORDER   = 2      # Marge en modules

EYE_FRAME_SHAPES = {
    "Carré":         "square",
    "Arrondi":       "rounded",
    "Extra arrondi": "extra_rounded",
    "Cercle":        "circle",
}

EYE_CENTER_SHAPES = {
    "Carré":         "square",
    "Arrondi":       "rounded",
    "Extra arrondi": "extra_rounded",
    "Cercle":        "circle",
    "Losange":       "diamond",
}


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def hex_to_rgb(h: str) -> tuple:
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def draw_eye_frame(result, x, y, size, qr_color, bg_color, shape):
    """Dessine le contour extérieur via supersampling 4× pour éviter tout artefact."""
    S  = 4           # facteur de supersampling
    bs = size * S    # taille du canvas temporaire
    fw = max(bs // 7, 1)

    tmp = Image.new('RGB', (bs, bs), bg_color)
    d   = ImageDraw.Draw(tmp)
    outer = [0, 0, bs, bs]
    inner = [fw, fw, bs - fw, bs - fw]

    if shape == "circle":
        d.ellipse(outer, fill=qr_color)
        d.ellipse(inner, fill=bg_color)
    elif shape == "rounded":
        r = fw * 2
        d.rounded_rectangle(outer, radius=r, fill=qr_color)
        d.rounded_rectangle(inner, radius=max(r - fw, 2), fill=bg_color)
    elif shape == "extra_rounded":
        r = bs // 3
        d.rounded_rectangle(outer, radius=r, fill=qr_color)
        d.rounded_rectangle(inner, radius=max(r - fw, 2), fill=bg_color)
    else:  # square — pas d'artefact mais on garde pour cohérence
        d.rectangle(outer, fill=qr_color)
        d.rectangle(inner, fill=bg_color)

    # Downscale 4× → taille réelle : antialiasing parfait, zéro artefact
    result.paste(tmp.resize((size, size), Image.LANCZOS), (x, y))


def draw_eye_center(draw, x, y, size, qr_color, shape):
    """Dessine le centre intérieur (3×3 modules) d'un marqueur."""
    bbox = [x, y, x + size, y + size]
    if shape == "circle":
        draw.ellipse(bbox, fill=qr_color)
    elif shape == "rounded":
        draw.rounded_rectangle(bbox, radius=size // 4, fill=qr_color)
    elif shape == "extra_rounded":
        draw.rounded_rectangle(bbox, radius=size // 3, fill=qr_color)
    elif shape == "diamond":
        cx, cy = x + size // 2, y + size // 2
        draw.polygon([(cx, y), (x + size, cy), (cx, y + size), (x, cy)], fill=qr_color)
    else:  # square
        draw.rectangle(bbox, fill=qr_color)


def generate_qr(url, logo_file, logo_ratio_pct, qr_color_hex, bg_color_hex,
                module_drawer_cls, eye_frame_shape, eye_center_shape) -> Image.Image:

    qr_rgb = hex_to_rgb(qr_color_hex)
    bg_rgb  = hex_to_rgb(bg_color_hex)

    # 1. Génération du QR en noir/blanc
    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=BOX_SIZE,
        border=BORDER,
    )
    qr.add_data(url)
    qr.make(fit=True)

    M           = qr.modules_count
    native_size = (M + 2 * BORDER) * BOX_SIZE
    scale       = SIZE / native_size

    qr_bw = qr.make_image(
        image_factory=StyledPilImage,
        module_drawer=module_drawer_cls(),
    ).convert('L')
    qr_bw = qr_bw.resize((SIZE, SIZE), Image.LANCZOS)

    # 2. Colorisation
    front_img  = Image.new('RGB', (SIZE, SIZE), qr_rgb)
    back_img   = Image.new('RGB', (SIZE, SIZE), bg_rgb)
    colored_qr = Image.composite(back_img, front_img, qr_bw)

    # 3. Coins arrondis
    result = Image.new('RGB', (SIZE, SIZE), bg_rgb)
    mask_r = Image.new('L', (SIZE, SIZE), 0)
    ImageDraw.Draw(mask_r).rounded_rectangle([0, 0, SIZE, SIZE], radius=CORNER_R, fill=255)
    result.paste(colored_qr, (0, 0), mask_r)

    # 4. Marqueurs personnalisés (finder patterns)
    bp  = round(BORDER * BOX_SIZE * scale)  # border en px
    ep  = round(7      * BOX_SIZE * scale)  # taille outer du marqueur
    ip  = round(3      * BOX_SIZE * scale)  # taille du centre
    io_ = round(2      * BOX_SIZE * scale)  # offset du centre

    draw = ImageDraw.Draw(result)
    for ex, ey in [
        (bp,             bp),              # haut-gauche
        (SIZE - bp - ep, bp),              # haut-droite
        (bp,             SIZE - bp - ep),  # bas-gauche
    ]:
        draw.rectangle([ex, ey, ex + ep, ey + ep], fill=bg_rgb)  # effacer
        draw_eye_frame(result, ex, ey, ep, qr_rgb, bg_rgb, eye_frame_shape)  # contour
        draw = ImageDraw.Draw(result)  # raffraîchir draw après paste
        draw_eye_center(draw, ex + io_, ey + io_, ip, qr_rgb, eye_center_shape)

    # 5. Logo optionnel
    if logo_file is not None:
        logo_size = int(SIZE * logo_ratio_pct / 100)
        logo = Image.open(logo_file).convert('RGBA').resize((logo_size, logo_size), Image.LANCZOS)
        lx = (SIZE - logo_size) // 2
        ly = (SIZE - logo_size) // 2
        pad = 12

        circle_mask = Image.new('L', (SIZE, SIZE), 0)
        ImageDraw.Draw(circle_mask).ellipse(
            [lx - pad, ly - pad, lx + logo_size + pad, ly + logo_size + pad],
            fill=255,
        )
        result.paste(Image.new('RGB', (SIZE, SIZE), (255, 255, 255)), (0, 0), circle_mask)

        logo_mask = Image.new('L', (logo_size, logo_size), 0)
        ImageDraw.Draw(logo_mask).ellipse([0, 0, logo_size, logo_size], fill=255)
        result.paste(logo.convert('RGB'), (lx, ly), logo_mask)

    return result


# ─────────────────────────────────────────────
# HELPER — boutons de téléchargement (réutilisable)
# ─────────────────────────────────────────────
def render_download_buttons(img: Image.Image, prefix: str) -> None:
    """Affiche le slider de taille + 4 boutons de téléchargement."""
    import base64
    export_size = st.select_slider(
        "Taille de l'export",
        options=[200, 300, 400, 500, 600, 700, 800, 900, 1000,
                 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900, 2000],
        value=600,
        format_func=lambda v: f"{v} × {v} px",
        key=f"export_size_{prefix}",
    )
    export_img = img.resize((export_size, export_size), Image.LANCZOS)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    buf_png = io.BytesIO()
    export_img.save(buf_png, format="PNG", dpi=(300, 300))
    buf_png.seek(0)

    buf_jpg = io.BytesIO()
    export_img.convert("RGB").save(buf_jpg, format="JPEG", quality=95, dpi=(300, 300))
    buf_jpg.seek(0)

    buf_pdf = io.BytesIO()
    export_img.convert("RGB").save(buf_pdf, format="PDF", resolution=300)
    buf_pdf.seek(0)

    png_b64 = base64.b64encode(buf_png.getvalue()).decode()
    buf_png.seek(0)
    svg_content = (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{export_size}" height="{export_size}">'
        f'<image href="data:image/png;base64,{png_b64}" '
        f'width="{export_size}" height="{export_size}"/>'
        f'</svg>'
    )
    buf_svg = io.BytesIO(svg_content.encode())

    dl1, dl2, dl3, dl4 = st.columns(4)
    with dl1:
        st.download_button("⬇ PNG", data=buf_png, file_name=f"{prefix}_{ts}.png",
                           mime="image/png", use_container_width=True, type="primary",
                           key=f"dl_png_{prefix}")
    with dl2:
        st.download_button("⬇ JPG", data=buf_jpg, file_name=f"{prefix}_{ts}.jpg",
                           mime="image/jpeg", use_container_width=True, type="primary",
                           key=f"dl_jpg_{prefix}")
    with dl3:
        st.download_button("⬇ SVG", data=buf_svg, file_name=f"{prefix}_{ts}.svg",
                           mime="image/svg+xml", use_container_width=True, type="primary",
                           key=f"dl_svg_{prefix}")
    with dl4:
        st.download_button("⬇ PDF", data=buf_pdf, file_name=f"{prefix}_{ts}.pdf",
                           mime="application/pdf", use_container_width=True, type="primary",
                           key=f"dl_pdf_{prefix}")


# ─────────────────────────────────────────────
# LAYOUT — deux onglets
# ─────────────────────────────────────────────
tab1, tab2 = st.tabs(["🔗  QR Code URL / Texte", "💼  Carte de visite pro"])


# ══════════════════════════════════════════════
# ONGLET 1 — QR Code classique
# ══════════════════════════════════════════════
with tab1:
    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        st.subheader("Contenu")
        url = st.text_input(
            "Texte ou lien à encoder",
            value="",
            placeholder="https://",
            key="url_tab1",
        )

        st.subheader("Logo")
        logo_file  = st.file_uploader("Charger un logo (optionnel)",
                                      type=["png","jpg","jpeg","webp"], key="logo_tab1")
        logo_ratio = st.slider("Taille du logo (% du QR)", 10, 35, 22, 1, key="logo_ratio_tab1")

        st.subheader("Personnalisation")
        qr_shape   = st.selectbox("Forme des modules",     list(QR_SHAPES.keys()),
                                  index=1, key="shape_tab1")
        eye_frame  = st.selectbox("Contour des marqueurs", list(EYE_FRAME_SHAPES.keys()),
                                  index=0, key="eye_frame_tab1")
        eye_center = st.selectbox("Centre des marqueurs",  list(EYE_CENTER_SHAPES.keys()),
                                  index=0, key="eye_center_tab1")

        c1, c2 = st.columns(2)
        with c1:
            qr_color = st.color_picker("Couleur QR",   "#000000", key="qr_color_tab1")
        with c2:
            bg_color = st.color_picker("Couleur fond", "#FFFFFF",  key="bg_color_tab1")

        generate = st.button("Générer le QR Code", type="primary",
                             use_container_width=True, key="gen_tab1")

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
                            eye_frame_shape=EYE_FRAME_SHAPES[eye_frame],
                            eye_center_shape=EYE_CENTER_SHAPES[eye_center],
                        )
                        st.session_state["qr_img"] = img
                    except Exception as e:
                        st.error(f"Erreur : {e}")

        if "qr_img" in st.session_state:
            img = st.session_state["qr_img"]
            col_pad1, col_img, col_pad2 = st.columns([1, 2, 1])
            with col_img:
                st.image(img, use_container_width=True)
            render_download_buttons(img, "QR")
        else:
            st.info("Le QR code apparaîtra ici après génération.")


# ══════════════════════════════════════════════
# ONGLET 2 — Carte de visite (vCard 3.0)
# ══════════════════════════════════════════════
with tab2:
    col_form, col_preview = st.columns([1, 1], gap="large")

    with col_form:
        st.subheader("Informations")
        vc_prenom   = st.text_input("Prénom",         placeholder="Jean",                    key="vc_prenom")
        vc_nom      = st.text_input("Nom",             placeholder="Dupont",                  key="vc_nom")
        vc_email    = st.text_input("Email",           placeholder="jean@exemple.com",        key="vc_email")
        vc_tel      = st.text_input("Téléphone",       placeholder="+33 6 00 00 00 00",       key="vc_tel")
        vc_linkedin = st.text_input("LinkedIn",        placeholder="https://linkedin.com/in/…", key="vc_linkedin")
        vc_x        = st.text_input("X (Twitter)",     placeholder="https://x.com/…",         key="vc_x")
        vc_site     = st.text_input("Site web",        placeholder="https://…",               key="vc_site")
        vc_bio      = st.text_area("Bio (quelques mots)",
                                   placeholder="Développeur passionné par l'IA…",
                                   max_chars=200, key="vc_bio")

        st.subheader("Logo / Photo")
        vc_logo       = st.file_uploader("Image (optionnel)",
                                         type=["png","jpg","jpeg","webp"], key="vc_logo")
        vc_logo_ratio = st.slider("Taille du logo (% du QR)", 10, 35, 22, 1, key="vc_logo_ratio")

        st.subheader("Personnalisation")
        vc_qr_shape   = st.selectbox("Forme des modules", list(QR_SHAPES.keys()),
                                     index=1, key="vc_shape")
        vc_eye_frame  = st.selectbox("Contour des marqueurs", list(EYE_FRAME_SHAPES.keys()),
                                     index=0, key="vc_eye_frame")
        vc_eye_center = st.selectbox("Centre des marqueurs",  list(EYE_CENTER_SHAPES.keys()),
                                     index=0, key="vc_eye_center")

        c1, c2 = st.columns(2)
        with c1:
            vc_qr_color = st.color_picker("Couleur QR",   "#1A3C5E", key="vc_qr_color")
        with c2:
            vc_bg_color = st.color_picker("Couleur fond", "#FFFFFF",  key="vc_bg_color")

        gen_vcard = st.button("Générer la carte de visite", type="primary",
                              use_container_width=True, key="gen_vcard")

    with col_preview:
        st.subheader("Résultat")

        if gen_vcard:
            if not vc_prenom.strip() and not vc_nom.strip():
                st.error("Veuillez saisir au moins un prénom ou un nom.")
            else:
                lines = [
                    "BEGIN:VCARD",
                    "VERSION:3.0",
                    f"N:{vc_nom.strip()};{vc_prenom.strip()};;;",
                    f"FN:{(vc_prenom.strip() + ' ' + vc_nom.strip()).strip()}",
                ]
                if vc_email.strip():
                    lines.append(f"EMAIL:{vc_email.strip()}")
                if vc_tel.strip():
                    lines.append(f"TEL:{vc_tel.strip()}")
                if vc_site.strip():
                    lines.append(f"URL:{vc_site.strip()}")
                if vc_linkedin.strip():
                    lines.append(f"X-SOCIALPROFILE;type=linkedin:{vc_linkedin.strip()}")
                if vc_x.strip():
                    lines.append(f"X-SOCIALPROFILE;type=twitter:{vc_x.strip()}")
                if vc_bio.strip():
                    lines.append(f"NOTE:{vc_bio.strip()}")
                lines.append("END:VCARD")
                vcard_str = "\r\n".join(lines)

                with st.spinner("Génération..."):
                    try:
                        img_vc = generate_qr(
                            url=vcard_str,
                            logo_file=vc_logo,
                            logo_ratio_pct=vc_logo_ratio,
                            qr_color_hex=vc_qr_color,
                            bg_color_hex=vc_bg_color,
                            module_drawer_cls=QR_SHAPES[vc_qr_shape],
                            eye_frame_shape=EYE_FRAME_SHAPES[vc_eye_frame],
                            eye_center_shape=EYE_CENTER_SHAPES[vc_eye_center],
                        )
                        st.session_state["qr_vcard"] = img_vc
                    except Exception as e:
                        st.error(f"Erreur : {e}")

        if "qr_vcard" in st.session_state:
            img_vc = st.session_state["qr_vcard"]
            col_pad1, col_img, col_pad2 = st.columns([1, 2, 1])
            with col_img:
                st.image(img_vc, use_container_width=True)
            render_download_buttons(img_vc, "vcard")
        else:
            st.info("Le QR code de votre carte de visite apparaîtra ici.")


# ─────────────────────────────────────────────
# COPYRIGHT
# ─────────────────────────────────────────────
st.markdown(
    f"<div style='text-align:center; color:#888; font-size:0.8em; margin-top:2rem;'>"
    f"© {datetime.now().year} By DataSoft Solution"
    "</div>",
    unsafe_allow_html=True,
)