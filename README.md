# What I'm Buying (MVP)

Simple MVP to parse Brazilian NFC-e public pages from QR URLs and generate purchase insights.

## What it does

- Accepts an NFC-e QR URL (already scanned from receipt QR code).
- Fetches the public page HTML.
- Parses invoice items with resilient table heuristics.
- Stores invoice + item history in SQLite.
- Generates basic insights:
  - products missing from your last purchase but frequently bought
  - products with recent price increase

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

Generate insights:

```bash
python -m src.what_im_buying.cli report
```

Generate AI insights (optional):

```bash
pip install openai
echo "OPENAI_API_KEY=your_key" > .env
python -m src.what_im_buying.cli ai-report
```

The CLI automatically loads variables from `.env`.

Import from a saved HTML file (for testing):

```bash
python -m src.what_im_buying.cli import-html tests/fixtures/sample_sp_nfce.html --url "local://sample"
```

## Notes

- This is a first iteration focused on NFC-e visual page parsing.
- Different states/providers can vary HTML structure; parser is heuristic.
- Database file defaults to `data/what_im_buying.db`.
- Live execution requires dependencies from `requirements.txt`.


Natural next steps:

- Add robust parsers per state/provider (SP first, then RJ/MG/etc).
- Add QR image decoding (upload photo -> extract URL -> parse).
- Add product normalization via barcode + brand/size matching for better price tracking.