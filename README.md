# 💌 Wedding Invitation Stamper

This project takes a base PDF wedding invitation and personalizes it for each guest by:

- Adding the guest's **name** to a chosen page (centered, custom font & color)
- Adding a **QR code** to a chosen page (containing: `Table + Name`)
- Saving each customized invite as a separate PDF in the output folder

A **Tkinter GUI** lets you configure every setting visually with a live PDF preview before generating.

---

## 📂 Folder Structure

```
project-root/
│
├── invites/                   # Output folder for personalized PDFs
├── utils/
│   ├── invitation.pdf        # Original invitation template
│   └── PTC75F.ttf            # Custom font used in the invite
├── guest_list.csv            # CSV file with columns: Table, Name
├── app.py                    # GUI application
├── requirements.txt          # Python package dependencies
└── README.md                 # This file
```

---

## 🐍 Requirements

- Python **3.10+** (tkinter is included with Python on Windows & macOS)
- All other libraries are listed in `requirements.txt`

### 🔗 Download Python 3.10 or later

[➡️ Download Python 3.10+ from the official site](https://www.python.org/downloads/)

> **Linux users:** If tkinter is missing, run `sudo apt install python3-tk`

---

## 📦 Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 🧾 CSV Format

Create a `guest_list.csv` file in the root directory with the following format:

```csv
Table,Name
Bride,Mr. John Doe
Groom,Mrs. Adamou Moussa
Family,Col. Gilbert Fondufe
...
```

- `Table`: Which side or group they belong to (e.g. "Bride", "Groom", "Family")
- `Name`: Full name to be printed and encoded in the QR code

---

## 🚀 Run the App

```bash
python app.py
```

---

## 🖥️ GUI Overview

| Section | Settings |
|---|---|
| **Files** | Invite PDF, Font file, CSV file, Output folder |
| **Text Settings** | Page (0-indexed), Font size, Text Y position, Text color |
| **QR Code Settings** | Page (0-indexed), X/Y position, Size, QR color, Background color (with optional transparency) |
| **Live Preview** | Renders the actual PDF page with overlaid name and QR position indicators; updates as you adjust settings |
| **Log** | Per-guest progress output during generation |

### Live Preview
- The **yellow highlight** shows where the guest name will appear using the real font.
- The **red box** shows the QR code position and size.
- Toggle between **Text page** and **QR page** views using the radio buttons.

---

## 📤 Output Example

```
invites/
├── Mr. John Doe - Wedding Invite.pdf
├── Mrs. Adamou Moussa - Wedding Invite.pdf
├── Col. Gilbert Fondufe - Wedding Invite.pdf
...
```

---

## 🧼 Cleanup

The app automatically generates and deletes a temporary QR image for each guest after each invite is saved.

---

## 📞 Support

For issues or questions, feel free to open an issue or reach out.
