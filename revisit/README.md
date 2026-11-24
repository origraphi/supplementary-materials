# reVISit study setup

The pilot and the online study ran on [reVISit](https://revisit.dev), an open-source platform for
web-based user studies (BSD-3-Clause, see `LICENSE` and `CITATION.cff`). This folder is the full
reVISit application with our study added. Our study lives in `public/biofabric-study/` and is
listed in `public/global.json`; the rest is the reVISit platform.

## Our study

| File                                            | Contents                                                                                                           |
|-------------------------------------------------|--------------------------------------------------------------------------------------------------------------------|
| `public/biofabric-study/config.json`            | Study configuration: consent, introduction, tutorial, practice trials, attention checks, the three tasks, NASA-TLX |
| `public/biofabric-study/create_revisit.py`      | Prints the study configuration; redirect it into `config.json` (uses the `revisitpy` package)                      |
| `public/biofabric-study/build_help_texts.py`    | Generates the per-task help texts in `assets/help/`                                                                |
| `public/biofabric-study/start.html`             | Entry page: assigns each participant to the condition with fewer participants so far                               |
| `public/biofabric-study/assets/*.md`            | Texts shown to participants (consent, introduction, tutorial, terminology, NASA-TLX)                               |
| `public/biofabric-study/assets/biofabric/`      | The BioFabric stimulus used in the trials                                                                          |
| `public/biofabric-study/assets/biofabric/data/` | Study graphs (selected Rome graphs, estimation graphs) and the scripts that converted them                         |
| `public/global.json`                            | Lists the study; `biofabric-study-pilot` reuses the same configuration for the pilot                               |

### Conditions

The condition is set with the URL parameter `condition`:

| URL value   | Condition                     |
|-------------|-------------------------------|
| `normal`    | unfolded (standard BioFabric) |
| `collapsed` | (edge-)folded (Origraphi)     |

The study files and the exported data use these URL values; the analyses relabel them as
`unfolded` and `folded`.

## Running locally

Requires Node.js and yarn (`npm i -g yarn`; use yarn, not npm).

```bash
yarn install
yarn serve
```

Then open <http://localhost:8080/biofabric-study?condition=collapsed> (or `condition=normal`).
`start.html` picks the condition automatically when a database is configured.

`.env` contains placeholders. With the default `VITE_STORAGE_ENGINE="localStorage"`, responses
are only stored in the browser. To collect data, fill in your own Firebase or Supabase settings
(see the [reVISit documentation](https://revisit.dev/docs)), and the Supabase settings in `start.html`.

To regenerate the configuration after changing `create_revisit.py`:

```bash
cd public/biofabric-study
pip install revisitpy
python build_help_texts.py
python create_revisit.py > config.json
```

## Anonymized for review

Author names, affiliations and contact details (study metadata and consent form), the Prolific
completion and return codes, and the database credentials have been replaced with placeholders.