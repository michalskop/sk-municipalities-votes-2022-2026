import VoteEventPage from "../../../../[lang]/[city]/vote-event/[id]/page";
import { DEFAULT_LANG } from "@/lib/i18n";

export function generateStaticParams() { return []; }
export const dynamicParams = true;
export const dynamic = "force-static";
export const revalidate = 3600;

export default function DefaultVoteEventPage({ params }: {
  params: Promise<{ lang: string; id: string }>;
}) {
  const localizedParams = params.then(({ lang: city, id }) => ({ city, id, lang: DEFAULT_LANG }));
  return <VoteEventPage params={localizedParams} />;
}
