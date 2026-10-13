import { cache } from "react";
import type { VoteEventVoter, VoteEventPolarityCounts } from "@legislature/charts";
import { getCityConfig } from "./city.config";

export interface CityVoteEventSummary {
  id: string;
  start_date: string;
  title: string;
  result: "pass" | "fail" | null;
  polarity_counts: VoteEventPolarityCounts;
  option_counts: { abstain: number; did_not_vote: number };
}

export interface CityVoteEvent extends CityVoteEventSummary {
  parliament_id: string;
  identifier?: string;
  topic_description?: string;
  requirement?: string;
  required_count?: number;
  definition_name: string | null;
  votes: VoteEventVoter[];
}

const REVALIDATE = 3600;
function dataBaseFor(citySlug: string) {
  const city = getCityConfig(citySlug);
  if (!city) throw new Error(`Unknown citySlug: ${citySlug}`);
  return `${city.dataBase.replace(/\/analyses$/, "/data")}/dashboard`;
}

export const getCityVoteEvents = cache(async (citySlug: string): Promise<CityVoteEventSummary[]> => {
  const base = dataBaseFor(citySlug);
  const response = await fetch(`${base}/index.json`, { next: { revalidate: REVALIDATE } });
  if (!response.ok) throw new Error(`Failed to fetch vote index: ${response.status}`);
  const index = await response.json() as { version: number; count: number; pages: string[] };
  if (index.version !== 1 || !index.pages.every((name) => /^summaries\/\d{4}\.json$/.test(name))) {
    throw new Error("Invalid dashboard vote index");
  }
  const pages = await Promise.all(index.pages.map(async (name) => {
    const response = await fetch(`${base}/${name}`, { next: { revalidate: REVALIDATE } });
    if (!response.ok) throw new Error(`Failed to fetch vote summaries: ${response.status}`);
    return await response.json() as CityVoteEventSummary[];
  }));
  return pages.flat();
});

export async function getCityVoteEvent(citySlug: string, id: string): Promise<CityVoteEvent | null> {
  try { id = decodeURIComponent(id); } catch { return null; }
  const prefix = `${citySlug}:vote-event:`;
  const fileId = id.startsWith(prefix) ? id.slice(prefix.length) : id;
  if (!/^[A-Za-z0-9._-]+$/.test(fileId) || fileId === "." || fileId === "..") return null;
  const response = await fetch(`${dataBaseFor(citySlug)}/vote-events/${fileId}.json`, {
    next: { revalidate: REVALIDATE },
  });
  if (response.status === 404) return null;
  if (!response.ok) throw new Error(`Failed to fetch vote event: ${response.status}`);
  const event = await response.json() as CityVoteEvent;
  return event.id === `${prefix}${fileId}` ? event : null;
}
