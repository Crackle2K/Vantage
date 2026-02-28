import type { KeyboardEvent } from 'react';
import { CheckCircle2, Eye, Heart, MapPin } from 'lucide-react';
import { cn } from '@/lib/utils';
import { BusinessImage } from '@/components/explore/BusinessImage';
import { buildApiUrl } from '@/api';
import type { Business } from '@/types';

interface BusinessCardProps {
  business: Business;
  trustReasons: string[];
  isFavorite: boolean;
  onToggleFavorite: () => void;
  onViewDetails?: () => void;
  viewMode?: 'grid' | 'feed';
  matchSummary?: string | null;
}

const IMAGE_ASPECTS = ['aspect-[4/5]', 'aspect-[1/1]', 'aspect-[6/5]', 'aspect-[5/6]', 'aspect-[4/4.5]'] as const;

function distanceLabel(distance?: number): string | null {
  if (typeof distance !== 'number') {
    return null;
  }
  return `${distance.toFixed(1)} km away`;
}

function imageAspectClass(business: Business): string {
  const seed = `${business.id || business._id || business.name}:${business.category || ''}`;
  const hash = Array.from(seed).reduce((sum, char) => sum + char.charCodeAt(0), 0);
  return IMAGE_ASPECTS[hash % IMAGE_ASPECTS.length];
}

function prioritizeImageCandidates(business: Business, proxyPhotoUrl?: string): string[] {
  const rawCandidates = [business.primary_image_url, business.image_url, ...(business.image_urls ?? []), business.image, proxyPhotoUrl]
    .filter((value): value is string => !!value && value.trim().length > 0);
  const seen = new Set<string>();
  const directPhotos: string[] = [];
  const proxyPhotos: string[] = [];
  const placeholders: string[] = [];

  rawCandidates.forEach((candidate) => {
    if (seen.has(candidate)) {
      return;
    }
    seen.add(candidate);

    if (candidate.startsWith('data:image')) {
      placeholders.push(candidate);
      return;
    }

    if (candidate.includes('/api/photos?')) {
      proxyPhotos.push(candidate);
      return;
    }

    directPhotos.push(candidate);
  });

  return [...directPhotos, ...proxyPhotos, ...placeholders];
}

function buildCardDescription(business: Business): string {
  const shortDescription = (business.short_description || '').trim();
  const longDescription = (business.description || '').trim();
  const categoryLabel = (business.category || 'local business').toLowerCase();
  const tags = (business.known_for ?? []).slice(0, 3);
  const locationLine = business.address ? `Located at ${business.address}.` : 'Located nearby for easy discovery.';

  if (longDescription && longDescription.length > shortDescription.length + 24) {
    return longDescription;
  }

  if (shortDescription && longDescription && shortDescription !== longDescription) {
    return `${shortDescription} ${longDescription}`;
  }

  if (shortDescription) {
    if (tags.length > 0) {
      return `${shortDescription} Guests usually come here for ${tags.join(', ').toLowerCase()}. ${locationLine}`;
    }
    return `${shortDescription} This ${categoryLabel} is a dependable option in the area. ${locationLine}`;
  }

  if (longDescription) {
    return `${longDescription} ${locationLine}`;
  }

  if (tags.length > 0) {
    return `A trusted ${categoryLabel} nearby. Guests usually come here for ${tags.join(', ').toLowerCase()}. ${locationLine}`;
  }

  return `A trusted ${categoryLabel} nearby. It is a dependable local option when you want something close. ${locationLine}`;
}

