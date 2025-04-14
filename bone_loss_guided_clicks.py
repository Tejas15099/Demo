# 📀 Streamlit Canvas App: Bone Loss % + Grade Estimator (Guided A→B, C, D)
import streamlit as st
import numpy as np
from PIL import Image
from streamlit_drawable_canvas import st_canvas
import cv2

# 📏 Function to calculate distance between two points
def distance(p1, p2):
    return np.linalg.norm(np.array(p1) - np.array(p2))

st.set_page_config(layout="wide")
st.title("🦷 Bone Loss % and Grade Estimator (Canvas Version)")
st.markdown("Click in this order: **1st: CEJ (A), 2nd: Bone Crest (C), 3rd: Apex (D)**.\n\nPhysiologic Bone Level (B) will be automatically calculated 1.5 mm apical to CEJ.")

uploaded_file = st.file_uploader("📤 Upload IOPA Radiograph", type=["png", "jpg", "jpeg"])
age = st.number_input("👴 Enter Patient Age", min_value=1, max_value=120, value=30)

if uploaded_file is not None:
    image = Image.open(uploaded_file).convert("RGB")

    # Sidebar controls
    st.sidebar.header("🛠️ Image Settings")
    canvas_max_width = st.sidebar.slider("Canvas width (px)", min_value=400, max_value=1200, value=600, step=50)
    rotation_angle = st.sidebar.slider("Rotate image (degrees)", min_value=0, max_value=360, value=0, step=90)

    # Apply rotation
    image_rotated = image.rotate(-rotation_angle, expand=True)
    image_np = np.array(image_rotated)

    # Scale image
    scale = canvas_max_width / image_np.shape[1] if image_np.shape[1] > canvas_max_width else 1.0
    h, w = int(image_np.shape[0] * scale), int(image_np.shape[1] * scale)
    resized_image = cv2.resize(image_np, (w, h))
    image_pil_resized = Image.fromarray(resized_image)

    st.markdown("### ✏️ Annotate 3 Points Using the Canvas Below")
    with st.container():
        canvas_result = st_canvas(
            fill_color="rgba(255, 0, 0, 1)",
            stroke_width=10,
            stroke_color="#FF0000",
            background_image=image_pil_resized,
            update_streamlit=True,
            height=h,
            width=w,
            drawing_mode="point",
            key="canvas",
        )

    if canvas_result.json_data is not None:
        points = []
        for obj in canvas_result.json_data["objects"]:
            norm_x = obj["left"]
            norm_y = obj["top"]
            x = int(norm_x)
            y = int(norm_y)
            points.append((x, y))

        if len(points) == 3:
            CEJ = points[0]   # A
            BoneCrest = points[1]  # C
            Apex = points[2]   # D
            pixel_shift = int(h * 0.015)
            PhysioBone = (CEJ[0], CEJ[1] + pixel_shift)  # B

            alpha = distance(PhysioBone, BoneCrest)
            beta = distance(PhysioBone, Apex)

            if beta == 0:
                st.error("❌ Apex too close to physiological bone level")
            else:
                bone_loss_percent = (alpha / beta) * 100
                ratio = bone_loss_percent / age

                if ratio < 0.25:
                    grade = "Grade A (Slow Progression)"
                elif ratio <= 1.0:
                    grade = "Grade B (Moderate Progression)"
                else:
                    grade = "Grade C (Rapid Progression)"

                output_img = resized_image.copy()
                for i, pt in enumerate([CEJ, PhysioBone, BoneCrest, Apex]):
                    cv2.circle(output_img, (int(pt[0]), int(pt[1])), 6, (0, 0, 255), -1)
                    cv2.putText(output_img, chr(65+i), (int(pt[0])+10, int(pt[1])-10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

                with st.container():
                    st.image(output_img, caption="📍 Marked Points (A, B, C, D)", channels="RGB", use_column_width=True)

                st.markdown("---")
                st.markdown(f"**📏 Alpha (B to C):** `{alpha:.2f} px`")
                st.markdown(f"**📏 Beta (B to D):** `{beta:.2f} px`")
                st.markdown(f"**🦷 Bone Loss %:** `{bone_loss_percent:.2f}%`")
                st.markdown(f"**👴 Age:** `{age} years`")
                st.markdown(f"**📉 Bone Loss / Age Ratio:** `{ratio:.2f}`")
                st.markdown(f"**🧠 Suggested Grade:** `{grade}`")
        else:
            st.info(f"🖱️ Click {3 - len(points)} more point(s) in the correct order (A, C, D)")

else:
    st.warning("Please upload an image to begin.")
