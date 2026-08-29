import io
from PIL import Image, ImageEnhance, ImageOps
import streamlit as st

# Check if rembg is available
try:
    from rembg import new_session, remove as remove_bg

    REMBG_AVAILABLE = True
except Exception:
    REMBG_AVAILABLE = False

st.set_page_config(
    page_title="EditEdge Studio", page_icon="📷", layout="wide"
)

# Custom Styling (Premium Dark Theme)
st.markdown(
    """
    <style>
    .stApp { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color: #f8fafc; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: 600; background: linear-gradient(90deg, #3b82f6 0%, #2563eb 100%); color: white; border: none; }
    [data-testid="stImage"] img { border-radius: 12px; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5); }
    [data-testid="stDownloadButton"]>button { background: linear-gradient(90deg, #10b981 0%, #059669 100%); border: none; font-weight: bold; }
    [data-testid="stFileUploader"] { background-color: #1e293b; border: 2px dashed #475569; border-radius: 12px; padding: 15px; }
    </style>
""",
    unsafe_allow_html=True,
)

# --- SESSION STATES INITIALIZATION ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "angle" not in st.session_state:
    st.session_state.angle = 0
if "flip_h" not in st.session_state:
    st.session_state.flip_h = False
if "flip_v" not in st.session_state:
    st.session_state.flip_v = False
if "bg_processed_img" not in st.session_state:
    st.session_state.bg_processed_img = None

# ---------------------------------------------------------
# 1. LOGIN PAGE
# ---------------------------------------------------------
if not st.session_state.logged_in:
    st.title("🔒 EditEdge Studio Login")
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.subheader("Login Credentials")
        user = st.text_input("Username", value="admin")
        pwd = st.text_input("Password", type="password", value="1234")

        if st.button("Login to Editor", type="primary"):
            if user == "admin" and pwd == "1234":
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Invalid Credentials! (Default: admin / 1234)")
    st.button("📞 Admin Support & Help")
    

