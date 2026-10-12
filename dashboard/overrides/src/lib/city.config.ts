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
    id: slug, citySlug: slug, name, defaultLang: "sk", sourceUrl,
    dataBase: `${process.env.SK_DATA_BASE ?? "https://raw.githubusercontent.com/michalskop/sk-municipalities-votes-2022-2026/main"}/${slug}/analyses`,
    analyses: ["attendance"], hasVoteEvents: true, organizations: [],
    translations: { sk: dictionary(citySk, name), en: dictionary(cityEn, name) },
    pages: {
      home: [{ id: "attendance-swarm", config: { type: "swarm-chart", analysis: "attendance" },
        labels: { sk: { title: "Účasť na hlasovaniach", description: "Jeden bod predstavuje poslanca alebo poslankyňu. Kliknutím otvoríte profil." },
                  en: { title: "Attendance", description: "Each dot represents an assembly member. Click to open their profile." } } }],
      memberDetail: [{ id: "metrics-grid", config: { type: "metrics-grid" } },
        { id: "attendance-swarm", config: { type: "swarm-chart", analysis: "attendance" },
          labels: { sk: { title: "Účasť na hlasovaniach" }, en: { title: "Attendance" } } }],
      groupDetail: [],
    },
  };
}

export const PREPARED_CITIES: CityConfig[] = [
  city("bratislava", "Bratislava", "https://zastupitelstvo.bratislava.sk/"),
  city("kosice", "Košice", "https://www.kosice.sk/mesto/samosprava/mestske-zastupitelstvo/2022-2026"),
];
// Enable only after reviewed tables and attendance outputs are publicly available.
const published = new Set((process.env.SK_PUBLISHED_CITIES ?? "").split(",").filter(Boolean));
for (const slug of published) {
  if (!PREPARED_CITIES.some((c) => c.citySlug === slug)) throw new Error(`Unknown published city: ${slug}`);
}
export const CITIES = PREPARED_CITIES.filter((c) => published.has(c.citySlug));
export function getCityConfig(slug: string) { return CITIES.find((c) => c.citySlug === slug); }
export function getCitySlugs() { return CITIES.map((c) => c.citySlug); }
export function getCityTranslations(config: CityConfig, lang: string) {
  return config.translations[lang] ?? config.translations[config.defaultLang]!;
}
