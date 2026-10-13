"use client";

import { useSearchParams } from "next/navigation";
import { VoteEventGrid } from "@legislature/charts";
import type { VoteEventPartyGroup } from "@legislature/charts";
import type { CityVoteEvent } from "@/lib/vote-events";
import { CityLogotype } from "@/components/CityLogotype";

const REQUIREMENT_LABELS: Record<string, string> = {
  "simple majority": "jednoduchá väčšina",
  "absolute majority": "absolútna väčšina",
  "3/5": "3/5 väčšina",
  "2/3": "2/3 väčšina",
};

const LAYOUTS = [
  { key: "wp", label: "Hlasovania" },
  { key: "tabule", label: "Tabule" },
  { key: "polarity-first", label: "Podľa výsledku" },
  { key: "party-first", label: "Podľa klubu" },
] as const;

type Layout = (typeof LAYOUTS)[number]["key"];

function isLayout(v: string | undefined): v is Layout {
  return LAYOUTS.some((l) => l.key === v);
}

interface Props {
  ve: CityVoteEvent;
  groups: VoteEventPartyGroup[];
  hasGroups: boolean;
  lang: string;
}

export function VoteEventView(props: Props) {
  const searchParams = useSearchParams();
  const raw = searchParams.get("layout") ?? undefined;
  const layout = isLayout(raw) && (props.hasGroups || raw !== "party-first") ? raw : "wp";
  return <VoteEventPresentation {...props} layout={layout} />;
}

export function VoteEventPresentation({ ve, groups, hasGroups, lang, layout = "wp" }: Props & { layout?: Layout }) {
  const availableLayouts = hasGroups ? LAYOUTS : LAYOUTS.filter((item) => item.key !== "party-first");
  const isEnglish = lang === "en";
  return (
    <div className="space-y-4">
      <div className="flex gap-1">
        {availableLayouts.map((l) => (
          <a
            key={l.key}
            href={`?layout=${l.key}`}
            aria-current={layout === l.key ? "true" : undefined}
            onClick={(event) => {
              if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
              event.preventDefault();
              const url = new URL(window.location.href);
              url.searchParams.set("layout", l.key);
              window.history.pushState(null, "", url);
            }}
            className={`rounded px-3 py-1 text-sm font-medium transition-colors ${
              layout === l.key
                ? "bg-primary text-primary-foreground"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            {isEnglish
              ? ({ wp: "Vote", tabule: "Board", "polarity-first": "By result", "party-first": "By group" } as const)[l.key]
              : l.label}
          </a>
        ))}
      </div>
      <VoteEventGrid
        title={ve.title ?? ve.id}
        date={ve.start_date}
        result={ve.result}
        requirement={ve.requirement ? (REQUIREMENT_LABELS[ve.requirement] ?? ve.requirement) : undefined}
        requirementCountLabel="potrebné"
        logo={<CityLogotype size="xs" variant="mono" color="var(--color-surface-8)" />}
        required_count={ve.required_count}
        polarity_counts={ve.polarity_counts}
        groups={groups}
        dotSize={16}
        layout={layout}
        resultLabels={isEnglish ? { pass: "Passed", fail: "Rejected" } : { pass: "Schválené", fail: "Zamietnuté" }}
        polarityLabels={isEnglish
          ? { support: "For", oppose: "Against", neutral: "Abstained / absent" }
          : { support: "Pro", oppose: "Proti", neutral: "Zdržal sa / neprítomný" }}
      />
      {(ve.identifier || ve.topic_description) && (
        <section className="space-y-2 rounded border border-border bg-surface-0 p-4 text-sm">
          {ve.identifier && <p className="font-semibold">{ve.identifier}</p>}
          {ve.topic_description && <p className="whitespace-pre-wrap text-muted-foreground">{ve.topic_description}</p>}
        </section>
      )}
    </div>
  );
}
