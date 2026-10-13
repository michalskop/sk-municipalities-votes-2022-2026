import { Suspense } from "react";
import { notFound } from "next/navigation";
import type { VoteEventPartyGroup, VoteEventVoter } from "@legislature/charts";
import { PARTY_COLORS, PARTY_META } from "@/lib/parties";
import { groupIdToPartyId } from "@/lib/groups";
import { getCityConfig } from "@/lib/city.config";
import { getCityVoteEvent } from "@/lib/vote-events";
import { VoteEventView, VoteEventPresentation } from "@/components/VoteEventView";

// Generate and cache each vote on its first visit, then refresh hourly.
export function generateStaticParams() { return []; }
export const dynamicParams = true;
export const revalidate = 3600;

function buildGroups(votes: VoteEventVoter[], ungroupedLabel?: string): VoteEventPartyGroup[] {
  const byGroup = new Map<string, VoteEventVoter[]>();
  for (const v of votes) {
    const key = v.group_id ?? "other";
    const arr = byGroup.get(key) ?? [];
    arr.push(v);
    byGroup.set(key, arr);
  }

  // No fixed GROUP_ORDER here (unlike apps/cz-psp, which orders by a
  // hardcoded list of well-known party org IDs) — Praha's groups come from
  // D7's candidate-list fallback and aren't a stable "well-known" set the
  // way parliamentary party IDs are. Sort by voter count instead.
  const ordered = Array.from(byGroup.keys()).sort((a, b) => (byGroup.get(b)?.length ?? 0) - (byGroup.get(a)?.length ?? 0));

  return ordered.map((gid) => {
    const partyId = groupIdToPartyId(gid);
    const meta = PARTY_META[partyId];
    const color = PARTY_COLORS[partyId] ?? "#bcbcb0";
    return {
      group_id: gid,
      party_id: partyId,
      label: ungroupedLabel ?? meta?.shortName ?? gid,
      iconColor: color,
      iconAbbr: meta?.faceAbbr ?? partyId.toUpperCase(),
      iconTextColor: meta?.darkText ? "#1a1a1a" : "#ffffff",
      voters: byGroup.get(gid) ?? [],
    };
  });
}

export default async function VoteEventPage({ params }: {
  params: Promise<{ lang: string; city: string; id: string }>;
}) {
  const { lang, city: citySlug, id } = await params;
  const city = getCityConfig(citySlug);
  if (!city) notFound();
  const ve = await getCityVoteEvent(citySlug, id);
  if (!ve) notFound();
  const hasGroups = city.organizations.some((organization) => organization.classification === "group");
  const groups = buildGroups(ve.votes, hasGroups ? undefined : lang === "en" ? "Assembly members" : "Poslanci a poslankyne");
  const props = { ve, groups, hasGroups, lang };
  return (
    <Suspense fallback={<VoteEventPresentation {...props} />}>
      <VoteEventView {...props} />
    </Suspense>
  );
}
