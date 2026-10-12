export interface AboutSection {
  title: string;
  paragraphs: Array<
    | { type: "text"; text: string }
    | { type: "list"; items: Array<{ label: string; description: string }> }
    | { type: "links"; items: Array<{ href: string; label: string; description: string }> }
    | { type: "external-link"; href: string; text: string; suffix?: string }
  >;
}
export interface AboutContent { pageTitle: string; intro: string; sections: AboutSection[]; backLabel: string; }
const sk: AboutContent = {
  pageTitle: "O projekte", intro: "Mestá.DataTimes.sk pripravuje prehľad menovitých hlasovaní mestských zastupiteľstiev Bratislavy a Košíc vo volebnom období 2022–2026.",
  backLabel: "← Späť na prehľad", sections: [
    { title: "Dáta a metodika", paragraphs: [{ type: "text", text: "Vychádzame z oficiálnych archívov zasadnutí. Účasť znamená podiel hlasovaní, v ktorých poslanec alebo poslankyňa hlasovali za, proti alebo sa zdržali. Nehlasovanie sa do účasti nezapočítava. V zdrojových dátach ho uchovávame oddelene od neprítomnosti. Rozsah spracovaných zasadnutí uvedieme pri zverejnení dát." }] },
    { title: "Stav prípravy", paragraphs: [{ type: "text", text: "Dáta zatiaľ nie sú zverejnené. Historické členstvo v kluboch ani zloženie koalícií ešte nie sú overené, preto klubové a koaličné metriky zatiaľ nezobrazujeme." }] },
    { title: "Zdroje", paragraphs: [{ type: "links", items: [
      { href: "https://zastupitelstvo.bratislava.sk/", label: "Bratislava", description: "Oficiálny archív zasadnutí" },
      { href: "https://www.kosice.sk/mesto/samosprava/mestske-zastupitelstvo/2022-2026", label: "Košice", description: "Oficiálny archív zasadnutí" },
    ] }] },
    { title: "Autori", paragraphs: [{ type: "links", items: [
      { href: "https://datatimes.sk", label: "DataTimes.sk", description: "" },
      { href: "https://kohovolit.eu", label: "KohoVolit.eu", description: "" },
    ] }] },
  ],
};
const en: AboutContent = {
  pageTitle: "About", intro: "Mestá.DataTimes.sk is preparing a roll-call vote dashboard for Bratislava and Košice city assemblies, 2022–2026.",
  backLabel: "← Back to overview", sections: [
    { title: "Data and methodology", paragraphs: [{ type: "text", text: "We use official meeting archives. Attendance is the share of eligible roll calls in which a member voted for, against, or abstained. Nonvoting does not count as participation, but remains distinct from recorded absence in the source data. Meeting coverage will be documented when data is published." }] },
    { title: "Preparation status", paragraphs: [{ type: "text", text: "Data has not yet been published. Historical council group membership and coalitions remain unverified, so group and coalition metrics are not displayed." }] },
    { title: "Sources", paragraphs: sk.sections[2]!.paragraphs },
    { title: "Authors", paragraphs: sk.sections[3]!.paragraphs },
  ],
};
export function getAboutContent(lang: string): AboutContent { return lang === "en" ? en : sk; }
export const aboutContent: Record<string, AboutContent> = { sk, en };