# ---------------------------------------------------------
# 2. MAIN EDITOR PAGE
# ---------------------------------------------------------
else:
    head_col1, head_col2 = st.columns([4, 1])
    with head_col1:
        st.title("📷 EditEdge Studio Web")
    with head_col2:
        if st.button("Logout 🚪"):
            st.session_state.logged_in = False
            st.session_state.angle = 0
            st.session_state.flip_h = False
            st.session_state.flip_v = False
            st.session_state.bg_processed_img = None
            st.rerun()

    # --- WELCOME BANNER ---
    with st.expander("🚀 Welcome & Features Guide (Click to expand/collapse)"):
        st.write("""
Your lightweight, AI-powered web platform for fast image processing and professional document preparation directly in your browser.

**Key Features & Capabilities:**
* **AI Background Removal:** Instant, high-precision removal powered by optimized ONNX neural models.
* **Passport & ID Studio:** One-click background synthesis for solid white, official blue, or custom color fills.
* **Smart Enhancements:** Real-time controls for brightness, contrast, color saturation, sharpness, and grayscale filters.
* **Aspect Ratio Presets:** Quick cropping presets for 1:1 Square, 3:4 Passport, and 16:9 Banner layouts.
* **Multi-Format Export:** Seamlessly convert and download your images in PNG, JPEG, WEBP, or direct PDF formats.
""")

    # --- MAIN SCREEN CENTRE FILE UPLOADER ---
    uploaded_file = st.file_uploader(
        "📂 Upload Image Here to Start Editing",
        type=["png", "jpg", "jpeg", "webp"],
        key="main_file_uploader",
    )

    if uploaded_file:
        raw_img = Image.open(uploaded_file).convert("RGB")

        # Layout Split: Desktop me side-by-side, Mobile me vertical stacked
        col_preview, col_controls = st.columns([1, 1])

        # --- CONTROLS SECTION (IN MAIN PAGE) ---
        with col_controls:
            st.subheader("⚙️ Edit Controls")

            tab1, tab2, tab3 = st.tabs(
                ["🎛️ Enhancements", "📐 Crop & Rotate", "🤖 AI Tools"]
            )

            with tab1:
                b_col1, b_col2, b_col3 = st.columns(3)
                if b_col1.button("↻ Rotate 90°"):
                    st.session_state.angle = (st.session_state.angle + 90) % 360
                if b_col2.button("↔️ Mirror Flip"):
                    st.session_state.flip_h = not st.session_state.flip_h
                if b_col3.button("↺ Reset All"):
                    st.session_state.angle = 0
                    st.session_state.flip_h = False
                    st.session_state.flip_v = False
                    st.session_state.brightness = 1.0
                    st.session_state.contrast = 1.0
                    st.session_state.saturation = 1.0
                    st.session_state.sharpness = 1.0
                    st.session_state.bg_processed_img = None
                    st.rerun()

                brightness = st.slider(
                    "Brightness",
                    0.1,
                    2.0,
                    st.session_state.get("brightness", 1.0),
                    key="brightness",
                )
                contrast = st.slider(
                    "Contrast",
                    0.1,
                    2.0,
                    st.session_state.get("contrast", 1.0),
                    key="contrast",
                )
                saturation = st.slider(
                    "Color Saturation",
                    0.0,
                    2.0,
                    st.session_state.get("saturation", 1.0),
                    key="saturation",
                )
                sharpness = st.slider(
                    "Sharpness",
                    0.0,
                    3.0,
                    st.session_state.get("sharpness", 1.0),
                    key="sharpness",
                )

            with tab2:
                crop_option = st.selectbox(
                    "Preset Aspect Ratio Crop",
                    [
                        "Original (No Crop)",
                        "1:1 Square",
                        "3:4 Passport",
                        "16:9 Banner",
                    ],
                )
                is_grayscale = st.checkbox("Black & White (Grayscale)")

            with tab3:
                bg_color_hex = "#FFFFFF"
                apply_color_bg = False

                if REMBG_AVAILABLE:
                    if st.button("Remove Background (AI) ⚡"):
                        with st.spinner("AI Processing... Please wait..."):
                            try:
                                temp_img = raw_img.copy()
                                temp_img.thumbnail((800, 800))
                                session = new_session("u2netp")
                                st.session_state.bg_processed_img = remove_bg(
                                    temp_img, session=session
                                )
                                st.success("Background Removed!")
                            except Exception as e:
                                st.error(f"Error: {e}")

                    if st.session_state.bg_processed_img is not None:
                        bg_option = st.radio(
                            "Select BG:",
                            [
                                "Transparent (PNG)",
                                "Solid White",
                                "Passport Blue",
                                "Custom Color",
                            ],
                        )
                        if bg_option == "Solid White":
                            apply_color_bg = True
                            bg_color_hex = "#FFFFFF"
                        elif bg_option == "Passport Blue":
                            apply_color_bg = True
                            bg_color_hex = "#00BFFF"
                        elif bg_option == "Custom Color":
                            apply_color_bg = True
                            bg_color_hex = st.color_picker(
                                "Pick Custom BG Color", "#FFFFFF"
                            )

                        if st.button("Restore Original BG"):
                            st.session_state.bg_processed_img = None
                            st.rerun()

        # --- IMAGE PROCESSING ENGINE ---
        if st.session_state.bg_processed_img is not None:
            no_bg_img = st.session_state.bg_processed_img.copy()
            if apply_color_bg:
                hex_val = bg_color_hex.lstrip("#")
                rgb_color = tuple(
                    int(hex_val[i : i + 2], 16) for i in (0, 2, 4)
                )
                solid_bg = Image.new(
                    "RGBA", no_bg_img.size, rgb_color + (255,)
                )
                solid_bg.paste(no_bg_img, (0, 0), no_bg_img)
                edited_img = solid_bg.convert("RGB")
            else:
                edited_img = no_bg_img
        else:
            edited_img = raw_img.copy()

        # Apply Aspect Ratio Crop
        if crop_option != "Original (No Crop)":
            w, h = edited_img.size
            if crop_option == "1:1 Square":
                min_dim = min(w, h)
                edited_img = edited_img.crop((0, 0, min_dim, min_dim))
            elif crop_option == "3:4 Passport":
                new_h = int(w * 4 / 3)
                if new_h <= h:
                    edited_img = edited_img.crop((0, 0, w, new_h))
                else:
                    new_w = int(h * 3 / 4)
                    edited_img = edited_img.crop((0, 0, new_w, h))
            elif crop_option == "16:9 Banner":
                new_h = int(w * 9 / 16)
                if new_h <= h:
                    edited_img = edited_img.crop((0, 0, w, new_h))

        # Apply Rotation & Flips
        if st.session_state.angle != 0:
            edited_img = edited_img.rotate(
                -st.session_state.angle, expand=True
            )
        if st.session_state.flip_h:
            edited_img = ImageOps.mirror(edited_img)

        # Apply Enhancements
        edited_img = ImageEnhance.Brightness(edited_img).enhance(brightness)
        edited_img = ImageEnhance.Contrast(edited_img).enhance(contrast)
        edited_img = ImageEnhance.Color(edited_img).enhance(saturation)
        edited_img = ImageEnhance.Sharpness(edited_img).enhance(sharpness)

        if is_grayscale:
            edited_img = ImageOps.grayscale(edited_img)

        # --- PREVIEW & EXPORT (TOP LEFT PANEL) ---
        with col_preview:
            st.subheader("🖼️ Live Preview")
            st.image(
                edited_img,
                caption=f"Dimensions: {edited_img.width}x{edited_img.height} px",
            )

            st.subheader("🚀 Export Options")
            export_fmt = st.selectbox(
                "Export Format", ["PNG", "JPEG", "PDF", "WEBP"]
            )

            buf = io.BytesIO()
            if export_fmt in ["PDF", "JPEG"]:
                save_img = edited_img.convert("RGB")
                save_img.save(
                    buf,
                    format=export_fmt,
                    resolution=100.0 if export_fmt == "PDF" else None,
                )
            else:
                edited_img.save(buf, format=export_fmt)

            st.download_button(
                label=f"Download {export_fmt}",
                data=buf.getvalue(),
                file_name=f"editedge_output.{export_fmt.lower()}",
                mime=f"image/{export_fmt.lower()}",
                type="primary",
            )
    else:
        st.info(
            "👆 Upload an image using the box above to open the photo editor."
        )