export function BusinessCard({
  business,
  trustReasons,
  isFavorite,
  onToggleFavorite,
  onViewDetails,
  viewMode = 'grid',
  matchSummary,
}: BusinessCardProps) {
  const distance = distanceLabel(business.distance);
  const finalScore = business.ranking_components?.final_score ?? business.canonical_rank_score;
  const cardDescription = buildCardDescription(business);
  const knownFor = business.known_for ?? [];
  const imageAspect = imageAspectClass(business);
  const proxyPhotoUrl = business.place_id
    ? buildApiUrl(`/api/photos?place_id=${encodeURIComponent(business.place_id)}&maxwidth=${viewMode === 'grid' ? 1200 : 900}`)
    : undefined;
  const imageCandidates = prioritizeImageCandidates(business, proxyPhotoUrl);
  const statusLabel = business.is_active_today
    ? 'New & Active'
    : business.is_claimed
    ? 'Claimed'
    : business.has_deals
    ? 'Deal'
    : null;
  const canOpenDetails = typeof onViewDetails === 'function';
  const handleKeyDown = (event: KeyboardEvent<HTMLElement>) => {
    if (!canOpenDetails) {
      return;
    }
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      onViewDetails();
    }
  };

  return (
    <article
      onClick={onViewDetails}
      onKeyDown={handleKeyDown}
      role={canOpenDetails ? 'button' : undefined}
      tabIndex={canOpenDetails ? 0 : undefined}
      aria-label={canOpenDetails ? `View ${business.name}` : undefined}
      className={cn(
        'group overflow-hidden transition-all duration-300 motion-reduce:transition-none',
        canOpenDetails && 'cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[hsl(var(--primary))/0.45] focus-visible:ring-offset-2 focus-visible:ring-offset-[hsl(var(--background))]',
        viewMode === 'grid'
          ? 'break-inside-avoid rounded-[22px] bg-transparent hover:-translate-y-1 hover:scale-[1.01] motion-reduce:hover:translate-y-0 motion-reduce:hover:scale-100'
          : 'flex flex-col rounded-[26px] border border-[hsl(var(--border))/0.85] bg-[hsl(var(--card))] shadow-[0_14px_34px_-24px_hsl(var(--shadow-soft)/0.65)] hover:-translate-y-0.5 hover:shadow-[0_18px_38px_-24px_hsl(var(--shadow-soft)/0.68)] motion-reduce:hover:translate-y-0'
      )}
    >
      <div
        className={cn(
          'relative overflow-hidden bg-[hsl(var(--secondary))]',
          viewMode === 'grid'
            ? `${imageAspect} min-h-[320px] rounded-[22px] shadow-[0_22px_48px_-28px_hsl(var(--shadow-soft)/0.82)]`
            : 'aspect-[16/9] sm:min-h-full sm:w-[320px] sm:flex-shrink-0 sm:aspect-auto'
        )}
      >
        <div className="absolute inset-0">
          <BusinessImage
            key={imageCandidates.join('|') || business.name}
            primaryImage={imageCandidates[0]}
            imageCandidates={imageCandidates}
            category={business.category}
            alt={business.name}
            className="h-full w-full object-cover"
          />
        </div>
        <div className={cn('absolute inset-x-0 bottom-0 h-24 bg-gradient-to-t from-black/80 via-black/25 to-transparent', viewMode === 'grid' && 'h-20 from-black/62 via-black/18')} />

        <div className="absolute left-3 right-3 top-3 flex items-start justify-between gap-2">
          <div className="flex flex-wrap gap-2">
            <span className="rounded-full border border-white/20 bg-black/35 px-2.5 py-1 text-caption font-medium text-white backdrop-blur-sm">
              {business.category}
            </span>
            <span className="rounded-full border border-[hsl(var(--primary))/0.22] bg-[hsl(var(--primary))/0.22] px-2.5 py-1 text-caption font-medium text-white backdrop-blur-sm">
              {business.live_visibility_score ? `Trust ${Math.round(business.live_visibility_score)}` : 'Trust-ranked'}
            </span>
          </div>

          <button
            type="button"
            onClick={(event) => {
              event.stopPropagation();
              onToggleFavorite();
            }}
            className={cn(
              'flex h-10 w-10 items-center justify-center rounded-full border border-white/20 bg-black/40 text-white backdrop-blur-sm transition-all duration-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/70 focus-visible:ring-offset-2 focus-visible:ring-offset-black/20',
              viewMode === 'grid' && 'opacity-100 sm:translate-y-1 sm:opacity-0 sm:group-hover:translate-y-0 sm:group-hover:opacity-100',
              isFavorite && 'border-[hsl(var(--primary))/0.35] bg-[hsl(var(--primary))/0.28] text-white'
            )}
            aria-label={isFavorite ? 'Remove favorite' : 'Save favorite'}
          >
            <Heart className={cn('h-4 w-4', isFavorite && 'fill-current')} />
          </button>
        </div>

        <div className="absolute bottom-3 left-3 right-3 flex items-end justify-between gap-3">
          {viewMode === 'feed' ? (
            <div className="min-w-0">
              <p className="truncate text-caption font-semibold uppercase tracking-[0.16em] text-white/70">
                {statusLabel || 'Trust-first local'}
              </p>
              <h3 className="line-clamp-2 font-sub text-xl font-semibold leading-tight text-white">
                {business.name}
              </h3>
            </div>
          ) : (
            <p className="rounded-full border border-white/12 bg-black/28 px-2.5 py-1 text-caption font-semibold uppercase tracking-[0.14em] text-white/84 backdrop-blur-sm">
              {statusLabel || 'Live now'}
            </p>
          )}
          {distance && (
            <span className="inline-flex items-center gap-1 rounded-full border border-white/15 bg-black/35 px-2.5 py-1 text-caption text-white/90 backdrop-blur-sm">
              <MapPin className="h-3.5 w-3.5" />
              {distance}
            </span>
          )}
        </div>
      </div>

      <div className={cn('space-y-3', viewMode === 'grid' ? 'px-1 pb-1 pt-3' : 'p-4 sm:p-5')}>
        <div>
          <h3 className={cn('font-sub font-semibold leading-tight text-[hsl(var(--foreground))]', viewMode === 'grid' ? 'line-clamp-2 text-[1.1rem]' : 'line-clamp-2 text-xl')}>
            {business.name}
          </h3>
          {viewMode === 'feed' && (
            <p className="mt-1 line-clamp-1 text-caption uppercase tracking-[0.14em] text-[hsl(var(--muted-foreground))]">
              {business.address || 'Toronto'}
            </p>
          )}
        </div>
        {matchSummary && (
          <div className="inline-flex max-w-full items-center rounded-full border border-[hsl(var(--primary))/0.18] bg-[hsl(var(--primary))]/0.08 px-3 py-1 text-caption text-[hsl(var(--foreground))]">
            <span className="truncate">Matches your interests: {matchSummary}</span>
          </div>
        )}
        {viewMode === 'feed' && cardDescription && (
          <p className="line-clamp-4 text-ui text-[hsl(var(--foreground))/0.86]">
            {cardDescription}
          </p>
        )}
        {knownFor.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {knownFor.slice(0, viewMode === 'grid' ? 3 : 5).map((tag) => (
              <span
                key={tag}
                className={cn(
                  'rounded-full border px-2.5 py-1 text-caption',
                  viewMode === 'grid'
                    ? 'border-[hsl(var(--border))/0.7] bg-[hsl(var(--card))] text-[hsl(var(--muted-foreground))]'
                    : 'border-[hsl(var(--border))] bg-[hsl(var(--secondary))]/0.95 text-[hsl(var(--muted-foreground))]'
                )}
              >
                {tag}
              </span>
            ))}
          </div>
        )}

        {viewMode === 'grid' ? (
          <div className="flex items-center justify-between gap-3 pt-1">
            <div className="flex flex-wrap gap-2">
              {typeof finalScore === 'number' && (
                <span className="inline-flex items-center gap-1 rounded-full border border-[hsl(var(--primary))/0.18] bg-[hsl(var(--primary))/0.08] px-2.5 py-1 text-caption text-[hsl(var(--foreground))]">
                  <CheckCircle2 className="h-3.5 w-3.5 text-[hsl(var(--primary))]" />
                  {Math.round(finalScore)}
                </span>
              )}
              {trustReasons.slice(0, 1).map((reason) => (
                <span
                  key={reason}
                  className="inline-flex items-center gap-1 rounded-full border border-[hsl(var(--border))] bg-[hsl(var(--background))/0.8] px-2.5 py-1 text-caption text-[hsl(var(--muted-foreground))]"
                >
                  {reason}
                </span>
              ))}
            </div>
            <span className="text-caption font-medium text-[hsl(var(--muted-foreground))] transition-colors group-hover:text-[hsl(var(--foreground))]">
              Open
            </span>
          </div>
        ) : (
        <div className={cn('flex items-center justify-between gap-3 pt-3', 'border-t border-[hsl(var(--border))/0.8]')}>
          <div className="flex flex-wrap gap-2">
            {typeof finalScore === 'number' && (
              <span className="inline-flex items-center gap-1 rounded-full border border-[hsl(var(--primary))/0.18] bg-[hsl(var(--primary))/0.1] px-2.5 py-1 text-caption text-[hsl(var(--foreground))]">
                <CheckCircle2 className="h-3.5 w-3.5 text-[hsl(var(--primary))]" />
                Score {finalScore.toFixed(1)}
              </span>
            )}
            {trustReasons.slice(0, 1).map((reason) => (
              <span
                key={reason}
                className="inline-flex items-center gap-1 rounded-full border border-[hsl(var(--border))] bg-[hsl(var(--secondary))] px-2.5 py-1 text-caption text-[hsl(var(--foreground))]"
              >
                {reason}
              </span>
            ))}
          </div>

          <div className="flex items-center gap-2">
            {viewMode === 'feed' && (
              <button
                type="button"
                onClick={(event) => {
                  event.stopPropagation();
                  onToggleFavorite();
                }}
                className={cn(
                  'inline-flex items-center gap-1 rounded-full border border-[hsl(var(--border))] px-3 py-1.5 text-caption text-[hsl(var(--foreground))] transition-colors hover:bg-[hsl(var(--secondary))] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[hsl(var(--primary))/0.45] focus-visible:ring-offset-2 focus-visible:ring-offset-[hsl(var(--card))]',
                  isFavorite && 'border-[hsl(var(--primary))/0.3] bg-[hsl(var(--primary))/0.12]'
                )}
              >
                <Heart className={cn('h-3.5 w-3.5', isFavorite && 'fill-current text-[hsl(var(--primary))]')} />
                {isFavorite ? 'Saved' : 'Save'}
              </button>
            )}
            <span className="inline-flex items-center gap-1 rounded-full border border-[hsl(var(--border))] px-3 py-1.5 text-caption text-[hsl(var(--muted-foreground))]">
              <Eye className="h-3.5 w-3.5" />
              View
            </span>
          </div>
        </div>
        )}

        {viewMode === 'feed' && (
          <div className="space-y-2">
            <p className="text-caption font-semibold uppercase tracking-wide text-[hsl(var(--muted-foreground))]">
              Ranked high because
            </p>
            <div className="flex flex-wrap gap-1.5">
              {trustReasons.slice(0, 3).map((reason) => (
                <span
                  key={reason}
                  className="rounded-full border border-[hsl(var(--border))/0.9] bg-[hsl(var(--background))/0.66] px-2.5 py-1 text-caption text-[hsl(var(--muted-foreground))]"
                >
                  {reason}
                </span>
              ))}
            </div>
          </div>
        )}
        {business.is_active_today && (
          <p className="text-caption text-[hsl(var(--muted-foreground))]">
            Updated moments ago
          </p>
        )}
      </div>
    </article>
  );
}
