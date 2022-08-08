from __future__ import annotations

import json
from collections import OrderedDict
from datetime import datetime

from . import h, messages as m, t


def addCanIUsePanels(doc: t.SpecT) -> None:
    # Constructs "Can I Use panels" which show a compatibility data summary
    # for a term's feature.
    if not doc.md.includeCanIUsePanels:
        return

    if not doc.canIUse:
        doc.canIUse = CanIUseManager(dataFile=doc.dataFile)

    lastUpdated = datetime.utcfromtimestamp(doc.canIUse.updated).date().isoformat()

    # e.g. 'iOS Safari' -> 'ios_saf'
    classFromBrowser = doc.canIUse.agents

    atLeastOnePanel = False
    elements = h.findAll("[caniuse]", doc)
    if not elements:
        return
    validateCanIUseURLs(doc, elements)
    for dfn in elements:
        featId = dfn.get("caniuse")
        if not featId:
            continue
        del dfn.attrib["caniuse"]

        featId = featId.lower()
        if not doc.canIUse.hasFeature(featId):
            m.die(f"Unrecognized Can I Use feature ID: {featId}", el=dfn)
        feature = doc.canIUse.getFeature(featId)

        h.addClass(dfn, "caniuse-paneled")
        panel = canIUsePanelFor(
            id=featId,
            data=feature,
            update=lastUpdated,
            classFromBrowser=classFromBrowser,
        )
        dfnId = dfn.get("id")
        if not dfnId:
            m.die(f"Elements with `caniuse` attribute need to have an ID as well. Got:\n{h.serializeTag(dfn)}", el=dfn)
            continue
        panel.set("data-dfn-id", dfnId)
        h.appendChild(doc.body, panel)
        atLeastOnePanel = True

    if atLeastOnePanel:
        doc.extraScripts[
            "script-caniuse-panel"
        ] = """
            window.addEventListener("load", function(){
                var panels = [].slice.call(document.querySelectorAll(".caniuse-status"));
                for(var i = 0; i < panels.length; i++) {
                    var panel = panels[i];
                    var dfn = document.querySelector("#" + panel.getAttribute("data-dfn-id"));
                    var rect = dfn.getBoundingClientRect();
                    panel.style.top = (window.scrollY + rect.top) + "px";
                }
            });
            document.body.addEventListener("click", function(e) {
                if(e.target.classList.contains("caniuse-panel-btn")) {
                    e.target.parentNode.classList.toggle("wrapped");
                }
            });"""
        doc.extraStyles[
            "style-caniuse-panel"
        ] = """
            :root {
                --caniuse-shadow: #999;
                --caniuse-nosupport-text: #ccc;
                --caniuse-partialsupport-text: #666;
            }
            .caniuse-status { font: 1em sans-serif; width: 9em; padding: 0.3em; position: absolute; z-index: 8; top: auto; right: 0.3em; background: var(--borderedblock-bg, #EEE); color: var(--text, black); box-shadow: 0 0 3px var(--caniuse-shadow, #999); overflow: hidden; border-collapse: initial; border-spacing: initial; }
            .caniuse-status.wrapped { width: auto; height: 1em; }
            .caniuse-status.wrapped > :not(input) { display: none; }
            .caniuse-status > input { float: right; border: none; background: transparent; padding: 0; margin: 0; }
            .caniuse-status > p { font-size: 0.6em; margin: 0; padding: 0; clear: both; }
            .caniuse-status > p + p { padding-top: 0.5em; }
            .caniuse-status > .support { display: block; }
            .caniuse-status > .support > span { padding: 0.2em 0; display: block; display: table; }
            .caniuse-status > .support > span.partial { color: var(--caniuse-partialsupport-text, #666666); filter: grayscale(50%); }
            .caniuse-status > .support > span.no { color: var(--caniuse-nosupport-text, #CCCCCC); filter: grayscale(100%); }
            .caniuse-status > .support > span.no::before { opacity: 0.5; }
            .caniuse-status > .support > span:first-of-type { padding-top: 0.5em; }
            .caniuse-status > .support > span > span { padding: 0 0.5em; display: table-cell; vertical-align: top; }
            .caniuse-status > .support > span > span:first-child { width: 100%; }
            .caniuse-status > .support > span > span:last-child { width: 100%; white-space: pre; padding: 0; }
            .caniuse-status > .support > span::before { content: ' '; display: table-cell; min-width: 1.5em; height: 1.5em; background: no-repeat center center; background-size: contain; text-align: right; font-size: 0.75em; font-weight: bold; }
            .caniuse-status > .support > .and_chr::before { background-image: url(https://resources.whatwg.org/browser-logos/chrome.svg); }
            .caniuse-status > .support > .and_ff::before { background-image: url(https://resources.whatwg.org/browser-logos/firefox.png); }
            .caniuse-status > .support > .and_uc::before { background-image: url(https://resources.whatwg.org/browser-logos/uc.png); } /* UC Browser for Android */
            .caniuse-status > .support > .android::before { background-image: url(https://resources.whatwg.org/browser-logos/android.svg); }
            .caniuse-status > .support > .bb::before { background-image: url(https://resources.whatwg.org/browser-logos/bb.jpg); } /* Blackberry Browser */
            .caniuse-status > .support > .chrome::before { background-image: url(https://resources.whatwg.org/browser-logos/chrome.svg); }
            .caniuse-status > .support > .edge::before { background-image: url(https://resources.whatwg.org/browser-logos/edge.svg); }
            .caniuse-status > .support > .firefox::before { background-image: url(https://resources.whatwg.org/browser-logos/firefox.png); }
            .caniuse-status > .support > .ie::before { background-image: url(https://resources.whatwg.org/browser-logos/ie.png); }
            .caniuse-status > .support > .ie_mob::before { background-image: url(https://resources.whatwg.org/browser-logos/ie-mobile.svg); }
            .caniuse-status > .support > .ios_saf::before { background-image: url(https://resources.whatwg.org/browser-logos/safari-ios.svg); }
            .caniuse-status > .support > .op_mini::before { background-image: url(https://resources.whatwg.org/browser-logos/opera-mini.png); }
            .caniuse-status > .support > .op_mob::before { background-image: url(https://resources.whatwg.org/browser-logos/opera.svg); }
            .caniuse-status > .support > .opera::before { background-image: url(https://resources.whatwg.org/browser-logos/opera.svg); }
            .caniuse-status > .support > .safari::before { background-image: url(https://resources.whatwg.org/browser-logos/safari.png); }
            .caniuse-status > .support > .samsung::before { background-image: url(https://resources.whatwg.org/browser-logos/samsung.svg); }
            .caniuse-status > .caniuse { text-align: right; font-style: italic; }
            @media (max-width: 767px) {
                .caniuse-status.wrapped { width: 9em; height: auto; }
                .caniuse-status:not(.wrapped) { width: 1em; height: 1em; }
                .caniuse-status.wrapped > :not(input) { display: block; }
                .caniuse-status:not(.wrapped) > :not(input) { display: none; }
            }"""

        doc.extraStyles[
            "style-darkmode"
        ] += """
            @media (prefers-color-scheme: dark) {
                :root {
                    --caniuse-shadow: #444;
                    --caniuse-nosupport-text: #666;
                    --caniuse-partialsupport-text: #bbb;
                }
            }"""


