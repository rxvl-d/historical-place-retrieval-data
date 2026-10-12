"""Recover the original Wikimedia Commons file titles for the wikidata-heritage
pool. The pool stores each image as <QID>/<sanitized title>, where every
character outside [A-Za-z0-9._-] was replaced by '_'. For each place we list the
files of its Commons category (Wikidata sitelink or P373) plus its P18 images
and match them to the stored names by applying the same sanitisation.
Writes raw/commons_titles.json: {"<QID>/<stored name>": "<Commons title>" | null}.
API responses are cached in raw/commons_cache/ so the script can be re-run."""
import json, os, re, subprocess, sys, time, urllib.parse

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
RAW = os.path.join(ROOT, "raw")
CACHE = os.path.join(RAW, "commons_cache")
UA = "historical-place-retrieval-data/0.1 (research dataset release)"
os.makedirs(CACHE, exist_ok=True)


def sanitize(title):
    return re.sub(r"[^A-Za-z0-9._-]", "_", title)


def api(base, params, cache_key):
    path = os.path.join(CACHE, cache_key + ".json")
    if os.path.exists(path):
        return json.load(open(path))
    params = dict(params, format="json")
    url = base + "?" + urllib.parse.urlencode(params)
    for attempt in range(6):
        try:
            out = subprocess.run(["curl", "-s", "-m", "60", "-A", UA, url], capture_output=True, check=True).stdout
            data = json.loads(out)
            if "error" in data and data["error"].get("code") == "maxlag":
                time.sleep(5); continue
            json.dump(data, open(path, "w"))
            time.sleep(0.05)
            return data
        except Exception as e:
            time.sleep(2 * (attempt + 1))
    raise RuntimeError("failed: " + url)


def main():
    classes = json.load(open(f"{RAW}/wikidata-heritage-pool/classes.json"))["classes"]
    qids = [c["class_id"] for c in classes]
    cats, p18 = {}, {}
    for i in range(0, len(qids), 50):
        chunk = qids[i:i + 50]
        d = api("https://www.wikidata.org/w/api.php",
                dict(action="wbgetentities", ids="|".join(chunk), props="claims|sitelinks", sitefilter="commonswiki"),
                f"wd_{chunk[0]}_{i}")
        for q, e in d.get("entities", {}).items():
            sl = e.get("sitelinks", {}).get("commonswiki", {}).get("title")
            if sl and sl.startswith("Category:"):
                cats[q] = sl
            else:
                p373 = e.get("claims", {}).get("P373", [])
                if p373:
                    cats[q] = "Category:" + p373[0]["mainsnak"]["datavalue"]["value"]
            p18[q] = [c["mainsnak"]["datavalue"]["value"] for c in e.get("claims", {}).get("P18", [])
                      if "datavalue" in c["mainsnak"]]
        print(f"wikidata {min(i + 50, len(qids))}/{len(qids)}", file=sys.stderr)

    out, matched = {}, 0
    for n, c in enumerate(classes):
        q = c["class_id"]
        titles = set(p18.get(q, []))
        if q in cats:
            cont = None
            while True:
                params = dict(action="query", list="categorymembers", cmtitle=cats[q], cmtype="file", cmlimit="500")
                if cont: params["cmcontinue"] = cont
                d = api("https://commons.wikimedia.org/w/api.php", params, f"cat_{q}_{cont or 'first'}".replace("|", "_"))
                titles.update(m["title"][5:] for m in d.get("query", {}).get("categorymembers", []))
                cont = d.get("continue", {}).get("cmcontinue")
                if not cont: break
        by_san = {sanitize(t): t for t in titles}
        for img in c["images"]:
            key = img
            name = img.split("/", 1)[1]
            t = by_san.get(name) or by_san.get(name.rsplit(".", 1)[0] + "." + name.rsplit(".", 1)[1].lower())
            out[key] = t
            matched += t is not None
        if n % 200 == 0:
            print(f"places {n}/{len(classes)} matched {matched}", file=sys.stderr)
    json.dump(out, open(f"{RAW}/commons_titles.json", "w"), ensure_ascii=False)
    print(f"matched {matched}/{len(out)}")


if __name__ == "__main__":
    main()
