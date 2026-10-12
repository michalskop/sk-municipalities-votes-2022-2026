"""Compose a Slovak app from the existing dashboard without editing its checkout.

The output is an isolated monorepo preview and a reviewable apps/sk-cities addition.
"""
import argparse
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TEMPLATE = Path("/home/michal/project/legislature-dashboard")


def replace_required(path, old, new):
    text = path.read_text()
    if old not in text:
        raise ValueError(f"Dashboard template changed; inspect {path}: missing {old!r}")
    path.write_text(text.replace(old, new))


def prepare(template, out, reuse_dependencies=False):
    if out.exists():
        raise ValueError(f"Output already exists; choose a new empty path: {out}")
    app = out / "apps/sk-cities"
    template_app = template / "apps/cz-cities"
    shutil.copytree(template_app, app, ignore=shutil.ignore_patterns(
        "node_modules", ".next", "*.tsbuildinfo", "data", "dictionaries", "public", "scripts",
        ".env*", "DIVERGENCE.md"))
    shutil.copytree(ROOT / "dashboard/overrides", app, dirs_exist_ok=True)
    shutil.copytree(template / "packages", out / "packages", ignore=shutil.ignore_patterns(
        "node_modules", "*.tsbuildinfo", "dist", ".turbo"))
    for name in ("package.json", "pnpm-workspace.yaml", "tsconfig.base.json", "turbo.json"):
        shutil.copy2(template / name, out / name)
    package = json.loads((app / "package.json").read_text())
    package["name"] = "@legislature/sk-cities"
    package["scripts"].pop("prebuild", None)
    package["scripts"]["dev"] = "next dev --port 3014"
    package["scripts"]["lint"] = "eslint ."
    (app / "package.json").write_text(json.dumps(package, indent=2) + "\n")
    public = app / "public"
    public.mkdir()
    shutil.copy2(template_app / "public/favicon.svg", public / "favicon.svg")
    (public / "robots.txt").write_text("User-agent: *\nAllow: /\n")

    # Known, checked changes to the existing app; routes/components/packages stay shared.
    replace_required(app / "src/lib/i18n.ts", 'code: "cs"', 'code: "sk"')
    replace_required(app / "src/lib/metadata.ts", "mesta.datatimes.cz", "mesta.datatimes.sk")
    replace_required(app / "next.config.ts", "reactStrictMode: true,",
                     "reactStrictMode: true,\n  experimental: { cpus: 1 },")
    replace_required(app / "src/app/[lang]/about/page.tsx", 'aboutContent["cs"]', 'aboutContent["sk"]')
    data = app / "src/lib/data.ts"
    for analysis, func in (("rebelity", "fetchRebelity"), ("govity", "fetchGovity"), ("wpca", "fetchWpca")):
        replace_required(data, f"    {func}(citySlug),",
                         f'    getCityConfig(citySlug)?.analyses.includes("{analysis}") ? {func}(citySlug) : Promise.resolve([]),')

    # Avoid assigning Czech party brands to members with unverified Slovak affiliations.
    (app / "src/lib/parties.ts").write_text('''export const PARTY_META: Record<string, { shortName: string; faceAbbr: string; darkText?: boolean }> = {
  other: { shortName: "Bez overeného klubu", faceAbbr: "—", darkText: true },
};
export const PARTY_COLORS: Record<string, string> = { other: "#bcbcb0" };
''')
    translations = {
        "Města.DataTimes.cz": "Mestá.DataTimes.sk", "Města": "Mestá",
        "cs-CZ": "sk-SK", "Europe/Prague": "Europe/Bratislava",
        '["cs", "en"]': '["sk", "en"]',
        'Hlasování': 'Hlasovania', 'Zastupitelé': 'Poslanci a poslankyne',
        'Pro toto město zatím nejsou dostupná žádná jmenovitá hlasování.': 'Pre toto mesto zatiaľ nie sú dostupné menovité hlasovania.',
        'se zdrželo': 'sa zdržalo', 'nehlasovalo / chybělo': 'nehlasovalo / chýbalo',
        'Schváleno': 'Schválené', 'Zamítnuto': 'Zamietnuté', 'Zdržel se / nepřítomen': 'Zdržal sa / neprítomný',
        'prostá většina': 'jednoduchá väčšina', 'absolutní většina': 'absolútna väčšina',
        '3/5 většina': '3/5 väčšina', '2/3 většina': '2/3 väčšina', 'potřebné': 'potrebné',
        'Volební kalkulačka': 'Volebná kalkulačka',
    }
    for path in (app / "src").rglob("*"):
        if path.suffix not in (".ts", ".tsx"):
            continue
        text = path.read_text()
        for old, new in translations.items():
            text = text.replace(old, new)
        if "[city]" in path.parts:
            # Next cannot enumerate nested static params when no city is published.
            # Runtime city.config lookup still rejects every unconfigured city.
            text = text.replace("export const dynamicParams = false;", "export const dynamicParams = true;")
        path.write_text(text)
    # The preview builds offline with the same serif fallback from the shared tokens.
    layout = app / "src/app/[lang]/layout.tsx"
    text = layout.read_text().replace('import { Roboto_Slab } from "next/font/google";\n', "")
    start, end = text.index("const robotoSlab ="), text.index("// This IS")
    text = text[:start] + text[end:]
    text = text.replace('className={`${robotoSlab.variable} overflow-x-hidden`}', 'className="overflow-x-hidden"')
    layout.write_text(text)
    css = app / "src/app/globals.css"
    css.write_text(css.read_text() + '\n:root { --font-roboto-slab: Georgia; }\n')
    if reuse_dependencies:
        # Opt-in for local QA only. These absolute symlinks are not deployment artifacts.
        (out / "node_modules").symlink_to(template / "node_modules", target_is_directory=True)
        (app / "node_modules").symlink_to(template_app / "node_modules", target_is_directory=True)
        for package_dir in (out / "packages").iterdir():
            deps = template / "packages" / package_dir.name / "node_modules"
            if deps.exists():
                (package_dir / "node_modules").symlink_to(deps, target_is_directory=True)
    revision = subprocess.run(["git", "-C", str(template), "rev-parse", "HEAD"],
                              capture_output=True, text=True)
    (out / "TEMPLATE.json").write_text(json.dumps({"path": str(template),
        "revision": revision.stdout.strip() or None, "app": "apps/cz-cities",
        "target": "apps/sk-cities", "dependencies_reused": reuse_dependencies}, indent=2) + "\n")
    print(f"Prepared {app}; original dashboard checkout unchanged")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--reuse-dependencies", action="store_true", help="Local QA with installed template dependencies")
    args = parser.parse_args()
    prepare(args.template, args.out, args.reuse_dependencies)
