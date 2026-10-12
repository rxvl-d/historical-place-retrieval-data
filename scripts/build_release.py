"""Assemble the release tables from the raw dataset metadata (raw/) and the
Commons titles recovered by resolve_commons_titles.py. No images are included."""
import csv, json, os, urllib.parse

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
RAW = os.path.join(ROOT, "raw")


def jl(p): return json.load(open(os.path.join(RAW, p)))


def write(path, rows, cols):
    os.makedirs(os.path.dirname(os.path.join(ROOT, path)), exist_ok=True)
    with open(os.path.join(ROOT, path), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)
    print(path, len(rows))


# ---- wikidata-heritage (training data) ----
pool = jl("wikidata-heritage-pool/classes.json")["classes"]
train = {c["class_id"] for c in jl("wikidata-heritage-pool/classes_trainsplit.json")["classes"]}
held = {c["class_id"] for c in jl("wikidata-heritage-pool/classes_heldout.json")["classes"]}
assert not train & held and train | held == {c["class_id"] for c in pool}
coords = {p["class_id"]: p for p in jl("wikidata-heritage-pool/place_coords.json")["places"]}
titles = jl("commons_titles.json")


def split(q): return "train" if q in train else "heldout"


places, images = [], []
for c in pool:
    q = c["class_id"]; p = coords.get(q, {})
    places.append(dict(qid=q, wikidata_url=f"https://www.wikidata.org/wiki/{q}", split=split(q),
                       category=c.get("category", ""), cluster=c.get("cluster", ""),
                       lat=p.get("lat", ""), lon=p.get("lon", ""), n_images=len(c["images"])))
    for img in c["images"]:
        t = titles.get(img)
        images.append(dict(qid=q, split=split(q), stored_name=img.split("/", 1)[1], commons_title=t or "",
                           commons_file_page=("https://commons.wikimedia.org/wiki/File:" + urllib.parse.quote(t.replace(" ", "_"))) if t else ""))
write("wikidata_heritage/places.csv", places, ["qid", "wikidata_url", "split", "category", "cluster", "lat", "lon", "n_images"])
write("wikidata_heritage/images.csv", images, ["qid", "split", "stored_name", "commons_title", "commons_file_page"])
for s in ("train", "heldout"):
    with open(os.path.join(ROOT, f"wikidata_heritage/{s}_qids.txt"), "w") as f:
        f.write("\n".join(sorted(q for q in (train if s == "train" else held))) + "\n")

# ---- benchmarks ----
def archive_rows(d, name, image_id_fn, source_fn):
    rows = []
    for c in jl(f"{d}/classes.json")["classes"]:
        for img in c["images"]:
            sid, url = source_fn(img)
            rows.append(dict(place_id=c["class_id"], place_label=c["label"], alt_labels=" | ".join(c.get("alt_labels", [])),
                             image_id=image_id_fn(img), source_id=sid, source_url=url))
    write(f"benchmarks/{name}.csv", rows, ["place_id", "place_label", "alt_labels", "image_id", "source_id", "source_url"])


def girona(img):
    stem = img.rsplit(".", 1)[0]; coll, rec = stem.split("_", 1)
    return f"/{coll}/{rec}", f"https://www.europeana.eu/en/item/{coll}/{rec}"


def vabiko(img):
    urn = img.split("/")[0].replace("+", ":")
    return urn, f"https://nbn-resolving.org/{urn}"


archive_rows("girona-vpr", "sagarra", lambda i: i, girona)
archive_rows("fairphotos-vpr", "fairphotos", lambda i: i, lambda i: (i.rsplit(".", 1)[0], ""))
archive_rows("vabiko-vpr", "germancolonial", lambda i: i.split("/")[0], vabiko)

# SalvanyBuildings: manifest rows joined to the place classes (the paper uses place_class == building)
man = {}
import csv as _csv
for r in _csv.DictReader(open(os.path.join(RAW, "salvany_instance_retrieval_benchmark/manifest.csv"))):
    man[r["local_path"].replace("images/", "", 1)] = r
rows = []
for c in jl("salvany_instance_retrieval_benchmark/classes.json")["classes"]:
    for img in c["images"]:
        m = man[img]
        rows.append(dict(place_qid=c["class_id"].rsplit("/", 1)[-1], place_label=c["label"], place_class=c["place_class"],
                         image_id=img, europeana_id=m["europeana_id"],
                         europeana_url="https://www.europeana.eu/en/item" + m["europeana_id"],
                         iiif_image_url=m["image_url"], title=m["title"], rights=m["rights"], data_provider=m["data_provider"]))
write("benchmarks/salvany.csv", rows, ["place_qid", "place_label", "place_class", "image_id", "europeana_id", "europeana_url",
                                       "iiif_image_url", "title", "rights", "data_provider"])
