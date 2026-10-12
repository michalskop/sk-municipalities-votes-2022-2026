import type { ParliamentConfig, ParliamentTranslations } from "@legislature/parliament-core";
import { cityEn } from "./dictionaries/city.en";
import { citySk } from "./dictionaries/city.sk";

export type CityTranslations = Omit<ParliamentTranslations, "charts"> & {
  charts: { average: string; wpca: {
    govAxisLabelPositive: string; govAxisLabelNegative: string; otherAxisLabel: string;
  } };
};
export type CityConfig = Omit<ParliamentConfig, "translations"> & {
  citySlug: string;
  hasVoteEvents?: boolean;
  sourceUrl: string;
  translations: Record<string, CityTranslations>;
};

function dictionary(template: CityTranslations, name: string): CityTranslations {
  return JSON.parse(JSON.stringify(template).replaceAll("{city}", name)) as CityTranslations;
}

function city(slug: string, name: string, sourceUrl: string): CityConfig {
  return {
    id: slug,
    citySlug: slug,
    name,
    defaultLang: "sk",
    sourceUrl,
    dataBase: `${process.env.SK_DATA_BASE ?? "https://raw.githubusercontent.com/michalskop/sk-municipalities-votes-2022-2026/main"}/${slug}/analyses`,
    analyses: ["attendance", "rebelity", "govity", "wpca"],
    hasVoteEvents: true,
    organizations: [
      {
        classification: "group",
        urlSegment: "group",
        listUrlSegment: "groups",
        hasPage: true,
        labels: {
          sk: { singular: "klub", plural: "kluby", listTitle: "Poslanecké kluby" },
          en: { singular: "group", plural: "groups", listTitle: "Council groups" },
        },
      },
    ],
    translations: { sk: dictionary(citySk, name), en: dictionary(cityEn, name) },
    pages: {
      home: [
        {
          id: "attendance-swarm",
          config: {
            type: "swarm-chart",
            analysis: "attendance",
            referenceLines: [{ value: 0.5, label: "50 %" }],
          },
          labels: {
            sk: { title: "Účasť na hlasovaniach", description: "Jeden bod = jeden poslanec/poslankyňa. Kliknutím prejdete na ich profil." },
            en: { title: "Attendance", description: "Each dot = one assembly member. Click to open their profile." },
          },
        },
        {
          id: "wpca-scatter",
          config: { type: "scatter-chart", analysis: "wpca" },
          labels: {
            sk: { title: "Pozícia na základe hlasovaní", description: "2D mapa poslancov podľa spôsobu hlasovania (WPCA). Kliknutím prejdete na ich profil." },
            en: { title: "Positions based on voting behaviour", description: "2D map of assembly members by voting patterns (WPCA). Click to open their profile." },
          },
        },
        {
          id: "rebelity-swarm",
          config: { type: "swarm-chart", analysis: "rebelity", yMode: "auto", yDecimals: 1 },
          labels: {
            sk: { title: "Rebelovanie", description: "Ako často poslanec/poslankyňa hlasuje proti svojmu klubu." },
            en: { title: "Rebelliousness", description: "How often the assembly member votes against their own group." },
          },
        },
        {
          id: "govity-swarm",
          config: { type: "swarm-chart", analysis: "govity", yMode: "auto", yDecimals: 1 },
          labels: {
            sk: { title: "Zhoda s vedením mesta", description: "Ako často poslanec/poslankyňa hlasuje zhodne s vedením mesta." },
            en: { title: "Coalition alignment", description: "How often the assembly member votes in line with the city leadership." },
          },
        },
      ],
      memberDetail: [
        { id: "metrics-grid", config: { type: "metrics-grid" } },
        {
          id: "attendance-swarm",
          config: {
            type: "swarm-chart",
            analysis: "attendance",
            referenceLines: [{ value: 0.5, label: "50 %" }],
          },
          labels: {
            sk: { title: "Účasť na hlasovaniach", description: "Pozícia v rámci zastupiteľstva." },
            en: { title: "Attendance", description: "Position within the assembly." },
          },
        },
        {
          id: "wpca-scatter",
          config: { type: "scatter-chart", analysis: "wpca" },
          labels: {
            sk: { title: "Pozícia na základe hlasovaní", description: "Poloha na základe analýzy hlasovaní." },
            en: { title: "Positions based on voting behaviour", description: "Position based on voting analysis." },
          },
        },
        {
          id: "rebelity-swarm",
          config: { type: "swarm-chart", analysis: "rebelity", yMode: "auto", yDecimals: 1 },
          labels: {
            sk: { title: "Rebelovanie", description: "Ako často hlasuje proti svojmu klubu." },
            en: { title: "Rebelliousness", description: "How often they vote against their group." },
          },
        },
        {
          id: "govity-swarm",
          config: { type: "swarm-chart", analysis: "govity", yMode: "auto", yDecimals: 1 },
          labels: {
            sk: { title: "Zhoda s vedením mesta", description: "Ako často hlasuje zhodne s vedením mesta." },
            en: { title: "Coalition alignment", description: "How often they vote in line with the city leadership." },
          },
        },
      ],
      groupDetail: [
        { id: "metrics-grid", config: { type: "metrics-grid" } },
        {
          id: "wpca-scatter",
          config: { type: "scatter-chart", analysis: "wpca" },
          labels: {
            sk: { title: "Pozícia na základe hlasovaní", description: "Členovia klubu v kontexte celého zastupiteľstva." },
            en: { title: "Positions based on voting behaviour", description: "Group members in the context of the full assembly." },
          },
        },
        {
          id: "member-table",
          config: { type: "member-table", showPartyFilter: false },
          labels: {
            sk: { title: "Členovia klubu" },
            en: { title: "Group members" },
          },
        },
      ],
    },
  };
}

export const PREPARED_CITIES: CityConfig[] = [
  city("bratislava", "Bratislava", "https://zastupitelstvo.bratislava.sk/"),
  city("kosice", "Košice", "https://www.kosice.sk/mesto/samosprava/mestske-zastupitelstvo/2022-2026"),
];

const published = new Set((process.env.SK_PUBLISHED_CITIES ?? "bratislava,kosice").split(",").filter(Boolean));
for (const slug of published) {
  if (!PREPARED_CITIES.some((c) => c.citySlug === slug)) throw new Error(`Unknown published city: ${slug}`);
}
export const CITIES = PREPARED_CITIES.filter((c) => published.has(c.citySlug));
export function getCityConfig(slug: string) { return CITIES.find((c) => c.citySlug === slug); }
export function getCitySlugs() { return CITIES.map((c) => c.citySlug); }
export function getCityTranslations(config: CityConfig, lang: string) {
  return config.translations[lang] ?? config.translations[config.defaultLang]!;
}
