# KOReader to Markdown

Read bookmarks from [KOReader](https://koreader.rocks/) sidecars to Markdown files per book

## How-to

2. Run `pipenv install` to install all dependencies from `Pipfile`
   - [Install `pipenv`](https://github.com/pypa/pipenv#installation) if you
     don't have it yet
1. Run `make` to download `slpp.py`
3. Start your KOReader's SSH server without a password and make note of its IP address
4. Make sure you can connect to it using `ssh` from your terminal. See
   [this](https://github.com/koreader/koreader/wiki/SSH) for more info
5. Rename `example.env` to `.env` and add the host (IP address) and user (typically `root`) of your KOReader's SSH
6. Run `koreader-to-markdown.py`
   1. If your SSH key requires a passphrase, you will be prompted
7. Copy the result from `output` to your [Obsidian](https://obsidian.md/) vault, or wherever you want to have your highlights as Markdown

## Credits

- [`paramiko`](https://www.paramiko.org/) to read your KOReader's sidecars over SSH
- [`python-dotenv`](https://github.com/theskumar/python-dotenv) to read the contents of `.env`
- [`inquirer`](https://github.com/magmax/python-inquirer) to ask for your SSH key's passphrase, if needed