def canIUsePanelFor(id: str, data: t.JSONT, update: str, classFromBrowser: dict[str, str]) -> t.ElementT:
    panel = h.E.aside(
        {"class": "caniuse-status wrapped", "data-deco": ""},
        h.E.input({"value": "CanIUse", "type": "button", "class": "caniuse-panel-btn"}),
    )
    mainPara = h.E.p({"class": "support"}, h.E.b({}, "Support:"))
    h.appendChild(panel, mainPara)
    for browser, support in data["support"].items():
        statusCode = support[0]
        if statusCode == "u":
            continue
        minVersion = support[2:]
        h.appendChild(
            mainPara,
            browserCompatSpan(classFromBrowser[browser], browser, statusCode, minVersion),
        )
    h.appendChild(
        panel,
        h.E.p(
            {"class": "caniuse"},
            "Source: ",
            h.E.a({"href": "https://caniuse.com/#feat=" + id}, "caniuse.com"),
            " as of " + update,
        ),
    )
    return panel


def browserCompatSpan(
    browserCodeName: str, browserFullName: str, statusCode: str, minVersion: str | None = None
) -> t.ElementT:
    if statusCode == "n" or minVersion is None:
        minVersion = "None"
    elif minVersion == "all":
        minVersion = "All"
    else:
        minVersion = minVersion + "+"
    # browserCodeName: e.g. and_chr, ios_saf, ie, etc...
    # browserFullName: e.g. "Chrome for Android"
    statusClass = {"y": "yes", "n": "no", "a": "partial"}[statusCode]
    outer = h.E.span({"class": browserCodeName + " " + statusClass})
    if statusCode == "a":
        h.appendChild(outer, h.E.span({}, h.E.span({}, browserFullName, " (limited)")))
    else:
        h.appendChild(outer, h.E.span({}, browserFullName))
    h.appendChild(outer, h.E.span({}, minVersion))
    return outer


