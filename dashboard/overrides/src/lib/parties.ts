// Party/group display metadata (colors, short names, face abbreviations)
// for Slovak municipal councils (Bratislava and Košice, 2022-2026).

export const PARTY_META: Record<
  string,
  { shortName: string; faceAbbr: string; darkText?: boolean }
> = {
  // Bratislava council clubs
  "team-bratislava-ps-sas": { shortName: "Team BA, PS, SaS", faceAbbr: "TB" },
  "klub-starostov": { shortName: "Klub starostov", faceAbbr: "KS" },
  "klub-som-bratislava": { shortName: "SOM Bratislava", faceAbbr: "SOM" },

  // Košice council clubs
  "kosicky-klub": { shortName: "Košický klub", faceAbbr: "KK" },
  "starostovia-a-nezavisli": { shortName: "Starostovia a nezávislí", faceAbbr: "SaN" },
  "spolupraca-pre-kosice": { shortName: "Spolupráca pre Košice", faceAbbr: "SpK" },

  // Independent / unaffiliated (both cities)
  nezaradeni: { shortName: "Nezaradení", faceAbbr: "NEZ", darkText: true },
  other: { shortName: "Bez overeného klubu", faceAbbr: "—", darkText: true },
};

export const PARTY_COLORS: Record<string, string> = {
  // Bratislava
  "team-bratislava-ps-sas": "#009eb3",
  "klub-starostov": "#f97316",
  "klub-som-bratislava": "#2563eb",

  // Košice
  "kosicky-klub": "#0284c7",
  "starostovia-a-nezavisli": "#16a34a",
  "spolupraca-pre-kosice": "#e11d48",

  // Independent / fallback
  nezaradeni: "#94a3b8",
  other: "#bcbcb0",
};
