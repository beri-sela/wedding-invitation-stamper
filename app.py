import tkinter as tk
from tkinter import ttk, filedialog, colorchooser, scrolledtext
import threading
import os

PREVIEW_W = 360  # px width of the live preview panel

# === DEFAULTS (mirrors stamp_invites.py CONFIG) ===
DEFAULTS = {
    "pdf_path":      "utils/invitation.pdf",
    "font_path":     "utils/PTC75F.ttf",
    "csv_path":      "guest_list.csv",
    "output_folder": "invites",
    "page_text":     1,   # 0-indexed page for name text
    "font_size":     12,
    "text_y":        108,
    "text_color":    "#000000",
    "page_qr":       1,   # 0-indexed page for QR code
    "qr_x":          118,
    "qr_y":          333,
    "qr_size":       63,
    "qr_fg_color":   "#000000",
    "qr_bg_color":   "#ffffff",
}


# ── helpers ───────────────────────────────────────────────────────────────────

def hex_to_rgb_float(hex_color):
    """#rrggbb → (r, g, b) floats in [0, 1] for PyMuPDF."""
    h = hex_color.lstrip("#")
    return tuple(int(h[i:i+2], 16) / 255.0 for i in (0, 2, 4))


# ── stamping logic ────────────────────────────────────────────────────────────

def _make_qr_transparent(pil_img, bg_hex):
    """Replace all pixels matching bg_hex with alpha=0."""
    from PIL import Image
    rgba = pil_img.convert("RGBA")
    h    = bg_hex.lstrip("#")
    bg   = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
    data = rgba.getdata()
    rgba.putdata([(r, g, b, 0) if (r, g, b) == bg else (r, g, b, a) for r, g, b, a in data])
    return rgba


def run_stamper(config, log):
    import fitz
    import qrcode
    import pandas as pd
    import io

    try:
        pdf_path         = config["pdf_path"]
        font_path        = config["font_path"]
        font_size        = config["font_size"]
        text_y           = config["text_y"]
        text_color       = hex_to_rgb_float(config["text_color"])
        page_text        = config["page_text"]
        qr_x             = config["qr_x"]
        qr_y             = config["qr_y"]
        qr_size          = config["qr_size"]
        qr_fg_color      = config["qr_fg_color"]
        qr_bg_color      = config["qr_bg_color"]
        qr_bg_transparent = config.get("qr_bg_transparent", False)
        page_qr          = config["page_qr"]
        csv_path      = config["csv_path"]
        output_folder = config["output_folder"]

        os.makedirs(output_folder, exist_ok=True)

        font = fitz.Font(fontfile=font_path)
        log(f"[INFO] Loaded font: {font.name}")

        guests = pd.read_csv(csv_path)
        log(f"[INFO] Loaded {len(guests)} guests from {csv_path}")

        for _, row in guests.iterrows():
            table = str(row["Table"]).strip()
            name  = str(row["Name"]).strip()
            qr_text     = f"{table} {name}"
            output_path = os.path.join(output_folder, f"{name} - Wedding Invite.pdf")

            doc  = fitz.open(pdf_path)
            page = doc[page_text]

            font       = fitz.Font(fontfile=font_path)
            text_width = font.text_length(name, fontsize=font_size)
            x_centered = (page.rect.width - text_width) / 2
            fontname   = f"{page.insert_font(fontfile=font_path)}"

            page.insert_text(
                (x_centered, text_y),
                name,
                fontname=fontname,
                fontfile=font_path,
                fontsize=font_size,
                color=text_color,
                overlay=True,
            )
            log(f"[OK] Name inserted for {name}")

            qr = qrcode.QRCode()
            qr.add_data(qr_text)
            qr.make(fit=True)
            qr_pil      = qr.make_image(fill_color=qr_fg_color, back_color=qr_bg_color)
            qr_img_path = "qr_temp.png"
            if qr_bg_transparent:
                buf = io.BytesIO()
                qr_pil.save(buf, format="PNG")
                buf.seek(0)
                from PIL import Image as _PilImage
                rgba = _make_qr_transparent(_PilImage.open(buf), qr_bg_color)
                rgba.save(qr_img_path, format="PNG")
            else:
                qr_pil.save(qr_img_path)

            qr_rect = fitz.Rect(qr_x, qr_y, qr_x + qr_size, qr_y + qr_size)
            doc[page_qr].insert_image(qr_rect, filename=qr_img_path, overlay=True)
            log(f"[OK] QR inserted for {name}")

            doc.save(output_path)
            doc.close()
            log(f"[DONE] {output_path}")

            if os.path.exists(qr_img_path):
                os.remove(qr_img_path)

        log("[ALL DONE] All invites generated.")

    except Exception as exc:
        log(f"[ERROR] {exc}")