def validateCanIUseURLs(doc: t.SpecT, elements: list[t.ElementT]) -> None:
    # First, ensure that each Can I Use URL shows up at least once in the data;
    # otherwise, it's an error to be corrected somewhere.
    urlFeatures = set()
    if doc.canIUse is None:
        return
    for url in doc.md.canIUseURLs:
        sawTheURL = False
        for featureID, featureUrl in doc.canIUse.urlFromFeature.items():
            if featureUrl.startswith(url):
                sawTheURL = True
                urlFeatures.add(featureID)
        if not sawTheURL and url not in doc.md.ignoreCanIUseUrlFailure:
            m.warn(
                f"The Can I Use URL '{url}' isn't associated with any of the Can I Use features."
                "Please check Can I Use for the correct spec url, and either correct your spec or correct Can I Use."
                "If the URL is correct and you'd like to keep it in pre-emptively, add the URL to a 'Ignore Can I Use URL Failure' metadata."
            )

    # Second, ensure that every feature in the data corresponding to one of the listed URLs
    # has a corresponding Can I Use entry in the document;
    # otherwise, you're missing some features.
    docFeatures = set()
    for el in elements:
        canIUseAttr = el.get("caniuse")
        assert canIUseAttr is not None
        featureID = canIUseAttr.lower()
        docFeatures.add(featureID)

    unusedFeatures = urlFeatures - docFeatures
    if unusedFeatures:
        featureList = "\n".join(" * {0} - https://caniuse.com/#feat={0}".format(x) for x in sorted(unusedFeatures))
        m.warn(
            f"The following Can I Use features are associated with your URLs, but don't show up in your spec:\n{featureList}"
        )


class CanIUseManager:
    def __init__(self, dataFile: t.DataFileRequester):
        self.dataFile = dataFile
        data = json.loads(
            self.dataFile.fetch("caniuse", "data.json", str=True),
            object_pairs_hook=OrderedDict,
        )
        self.updated = data["updated"]
        self.agents = data["agents"]
        self.urlFromFeature = data["features"]
        self.features: t.JSONT = {}

    def hasFeature(self, featureName: str) -> bool:
        return featureName in self.urlFromFeature

    def getFeature(self, featureName: str) -> t.JSONT:
        if featureName in self.features:
            return self.features[featureName]
        if not self.hasFeature(featureName):
            return {}
        data = json.loads(
            self.dataFile.fetch("caniuse", f"feature-{featureName}.json", str=True),
            object_pairs_hook=OrderedDict,
        )
        self.features[featureName] = data
        return data
