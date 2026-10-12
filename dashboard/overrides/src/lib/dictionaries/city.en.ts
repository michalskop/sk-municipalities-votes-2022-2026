import type { CityTranslations } from "../city.config";

export const cityEn: CityTranslations = {
  nav: { overview: "Overview", members: "Assembly members" },
  member: {
    singular: "assembly member",
    plural: "Assembly members",
    current: "Current assembly members",
    former: "Former assembly members",
  },
  metrics: {
    attendance: "Attendance",
    rebelity: "Rebelliousness",
    govity: "Coalition alignment",
    corrections: "Vote corrections",
    wpca: "Voting positions (WPCA)",
  },
  ui: {
    memberCount: "{n} assembly members",
    voteCount: "of {total} votes",
    rebelVotes: "{n} rebellious votes",
    announcedCorrections: "{n} announced",
    outOf: "of",
    currentMembers: "Current assembly members",
    backToOverview: "← Back to overview",
  },
  home: {
    title: "{city} City Assembly",
    description:
      "Named votes of the {city} City Assembly for the 2022–2026 term and attendance by its members.",
    membersCardTitle: "Assembly members",
    membersCardDescription: "Assembly members and their attendance at votes.",
    groupsCardTitle: "Groups",
    groupsCardDescription: "Historical assembly-group membership has not yet been verified.",
  },
  about: { navLabel: "About" },
  seo: {
    siteTitle: "{city} City Assembly — Mestá.DataTimes.sk",
    titleSuffix: " — {city} — Mestá.DataTimes.sk",
    defaultDescription:
      "Named votes of the {city} City Assembly and member attendance for the 2022–2026 term.",
  },
  footer: {
    dataSource: "Data: official {city} city assembly archive, 2022–2026 term",
    aboutSection: "About",
    projectsSection: "Our projects",
    contactSection: "Contact",
  },
  table: {
    allFilter: "All",
    sortAsc: "Sort ascending",
    sortDesc: "Sort descending",
    name: "Assembly member",
    party: "Group",
    attendance: "Attendance",
    rebelity: "Rebelliousness",
    govity: "Coalition alignment",
    corrections: "Vote corrections",
  },
  charts: {
    average: "Average",
    wpca: {
      govAxisLabelPositive: "Coalition",
      govAxisLabelNegative: "Coalition",
      otherAxisLabel: "Voting",
    },
  },
};
