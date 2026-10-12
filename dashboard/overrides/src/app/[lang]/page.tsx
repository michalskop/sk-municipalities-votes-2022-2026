import Link from "next/link";
import { CITIES, PREPARED_CITIES, getCityTranslations } from "@/lib/city.config";
import { getSiteTranslations } from "@/lib/site";
import { cityBasePath } from "@/lib/routing";
import { buildGlobalMetadata } from "@/lib/metadata";
import { CityLogotype } from "@/components/CityLogotype";
import { SiteHeaderGlobal } from "@/components/SiteHeaderGlobal";
import { SiteFooterGlobal } from "@/components/SiteFooterGlobal";

interface Props { params: Promise<{ lang: string }>; }
export async function generateMetadata({ params }: Props) {
  return buildGlobalMetadata({ lang: (await params).lang, title: null });
}
export default async function LandingPage({ params }: Props) {
  const { lang } = await params;
  const t = getSiteTranslations(lang);
  return <>
    <SiteHeaderGlobal lang={lang} />
    <main className="flex-1 w-full max-w-5xl mx-auto px-4 py-8 space-y-10">
      <section className="flex flex-col items-center text-center gap-4 py-8">
        <CityLogotype size="lg" /><p className="text-muted-foreground text-lg max-w-xl">{t.tagline}</p>
      </section>
      <section className="space-y-4">
        <h1 className="text-2xl font-bold">{t.citiesHeading}</h1>
        <p className="text-sm text-muted-foreground">{t.citiesDescription}</p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {PREPARED_CITIES.map((city) => {
            const ct = getCityTranslations(city, lang);
            const ready = CITIES.some((c) => c.citySlug === city.citySlug);
            const content = <><h2 className="text-xl font-semibold mb-1">{ct.home.title}</h2>
              <p className="text-sm text-muted-foreground">{ct.home.description}</p></>;
            return ready ? <Link key={city.citySlug} href={cityBasePath(lang, city.citySlug)}
              className="block p-6 bg-surface-2 rounded-badge hover:bg-surface-3 transition-colors">
              {content}<p className="text-sm font-medium text-primary mt-3">{t.cityCardCta}</p>
            </Link> : <article key={city.citySlug} className="p-6 bg-surface-2 rounded-badge">
              {content}<p className="text-sm font-medium mt-3">{lang === "en" ? "Data in preparation" : "Dáta pripravujeme"}</p>
              <a href={city.sourceUrl} className="text-sm text-primary underline mt-2 inline-block">
                {lang === "en" ? "Official meeting archive ↗" : "Oficiálny archív zasadnutí ↗"}</a>
            </article>;
          })}
        </div>
      </section>
    </main><SiteFooterGlobal lang={lang} />
  </>;
}
