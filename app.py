import io
from PIL import Image, ImageEnhance
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

# Custom Styling
st.markdown(
    """
    <style>
    .stApp { background-color: #0f172a; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; }
    </style>
""",
    unsafe_allow_html=True,
)

# --- SESSION STATES INITIALIZATION ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "angle" not in st.session_state:
    st.session_state.angle = 0

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
            st.session_state.bg_processed_img = None
            st.rerun()

    # --- SIDEBAR CONTROLS ---
    st.sidebar.header("📂 Step 1: Upload Image")
    uploaded_file = st.sidebar.file_uploader(
        "Choose an Image File", type=["png", "jpg", "jpeg", "webp"]
    )

    if uploaded_file:
        raw_img = Image.open(uploaded_file).convert("RGB")

        st.sidebar.markdown("---")
        st.sidebar.header("⚙️ Step 2: Edit Controls")

        # Rotate & Reset Buttons
        btn_col1, btn_col2 = st.sidebar.columns(2)

        if btn_col1.button("↻ Rotate 90°"):
            st.session_state.angle = (st.session_state.angle + 90) % 360

        if btn_col2.button("↺ Reset All"):
            st.session_state.angle = 0
            st.session_state.brightness = 1.0
            st.session_state.contrast = 1.0
            st.session_state.bg_processed_img = None
            st.rerun()

        # Sliders
        brightness = st.sidebar.slider(
            "Brightness",
            0.1,
            2.0,
            st.session_state.get("brightness", 1.0),
            key="brightness",
        )
        contrast = st.sidebar.slider(
            "Contrast",
            0.1,
            2.0,
            st.session_state.get("contrast", 1.0),
            key="contrast",
        )

        # AI Tools Section
        st.sidebar.markdown("---")
        st.sidebar.header("🤖 AI Tools & Backgrounds")

        bg_color_hex = "#FFFFFF"
        apply_color_bg = False

        if REMBG_AVAILABLE:
            if st.sidebar.button("Remove Background (AI) ⚡"):
                with st.spinner(
                    "AI Processing... (Fast lightweight model loading)..."
                ):
                    try:
                        # Resize slightly for super fast performance
                        temp_img = raw_img.copy()
                        temp_img.thumbnail((800, 800))

                        # Using lightweight u2netp session (~4MB instead of 170MB)
                        session = new_session("u2netp")
                        st.session_state.bg_processed_img = remove_bg(
                            temp_img, session=session
                        )
                        st.success("Background Removed Successfully!")
                    except Exception as e:
                        st.error(f"Background Removal Error: {e}")

            if st.session_state.bg_processed_img is not None:
                st.sidebar.markdown("**Passport / Document BG Color:**")
                bg_option = st.sidebar.radio(
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
                    bg_color_hex = st.sidebar.color_picker(
                        "Pick Custom BG Color", "#FFFFFF"
                    )

                if st.sidebar.button("Restore Original BG"):
                    st.session_state.bg_processed_img = None
                    st.rerun()
        else:
            st.sidebar.warning(
                "AI BG Removal disabled. Please check requirements.txt"
            )

        # --- IMAGE PROCESSING ---
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

        # Apply Rotation
        if st.session_state.angle != 0:
            edited_img = edited_img.rotate(
                -st.session_state.angle, expand=True
            )

        # Apply Brightness & Contrast
        edited_img = ImageEnhance.Brightness(edited_img).enhance(brightness)
        edited_img = ImageEnhance.Contrast(edited_img).enhance(contrast)

        # --- PREVIEW & EXPORT ---
        col_view, col_export = st.columns([3, 1])

        with col_view:
            st.subheader("Live Preview")
            st.image(
                edited_img,
                caption=f"Current Rotation: {st.session_state.angle}°",
            )

        with col_export:
            st.subheader("🚀 Export Options")
            export_fmt = st.selectbox(
                "Export Format", ["PNG", "JPEG", "PDF", "WEBP"]
            )

            buf = io.BytesIO()
            if export_fmt == "PDF":
                pdf_img = edited_img.convert("RGB")
                pdf_img.save(buf, format="PDF", resolution=100.0)
            elif export_fmt == "JPEG":
                jpeg_img = edited_img.convert("RGB")
                jpeg_img.save(buf, format="JPEG")
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
        st.info("👈 Please upload an image from the sidebar to start editing.")

