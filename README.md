# What I'm Buying (MVP)

Simple MVP to parse Brazilian NFC-e public pages from QR URLs and normalize invoice items.

## What it does

- Accepts an NFC-e QR URL (already scanned from receipt QR code).
- Fetches the public page HTML.
- Parses invoice items with resilient table heuristics.
- Stores invoice + item history in SQLite.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Parse an invoice from QR URL:

```bash
python -m src.what_im_buying.cli parse-url \
  "https://www.nfce.fazenda.sp.gov.br/NFCeConsultaPublica/Paginas/ConsultaQRCode.aspx?p=..."
```

For AI-powered commands, set your key in `.env`:

```bash
echo "OPENAI_API_KEY=your_key" > .env
```

The CLI automatically loads variables from `.env`.

Normalize latest invoice items (Phase 1 spike):

```bash
python -m src.what_im_buying.cli normalize-last-invoice
```

Run minimal viewer UI:

```bash
streamlit run src/what_im_buying/viewer.py
```

Import from a saved HTML file (for testing):

```bash
python -m src.what_im_buying.cli import-html tests/fixtures/sample_sp_nfce.html --url "local://sample"
```

## Notes

- This is a first iteration focused on NFC-e visual page parsing.
- Different states/providers can vary HTML structure; parser is heuristic.
- Database file defaults to `data/what_im_buying.db`.
- Live execution requires dependencies from `requirements.txt`.
