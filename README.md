# KOReader to Markdown

Read bookmarks from KOReader sidecars to Markdown files per book

## How-to

1. Run `make` to download `slpp.py`
1. Run `conda env create -f environment.yml` to set up a conda environment in `./env`
1. Add the host and user of your KOReader's SSH to `example.env` and rename it to `.env`
1. Run `koreader-to-markdown.py`
1. Copy the result from `output` to Obsidian, or wherever you want to have your highlights as Markdown
