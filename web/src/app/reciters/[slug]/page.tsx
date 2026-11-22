import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { ReciterProfileScreen } from "@/components/ReciterProfileScreen";
import { displayName, getProfile, PROFILES } from "@/lib/reciterProfiles";

type Params = Promise<{ slug: string }>;

// Every profile is known at build time, so each gets its own static page.
// Any other address renders the not-found page.
export function generateStaticParams() {
  return PROFILES.map((profile) => ({ slug: profile.id }));
}

export async function generateMetadata({
  params,
}: {
  params: Params;
}): Promise<Metadata> {
  const profile = getProfile((await params).slug);
  if (!profile) return {};
  return {
    title: displayName(profile),
    description:
      profile.short_bio_ar ??
      `صفحة القارئ ${displayName(profile)} في مكتبة أنصِت.`,
  };
}

export default async function ReciterProfilePage({
  params,
}: {
  params: Params;
}) {
  const profile = getProfile((await params).slug);
  if (!profile) notFound();
  return <ReciterProfileScreen profile={profile} />;
}
