import fitz  # PyMuPDF
import qrcode
import pandas as pd
import os

from PIL import Image

# === CONFIG ===
pdf_path = "utils/invitation.pdf"
font_path = "utils/PTC75F.ttf"
font_size = 15
text_y = 190
qr_x, qr_y = 100, 260
qr_size = 100
csv_path = "guest_list.csv"  # CSV with columns: Table, Name
output_folder = "invites"

# === Ensure output folder exists ===
os.makedirs(output_folder, exist_ok=True)

# === Load font ===
font = fitz.Font(fontfile=font_path)
fontname = font.name
print(f"[INFO] Loaded custom font: {fontname}")

# === Load guest data ===
guests = pd.read_csv(csv_path)
print(f"[INFO] Loaded {len(guests)} guests from CSV.")

for index, row in guests.iterrows():
    table = str(row['Table']).strip()
    name = str(row['Name']).strip()
    qr_text = f"{table} {name}"
    filename = f"{name} - Wedding Invite.pdf"
    output_path = os.path.join(output_folder, filename)

    # === Open PDF fresh for each guest ===
    doc = fitz.open(pdf_path)

    # === Use accurate text width for proper centering ===
    page = doc[1]
    font = fitz.Font(fontfile=font_path)
    text_width = font.text_length(name, fontsize=font_size)
    x_centered = (page.rect.width - text_width) / 2

    # === Insert Name on Page 2 ===
    page = doc[1]
    fontname = f'{page.insert_font(fontfile=font_path)}'
    page.insert_text(
        (x_centered, text_y),
        name,
        fontname=fontname,
        fontfile=font_path,
        fontsize=font_size,
        color=(0, 0, 0),
        overlay=True
    )
    print(f"[OK] Inserted name for {name} on page 2.")

    # === Generate QR Code ===
    qr_img = qrcode.make(qr_text)
    qr_img_path = "qr_temp.png"
    qr_img.save(qr_img_path)

    # === Insert QR Code on Page 3 ===
    qr_page = doc[2]
    qr_rect = fitz.Rect(qr_x, qr_y, qr_x + qr_size, qr_y + qr_size)
    qr_page.insert_image(qr_rect, filename=qr_img_path, overlay=True)
    print(f"[OK] Inserted QR for {name} on page 3.")

    # === Save personalized PDF ===
    doc.save(output_path)
    doc.close()
    print(f"[DONE] Saved: {output_path}")

    # === Clean up temporary QR image ===
    if os.path.exists(qr_img_path):
        os.remove(qr_img_path)

print("[ALL DONE] All invites generated.")