# ── UI ────────────────────────────────────────────────────────────────────────

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Wedding Invitation Stamper")
        self.resizable(True, True)
        self._preview_job = None
        self._preview_img = None   # hold reference to avoid GC
        self._build()
        self._schedule_preview()

    # ── layout ────────────────────────────────────────────────────────────────

    def _build(self):
        P = dict(padx=6, pady=3)

        # ── top row: controls (left) | preview (right) ──
        top = ttk.Frame(self)
        top.grid(row=0, column=0, sticky="nsew")
        top.columnconfigure(1, weight=1)

        ctrl = ttk.Frame(top)
        ctrl.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)

        # Files
        f = ttk.LabelFrame(ctrl, text="Files", padding=8)
        f.grid(row=0, column=0, columnspan=2, sticky="ew", **P)
        self.v_pdf    = self._file_row(f, "Invite PDF:",  DEFAULTS["pdf_path"],      0, True,  [("PDF", "*.pdf")])
        self.v_font   = self._file_row(f, "Font File:",   DEFAULTS["font_path"],     1, True,  [("Fonts", "*.ttf *.otf")])
        self.v_csv    = self._file_row(f, "CSV File:",    DEFAULTS["csv_path"],      2, True,  [("CSV", "*.csv")])
        self.v_outdir = self._file_row(f, "Output Dir:",  DEFAULTS["output_folder"], 3, False, None)

        # Text & QR side by side
        mid = ttk.Frame(ctrl)
        mid.grid(row=1, column=0, columnspan=2, sticky="ew")

        t = ttk.LabelFrame(mid, text="Text Settings", padding=8)
        t.grid(row=0, column=0, sticky="nsew", **P)
        self.v_page_text  = self._spin_row(t, "Page (0-idx):", DEFAULTS["page_text"], 0,  0,  100)
        self.v_font_size  = self._spin_row(t, "Font Size:",    DEFAULTS["font_size"], 1,  1,  500)
        self.v_text_y     = self._spin_row(t, "Text Y:",       DEFAULTS["text_y"],    2,  0, 5000)
        self.v_text_color = self._color_row(t, "Text Color:",  DEFAULTS["text_color"], 3)

        q = ttk.LabelFrame(mid, text="QR Code Settings", padding=8)
        q.grid(row=0, column=1, sticky="nsew", **P)
        self.v_page_qr     = self._spin_row(q, "Page (0-idx):", DEFAULTS["page_qr"],     0,  0,  100)
        self.v_qr_x        = self._spin_row(q, "QR X:",         DEFAULTS["qr_x"],        1,  0, 5000)
        self.v_qr_y        = self._spin_row(q, "QR Y:",         DEFAULTS["qr_y"],        2,  0, 5000)
        self.v_qr_size     = self._spin_row(q, "QR Size:",      DEFAULTS["qr_size"],     3,  1, 5000)
        self.v_qr_fg_color = self._color_row(q, "QR Color:",    DEFAULTS["qr_fg_color"], 4)

        # QR BG Color row with optional transparency toggle
        ttk.Label(q, text="QR BG Color:").grid(row=5, column=0, sticky="w", padx=4, pady=2)
        self.v_qr_bg_color  = tk.StringVar(value=DEFAULTS["qr_bg_color"])
        self._qr_bg_preview = tk.Label(q, bg=DEFAULTS["qr_bg_color"], width=4,
                                       relief="solid", borderwidth=1)
        self._qr_bg_preview.grid(row=5, column=1, sticky="w", padx=4, pady=2)
        self._qr_bg_pick = ttk.Button(q, text="Pick",
                                      command=lambda: self._pick_qr_bg())
        self._qr_bg_pick.grid(row=5, column=2, padx=4, pady=2)
        self.v_qr_bg_transparent = tk.BooleanVar(value=False)
        ttk.Checkbutton(q, text="Transparent", variable=self.v_qr_bg_transparent,
                        command=self._toggle_qr_bg).grid(row=5, column=3, padx=4, pady=2)

        # Generate
        self.btn = ttk.Button(ctrl, text="Generate Invites", command=self._generate)
        self.btn.grid(row=2, column=0, columnspan=2, pady=10)

        # ── Live Preview (right panel) ──
        pf = ttk.LabelFrame(top, text="Live Preview", padding=4)
        pf.grid(row=0, column=1, sticky="nsew", padx=4, pady=4)

        sel = ttk.Frame(pf)
        sel.pack(fill="x", pady=(0, 4))
        ttk.Label(sel, text="Show:").pack(side="left")
        self.v_which = tk.StringVar(value="text")
        ttk.Radiobutton(sel, text="Text page", variable=self.v_which, value="text",
                        command=self._schedule_preview).pack(side="left", padx=6)
        ttk.Radiobutton(sel, text="QR page",   variable=self.v_which, value="qr",
                        command=self._schedule_preview).pack(side="left", padx=6)

        self.preview_lbl = ttk.Label(pf, text="Waiting for preview…",
                                     anchor="center", justify="center", width=PREVIEW_W // 7)
        self.preview_lbl.pack(expand=True, fill="both")

        # ── Log ──
        lf = ttk.LabelFrame(self, text="Log", padding=8)
        lf.grid(row=1, column=0, sticky="nsew", padx=8, pady=4)
        self.log_w = scrolledtext.ScrolledText(lf, width=80, height=10, state="disabled")
        self.log_w.pack(fill="both", expand=True)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # Traces → live preview
        for v in (self.v_pdf, self.v_font, self.v_page_text, self.v_font_size,
                  self.v_text_y, self.v_text_color, self.v_page_qr,
                  self.v_qr_x, self.v_qr_y, self.v_qr_size):
            v.trace_add("write", lambda *_: self._schedule_preview())

    # ── widget builders ───────────────────────────────────────────────────────

    def _file_row(self, parent, label, default, row, is_file, filetypes):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=4, pady=2)
        var = tk.StringVar(value=default)
        ttk.Entry(parent, textvariable=var, width=40).grid(row=row, column=1, padx=4, pady=2)
        if is_file:
            cmd = lambda v=var, ft=filetypes: v.set(
                filedialog.askopenfilename(filetypes=ft) or v.get()
            )
        else:
            cmd = lambda v=var: v.set(filedialog.askdirectory() or v.get())
        ttk.Button(parent, text="Browse", command=cmd).grid(row=row, column=2, padx=4, pady=2)
        return var

    def _spin_row(self, parent, label, default, row, lo, hi):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=4, pady=2)
        var = tk.IntVar(value=default)
        ttk.Spinbox(parent, from_=lo, to=hi, textvariable=var, width=8).grid(
            row=row, column=1, sticky="w", padx=4, pady=2
        )
        return var

    def _color_row(self, parent, label, default, row):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=4, pady=2)
        var     = tk.StringVar(value=default)
        preview = tk.Label(parent, bg=default, width=4, relief="solid", borderwidth=1)
        preview.grid(row=row, column=1, sticky="w", padx=4, pady=2)

        def pick(v=var, p=preview):
            result = colorchooser.askcolor(color=v.get())[1]
            if result:
                v.set(result)
                p.config(bg=result)

        ttk.Button(parent, text="Pick", command=pick).grid(row=row, column=2, padx=4, pady=2)
        return var

    def _pick_qr_bg(self):
        result = colorchooser.askcolor(color=self.v_qr_bg_color.get())[1]
        if result:
            self.v_qr_bg_color.set(result)
            self._qr_bg_preview.config(bg=result)

    def _toggle_qr_bg(self):
        transparent = self.v_qr_bg_transparent.get()
        state = "disabled" if transparent else "normal"
        self._qr_bg_preview.config(state=state)
        self._qr_bg_pick.config(state=state)
        self._schedule_preview()

    # ── preview ───────────────────────────────────────────────────────────────

    def _schedule_preview(self, *_):
        if self._preview_job:
            self.after_cancel(self._preview_job)
        self._preview_job = self.after(300, self._launch_preview_thread)

    def _launch_preview_thread(self):
        self._preview_job = None
        # Snapshot values on the main thread before handing off
        cfg = {
            "pdf_path":   self.v_pdf.get(),
            "font_path":  self.v_font.get(),
            "page_text":  self.v_page_text.get(),
            "font_size":  self.v_font_size.get(),
            "text_y":     self.v_text_y.get(),
            "text_color": self.v_text_color.get(),
            "page_qr":    self.v_page_qr.get(),
            "qr_x":              self.v_qr_x.get(),
            "qr_y":              self.v_qr_y.get(),
            "qr_size":           self.v_qr_size.get(),
            "qr_bg_transparent": self.v_qr_bg_transparent.get(),
            "which":             self.v_which.get(),
        }
        threading.Thread(target=self._render_preview, args=(cfg,), daemon=True).start()

    def _render_preview(self, cfg):
        """Runs in a background thread; posts result back to main thread."""
        try:
            import fitz
            from PIL import Image, ImageDraw, ImageFont

            pdf_path = cfg["pdf_path"]
            if not os.path.isfile(pdf_path):
                self.after(0, lambda: self.preview_lbl.config(text="PDF not found", image=""))
                return

            which    = cfg["which"]
            page_idx = cfg["page_text"] if which == "text" else cfg["page_qr"]
            scale    = 1.5   # render resolution multiplier

            doc = fitz.open(pdf_path)
            if page_idx >= len(doc):
                n = len(doc)
                doc.close()
                self.after(0, lambda: self.preview_lbl.config(
                    text=f"Page {page_idx} out of range\n(PDF has {n} pages)", image=""))
                return

            pix = doc[page_idx].get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples).convert("RGBA")
            doc.close()

            draw = ImageDraw.Draw(img, "RGBA")

            # ── text overlay (shown on its page) ──
            if which == "text" or cfg["page_text"] == page_idx:
                fs = int(cfg["font_size"] * scale)
                try:
                    pil_font = ImageFont.truetype(cfg["font_path"], fs)
                except Exception:
                    pil_font = ImageFont.load_default()

                placeholder = "Guest Name"
                bbox  = draw.textbbox((0, 0), placeholder, font=pil_font)
                tw    = bbox[2] - bbox[0]
                tx    = (img.width - tw) / 2
                asc, dsc = pil_font.getmetrics()
                # fitz text_y is the baseline; PIL draws from the top
                ty = cfg["text_y"] * scale - asc
                # highlight band
                draw.rectangle([tx - 2, ty, tx + tw + 2, ty + asc + dsc],
                               fill=(255, 220, 0, 90))
                draw.text((tx, ty), placeholder, font=pil_font, fill=cfg["text_color"])

            # ── QR overlay (shown on its page) ──
            if which == "qr" or cfg["page_qr"] == page_idx:
                qx = cfg["qr_x"]   * scale
                qy = cfg["qr_y"]   * scale
                qs = cfg["qr_size"] * scale
                if not cfg.get("qr_bg_transparent"):
                    draw.rectangle([qx, qy, qx + qs, qy + qs], fill=(220, 0, 0, 50))
                draw.rectangle([qx, qy, qx + qs, qy + qs], outline=(200, 0, 0, 255), width=2)
                try:
                    lbl_font = ImageFont.truetype(cfg["font_path"], max(10, int(11 * scale)))
                except Exception:
                    lbl_font = ImageFont.load_default()
                draw.text((qx + 3, qy + 3), "QR", font=lbl_font, fill=(180, 0, 0, 255))

            # Fit to preview width
            ratio = PREVIEW_W / img.width
            new_h = int(img.height * ratio)
            img   = img.convert("RGB").resize((PREVIEW_W, new_h), Image.LANCZOS)

            self.after(0, self._show_preview, img)

        except Exception as exc:
            msg = f"Preview error:\n{exc}"
            self.after(0, lambda m=msg: self.preview_lbl.config(text=m, image=""))

    def _show_preview(self, pil_img):
        from PIL import ImageTk
        photo = ImageTk.PhotoImage(pil_img)
        self._preview_img = photo          # prevent garbage collection
        self.preview_lbl.config(image=photo, text="")

    # ── log ───────────────────────────────────────────────────────────────────

    def _append_log(self, msg):
        self.log_w.config(state="normal")
        self.log_w.insert("end", msg + "\n")
        self.log_w.see("end")
        self.log_w.config(state="disabled")

    # ── generate ──────────────────────────────────────────────────────────────

    def _generate(self):
        self.btn.config(state="disabled")
        self.log_w.config(state="normal")
        self.log_w.delete("1.0", "end")
        self.log_w.config(state="disabled")

        config = {
            "pdf_path":      self.v_pdf.get(),
            "font_path":     self.v_font.get(),
            "csv_path":      self.v_csv.get(),
            "output_folder": self.v_outdir.get(),
            "page_text":     self.v_page_text.get(),
            "font_size":     self.v_font_size.get(),
            "text_y":        self.v_text_y.get(),
            "text_color":    self.v_text_color.get(),
            "page_qr":       self.v_page_qr.get(),
            "qr_x":          self.v_qr_x.get(),
            "qr_y":          self.v_qr_y.get(),
            "qr_size":       self.v_qr_size.get(),
            "qr_fg_color":        self.v_qr_fg_color.get(),
            "qr_bg_color":        self.v_qr_bg_color.get(),
            "qr_bg_transparent":  self.v_qr_bg_transparent.get(),
        }

        def task():
            run_stamper(config, lambda msg: self.after(0, self._append_log, msg))
            self.after(0, lambda: self.btn.config(state="normal"))

        threading.Thread(target=task, daemon=True).start()


if __name__ == "__main__":
    App().mainloop()
