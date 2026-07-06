#!/usr/bin/env python3
"""Convert an Antscan RADAR descriptive-metadata XML into a minimal, detached
RO-Crate metadata file following (a backwards-compatible subset of) the GIDE
search input profile.

Usage:
    python desc_to_rocrate.py dataset.desc_md.xml [ro-crate-metadata.json]
"""

import json
import re
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

# --- fixed values -----------------------------------------------------------

# Hardcoded imaging method: X-ray computed tomography (FBbi:00001002)
IMAGING_METHOD = {
    "@id": "http://purl.obolibrary.org/obo/FBbi_00001002",
    "@type": "DefinedTerm",
    "name": "X-ray computed tomography",
}

# RADAR XML namespace (elements are unprefixed within this default namespace)
NS = "{http://radar-service.eu/schemas/descriptive/radar/v09/radar-elements}"

CONTEXT = [
    "https://w3id.org/ro/crate/1.2/context",
    {
        "scientificName": "http://rs.tdwg.org/dwc/terms/scientificName",
        "measurementMethod": "http://rs.tdwg.org/dwc/iri/measurementMethod",
    },
]


# --- helpers ----------------------------------------------------------------


def tag(elem):
    """Local tag name without namespace."""
    return elem.tag[len(NS) :] if elem.tag.startswith(NS) else elem.tag


def _ns(path):
    """Insert the RADAR namespace before every element name in an ElementTree path."""
    return re.sub(r"([A-Za-z_][\w-]*)", lambda m: NS + m.group(1), path)


def find(root, path):
    return root.find(_ns(path))


def findall(root, path):
    return root.findall(_ns(path))


def text(elem, default=""):
    return elem.text.strip() if elem is not None and elem.text else default


def resolve_ncbi_taxon(species):
    """Resolve a scientific name to an NCBI taxonomy URL via the toolforge hub.

    https://hub.toolforge.org/ceb:<species>?property=P685 redirects to an
    NCBI taxonomy page whose final path segment is the taxid. Returns the
    NCBI datasets URL, or None if the lookup fails (offline, no match, etc.).
    """
    if not species:
        return None
    url = (
        "https://hub.toolforge.org/ceb:"
        + urllib.parse.quote(species)
        + "?property=P685"
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "desc_to_rocrate/1.0"})
        print(f"Resolving NCBI taxon for '{species}' via {url} ...")
        print(req)
        with urllib.request.urlopen(req, timeout=20) as resp:
            final = resp.geturl()
        print(f"Final URL after redirection: {final}")
        m = re.search(r"/taxonomy/(\d+)/", final)
        if m:
            print(m)
            return f"https://purl.obolibrary.org/obo/NCBITaxon_{m.group(1)}/"
    except Exception:
        pass
    return None


def parse_related_info(root):
    """Parse the free-text 'relatedInformation' blob of 'key = value, ...' pairs."""
    node = find(root, ".//relatedInformation")
    out = {}
    if node is not None and node.text:
        for part in node.text.split(","):
            if "=" in part:
                k, v = part.split("=", 1)
                out[k.strip()] = v.strip()
    return out


# --- conversion -------------------------------------------------------------


def build_crate(root, xml_filename):
    info = parse_related_info(root)

    doi = text(find(root, ".//identifier"))
    # The root dataset is the crate itself, identified by "./" (RO-Crate
    # convention). The DOI is retained as `identifier`.
    root_id = "./"

    name = text(find(root, ".//title"))
    description = text(find(root, ".//description"))
    date_published = text(find(root, ".//publicationYear"))
    license_name = text(find(root, ".//controlledRights"))

    graph = []

    # RO-Crate metadata descriptor (self-describing)
    graph.append(
        {
            "@id": "ro-crate-metadata.json",
            "@type": "CreativeWork",
            "conformsTo": {"@id": "https://w3id.org/ro/crate/1.2"},
            "about": {"@id": root_id},
        }
    )

    # Publisher (take the first listed)
    pub_el = find(root, ".//publisher")
    publisher = {
        "@id": (
            pub_el.get("nameIdentifier")
            if pub_el is not None and pub_el.get("nameIdentifier")
            else "#publisher"
        ),
        "@type": "Organization",
        "name": text(pub_el),
    }

    # Taxon, from parsed extra metadata. Prefer an NCBI taxonomy URL resolved
    # from the scientific name; fall back to the AntWiki Source, then a local id.
    species = info.get("Name", "")
    taxon_id = resolve_ncbi_taxon(species) or info.get("Source") or "#taxon"
    taxon = {
        "@id": taxon_id,
        "@type": "Taxon",
        "name": species,
        "scientificName": species,
    }

    # Root dataset
    dataset = {
        "@id": root_id,
        "@type": "Dataset",
        "name": name,
        "description": description,
        "datePublished": date_published,
        "license": license_name,
        "identifier": doi,
        "publisher": {"@id": publisher["@id"]},
        "about": {"@id": taxon["@id"]},
        "measurementMethod": {"@id": IMAGING_METHOD["@id"]},
        # Link back to the original descriptive metadata file
        "subjectOf": {"@id": xml_filename},
    }

    graph.append(dataset)
    graph.append(publisher)
    graph.append(taxon)
    graph.append(IMAGING_METHOD)

    # The original descriptive metadata, present as a linked file
    graph.append(
        {
            "@id": xml_filename,
            "@type": "File",
            "name": "Original RADAR descriptive metadata",
            "encodingFormat": "application/xml",
            "about": {"@id": root_id},
        }
    )

    return {"@context": CONTEXT, "@graph": graph}


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    xml_path = sys.argv[1]
    out_path = sys.argv[2] if len(sys.argv) > 2 else "ro-crate-metadata.json"

    root = ET.parse(xml_path).getroot()
    xml_filename = xml_path.rsplit("/", 1)[-1]

    crate = build_crate(root, xml_filename)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(crate, f, indent=2, ensure_ascii=False)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
