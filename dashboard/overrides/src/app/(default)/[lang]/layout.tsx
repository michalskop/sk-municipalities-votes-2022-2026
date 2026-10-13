import CityLayout from "../../[lang]/[city]/layout";
import { CITIES } from "@/lib/city.config";
import { DEFAULT_LANG } from "@/lib/i18n";

// Next.js requires the same first-segment parameter name in both route trees.
// For these unprefixed vote URLs, the segment value is the city slug.
export function generateStaticParams() {
  return CITIES.map((city) => ({ lang: city.citySlug }));
}
export const dynamicParams = true;

export default function DefaultCityLayout({ children, params }: {
  children: React.ReactNode;
  params: Promise<{ lang: string }>;
}) {
  const localizedParams = params.then(({ lang: city }) => ({ city, lang: DEFAULT_LANG }));
  return <CityLayout params={localizedParams}>{children}</CityLayout>;
}
