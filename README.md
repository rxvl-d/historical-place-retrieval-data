# Historical place retrieval: dataset references

Identifiers, links, place labels and splits for the datasets used in the paper
on place retrieval in historical photo archives. This repository contains no
images. Every image is referenced by the identifier or URL of its original
source, which also carries the image's licence.

## wikidata_heritage/ (fine-tuning data)

Photographs of heritage buildings from Wikimedia Commons, grouped by the
Wikidata item of the place they show. 6,612 places, 34,147 images, split by
place into 5,290 training places (27,309 images) and 1,322 held-out places
(6,838 images). The two splits share no place.

- `places.csv`: one row per place. `qid`, `wikidata_url`, `split` (train or
  heldout), building `category` and `cluster`, `lat`/`lon`, `n_images`.
- `images.csv`: one row per image. `qid`, `split`, `stored_name` (the file
  name used in our copy, where every character outside `[A-Za-z0-9._-]` was
  replaced by `_`), `commons_title` (original Commons file title) and
  `commons_file_page`.
- `train_qids.txt`, `heldout_qids.txt`: the split as plain lists of QIDs.

The original Commons titles were recovered by listing the files of each
place's Commons category (and its Wikidata P18 images) and matching them to the
stored names with the same character replacement (`scripts/resolve_commons_titles.py`).
33,904 of 34,147 images (99.3%) matched. For the other 243, `commons_title` is
empty and only `stored_name` is available. To fetch an image, use
`https://commons.wikimedia.org/wiki/Special:FilePath/<commons_title>`.

## benchmarks/ (evaluation archives)

Place labels and the identifier of each photograph. Two photographs are
relevant to each other when they carry the same `place_id`.

| file | archive | places | images | source identifier |
|---|---|---|---|---|
| `sagarra.csv` | Sagarra (Girona municipal archive) | 57 | 356 | Europeana record, `source_url` is the Europeana item page |
| `fairphotos.csv` | FAIRPhotos (Dutch press photography, Noord-Hollands Archief) | 134 | 610 | file identifier in the FAIR Data Call dataset, https://doi.org/10.17026/SS/7VD3ME (no per-image URL) |
| `germancolonial.csv` | GermanColonial (Image Archive from Colonial Contexts) | 92 | 346 | URN, resolved by `source_url` through nbn-resolving.org |
| `salvany.csv` | Salvany (Biblioteca de Catalunya via Europeana) | 383 | 2,840 | Europeana record and IIIF image URL |

Columns of `sagarra.csv`, `fairphotos.csv` and `germancolonial.csv`: `place_id`,
`place_label`, `alt_labels` (other captions grouped under the place, separated
by ` | `), `image_id` (file name in our copy), `source_id`, `source_url`.

`salvany.csv` has one row per image with `place_qid`, `place_label`,
`place_class`, `image_id`, `europeana_id`, `europeana_url`, `iiif_image_url`,
`title`, `rights` and `data_provider`. The paper uses only the building places
(`place_class == building`: 26 places, 176 images).

## scripts/

`resolve_commons_titles.py` and `build_release.py` produced these tables from
our local copies of the datasets. They are included for provenance and need
those local copies (a `raw/` folder with each dataset's `classes.json`,
`manifest.csv` for Salvany and the Wikidata-heritage `place_coords.json`).
