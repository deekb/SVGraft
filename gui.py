import threading
import dearpygui.dearpygui as dpg

from svgraft.cli import split_svg
from svgraft.config import ProcessConfig


# -----------------------------
# STATE (THREAD SAFE MODEL)
# -----------------------------
state = {
    "file": None,
    "output": "output.pdf",

    "page_w": 8.5,
    "page_h": 11.0,
    "margin": 7.0,

    "scale": 1.0,
    "pages_wide": None,
    "pages_tall": None,

    "status": "Idle",
    "running": False,

    # UI sync flag
    "dirty": True,
}


# -----------------------------
# UI SYNC (MAIN THREAD ONLY)
# -----------------------------
def ui_sync():
    if state["dirty"]:
        if dpg.does_item_exist("status_text"):
            dpg.set_value("status_text", state["status"])

        if dpg.does_item_exist("run_btn"):
            dpg.configure_item("run_btn", enabled=not state["running"])

        state["dirty"] = False


# -----------------------------
# FILE LOAD
# -----------------------------
def load_file(sender, app_data):
    state["file"] = app_data["file_path_name"]
    state["status"] = f"Loaded: {state['file']}"
    state["dirty"] = True


# -----------------------------
# WORKER (NO DPG CALLS HERE)
# -----------------------------
def worker():
    try:
        state["running"] = True
        state["status"] = "Processing..."
        state["dirty"] = True

        config = ProcessConfig(
            input_file=state["file"],
            output_file=state["output"],
            page_width_in=state["page_w"],
            page_height_in=state["page_h"],
            margin_mm=state["margin"],
            scale_factor=state["scale"],
            pages_wide=state["pages_wide"],
            pages_tall=state["pages_tall"],
            optimize_tile_orientation=True,
            border_stroke_mm=0.3,
            corner_triangle_size_mm=2.0,
        )

        with open(state["file"], "rb") as f:
            split_svg(f, config)

        state["status"] = "Done ✔ PDF generated"
        state["dirty"] = True

    except Exception as e:
        state["status"] = f"Error: {e}"
        state["dirty"] = True

    finally:
        state["running"] = False
        state["dirty"] = True


# -----------------------------
# RUN
# -----------------------------
def run_svgraft():
    if state["running"]:
        state["status"] = "Already running"
        state["dirty"] = True
        return

    if not state["file"]:
        state["status"] = "No file selected"
        state["dirty"] = True
        return

    threading.Thread(target=worker, daemon=True).start()


# -----------------------------
# UI
# -----------------------------
def build_ui():

    with dpg.window(tag="main", label="SVGraft Studio", width=980, height=650):

        dpg.add_text("SVGraft Studio")
        dpg.add_separator()

        # File row
        with dpg.group(horizontal=True):
            dpg.add_button(label="Load File", callback=lambda: dpg.show_item("file_dialog"))
            dpg.add_input_text(
                label="Output",
                default_value=state["output"],
                callback=lambda s, a: state.update({"output": a}),
            )

        dpg.add_separator()

        dpg.add_text("Page Settings")

        dpg.add_input_float(
            label="Page Width (in)",
            default_value=state["page_w"],
            callback=lambda s, a: state.update({"page_w": float(a)}),
        )

        dpg.add_input_float(
            label="Page Height (in)",
            default_value=state["page_h"],
            callback=lambda s, a: state.update({"page_h": float(a)}),
        )

        dpg.add_input_float(
            label="Margin (mm)",
            default_value=state["margin"],
            callback=lambda s, a: state.update({"margin": float(a)}),
        )

        dpg.add_separator()

        dpg.add_text("Scaling")

        dpg.add_input_float(
            label="Scale factor",
            default_value=state["scale"],
            callback=lambda s, a: state.update({"scale": float(a)}),
        )

        dpg.add_input_int(
            label="Pages wide",
            callback=lambda s, a: state.update({"pages_wide": a if a > 0 else None}),
        )

        dpg.add_input_int(
            label="Pages tall",
            callback=lambda s, a: state.update({"pages_tall": a if a > 0 else None}),
        )

        dpg.add_separator()

        dpg.add_button(label="Generate PDF", tag="run_btn", callback=run_svgraft)

        dpg.add_separator()

        dpg.add_text("Status:")
        dpg.add_text(state["status"], tag="status_text")


# -----------------------------
# FILE DIALOG (SAFE LOCATION)
# -----------------------------
def build_file_dialog():
    with dpg.file_dialog(
        directory_selector=False,
        show=False,
        callback=load_file,
        tag="file_dialog",
        width=700,
        height=400,
    ):
        dpg.add_file_extension(".svg")
        dpg.add_file_extension(".pdf")


# -----------------------------
# MAIN
# -----------------------------
def main():
    dpg.create_context()
    dpg.create_viewport(title="SVGraft Studio", width=980, height=650)

    build_ui()
    build_file_dialog()

    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.set_primary_window("main", True)

    # SAFE UI SYNC LOOP (instead of render callback)
    def loop():
        ui_sync()

    dpg.add_timer(0.05, callback=loop)  # 20 FPS UI sync

    dpg.start_dearpygui()
    dpg.destroy_context()

if __name__ == "__main__":
    main()