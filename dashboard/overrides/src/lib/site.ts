import { DEFAULT_LANG } from "./i18n";
export interface SiteTranslations {
  siteTitle: string; titleSuffix: string; tagline: string; defaultDescription: string;
  citiesHeading: string; citiesDescription: string; cityCardCta: string; noCitiesYet: string;
  aboutNavLabel: string;
  footer: { aboutSection: string; projectsSection: string; contactSection: string;
    dataSource: string; dataAsOf: string; lastChecked: string; };
}
export const SITE_TRANSLATIONS: Record<string, SiteTranslations> = {
  sk: { siteTitle: "Mestá.DataTimes.sk", titleSuffix: " — Mestá.DataTimes.sk",
    tagline: "Prehľad menovitých hlasovaní mestských zastupiteľstiev",
    defaultDescription: "Hlasovania mestských zastupiteľstiev Bratislavy a Košíc, volebné obdobie 2022–2026.",
    citiesHeading: "Mestá", citiesDescription: "Vyberte mesto, ktorého zastupiteľstvo chcete preskúmať.",
    cityCardCta: "Zobraziť zastupiteľstvo →", noCitiesYet: "Pripravujeme dáta pre prvé mestá.", aboutNavLabel: "O projekte",
    footer: { aboutSection: "O projekte", projectsSection: "Naše projekty", contactSection: "Kontakt",
      dataSource: "Oficiálne archívy mestských zastupiteľstiev.", dataAsOf: "Dáta k {date}", lastChecked: "posledná kontrola {datetime}" } },
  en: { siteTitle: "Mestá.DataTimes.sk", titleSuffix: " — Mestá.DataTimes.sk",
    tagline: "Roll-call votes in Slovak city assemblies",
    defaultDescription: "Bratislava and Košice municipal assembly votes, 2022–2026.",
    citiesHeading: "Cities", citiesDescription: "Choose a city to explore its assembly.",
    cityCardCta: "View assembly →", noCitiesYet: "Preparing data for the first cities.", aboutNavLabel: "About",
    footer: { aboutSection: "About", projectsSection: "Our projects", contactSection: "Contact",
      dataSource: "Official municipal assembly archives.", dataAsOf: "Data as of {date}", lastChecked: "last checked {datetime}" } },
};
export function getSiteTranslations(lang: string): SiteTranslations {
  return SITE_TRANSLATIONS[lang] ?? SITE_TRANSLATIONS[DEFAULT_LANG]!;
}
