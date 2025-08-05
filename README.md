# 💌 Wedding Invitation Stamper

This project takes a base PDF wedding invitation and personalizes it for each guest by:

- Adding the guest's **name** to Page 2
- Adding a **QR code** to Page 3 (containing: `Table + Name`)
- Saving each customized invite as a separate PDF in the `invites/` folder

---

## 📂 Folder Structure

```
project-root/
│
├── invites/                   # Output folder for personalized PDFs
├── utils/
│   ├── Nandila Wedding Invitation.pdf  # Original invitation template (3 pages)
│   └── PTC75F.ttf            # Custom font used in the invite
├── guest_list.csv            # CSV file with columns: Table, Name
├── stamp_invites.py          # Main script to generate invites
├── requirements.txt          # Python package dependencies
└── README.md                 # This file
```

---

## 🐍 Requirements

- Python **3.10+** is required  
- All other libraries are listed in `requirements.txt`

### 🔗 Download Python 3.10 or later

[➡️ Download Python 3.10+ from the official site](https://www.python.org/downloads/)

---

## 📦 Install Dependencies

After installing Python 3.10+, install the required packages by running:

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
- `Name`: Full name to be printed and encoded

---

## 🚀 Run the Script

```bash
python stamp_invites.py
```

Each guest will get a **custom invitation PDF** saved inside the `invites/` folder.

---

## 📤 Output Example

```
invites/
├── Mr. John Doe - Wedding Invite.pdf
├── Mrs. Adamou - Moussa Wedding Invite.pdf
├── Col. Gilbert - Fondufe Wedding Invite.pdf
...
```

---

## 🧼 Cleanup

The script will automatically:
- Generate and insert a temporary QR image for each guest
- Delete the QR image after each invite is saved

---

## 📞 Support

For issues or questions, feel free to open an issue or reach out.
