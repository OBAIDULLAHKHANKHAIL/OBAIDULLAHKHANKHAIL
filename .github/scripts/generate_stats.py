"""Builds theme-aware SVG stat cards from the GitHub GraphQL API (no third-party services)."""
import os, json, urllib.request
OUT = os.environ.get("OUT_DIR", "assets")
USER = os.environ.get("GH_USER", "OBAIDULLAHKHANKHAIL")
Q = """query($u:String!){user(login:$u){createdAt followers{totalCount}
contributionsCollection{totalCommitContributions totalPullRequestContributions totalIssueContributions totalPullRequestReviewContributions}
repositories(ownerAffiliations:OWNER,isFork:false,first:100,orderBy:{field:PUSHED_AT,direction:DESC}){totalCount nodes{stargazerCount languages(first:6,orderBy:{field:SIZE,direction:DESC}){edges{size node{name color}}}}}}}"""
def fetch():
    req = urllib.request.Request("https://api.github.com/graphql", json.dumps({"query": Q, "variables": {"u": USER}}).encode(),
                                 {"Authorization": "bearer " + os.environ["GH_TOKEN"], "Content-Type": "application/json"})
    u = json.load(urllib.request.urlopen(req))["data"]["user"]; c = u["contributionsCollection"]; langs = {}
    for r in u["repositories"]["nodes"]:
        for e in r["languages"]["edges"]:
            n = e["node"]["name"]; langs.setdefault(n, [0, e["node"]["color"] or "#8b949e"]); langs[n][0] += e["size"]
    return dict(commits=c["totalCommitContributions"], prs=c["totalPullRequestContributions"], issues=c["totalIssueContributions"],
                reviews=c["totalPullRequestReviewContributions"], stars=sum(r["stargazerCount"] for r in u["repositories"]["nodes"]),
                repos=u["repositories"]["totalCount"], followers=u["followers"]["totalCount"], since=u["createdAt"][:4], langs=langs)
TH = {"dark": dict(bg="#0d1117", bd="#30363d", t="#e6edf3", m="#8b949e", a="#38bdf8", tr="#21262d"),
      "light": dict(bg="#ffffff", bd="#d0d7de", t="#0e1226", m="#57606a", a="#5a4cf5", tr="#eaeef2")}
def v(x): return "–" if x is None else f"{x:,}"
def write(d):
    os.makedirs(OUT, exist_ok=True)
    items = [("Commits (past year)", d["commits"]), ("Pull requests", d["prs"]), ("Code reviews", d["reviews"]), ("Issues", d["issues"]),
             ("Stars earned", d["stars"]), ("Public repos", d["repos"]), ("Followers", d["followers"])]
    for n, T in TH.items():
        rows = "".join(f'<text x="28" y="{74 + i * 30}" fill="{T["m"]}" font-size="14">{k}</text><text x="372" y="{74 + i * 30}" fill="{T["t"]}" font-size="15" font-weight="700" text-anchor="end">{v(x)}</text>' for i, (k, x) in enumerate(items))
        open(f"{OUT}/stats-{n}.svg", "w").write(f'<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300" viewBox="0 0 400 300" font-family="Segoe UI,Helvetica,Arial,sans-serif"><rect x=".5" y=".5" width="399" height="299" rx="12" fill="{T["bg"]}" stroke="{T["bd"]}"/><text x="28" y="40" fill="{T["a"]}" font-size="18" font-weight="700">GitHub activity</text><text x="372" y="40" fill="{T["m"]}" font-size="12" text-anchor="end">since {d["since"]}</text>{rows}</svg>')
        tot = sum(s for s, _ in d["langs"].values()) or 1
        top = sorted(d["langs"].items(), key=lambda kv: -kv[1][0])[:6]; x = 28; bar = ""; leg = ""
        for i, (k, (s, col)) in enumerate(top):
            w = 344 * s / tot; bar += f'<rect x="{x:.1f}" y="62" width="{max(w, 2):.1f}" height="10" fill="{col}"/>'; x += w
            leg += f'<circle cx="{34 + (i % 2) * 180}" cy="{108 + (i // 2) * 30}" r="5" fill="{col}"/><text x="{46 + (i % 2) * 180}" y="{113 + (i // 2) * 30}" fill="{T["t"]}" font-size="13">{k} <tspan fill="{T["m"]}">{100 * s / tot:.0f}%</tspan></text>'
        if not top: leg = f'<text x="28" y="110" fill="{T["m"]}" font-size="13">Updates automatically after the first workflow run.</text>'
        open(f"{OUT}/langs-{n}.svg", "w").write(f'<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300" viewBox="0 0 400 300" font-family="Segoe UI,Helvetica,Arial,sans-serif"><rect x=".5" y=".5" width="399" height="299" rx="12" fill="{T["bg"]}" stroke="{T["bd"]}"/><text x="28" y="40" fill="{T["a"]}" font-size="18" font-weight="700">Top languages</text><clipPath id="c"><rect x="28" y="62" width="344" height="10" rx="5"/></clipPath><rect x="28" y="62" width="344" height="10" rx="5" fill="{T["tr"]}"/><g clip-path="url(#c)">{bar}</g>{leg}</svg>')
if __name__ == "__main__": write(fetch())
