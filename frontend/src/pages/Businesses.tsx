import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { AlertCircle, ChevronDown, LayoutGrid, Loader2, MapPin, Navigation, Rows3, SlidersHorizontal, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { BusinessCard } from '@/components/business-card';
import { BusinessModal } from '@/components/BusinessModal';
import { CommunityActivityRail, type CommunityActivityItem } from '@/components/explore/CommunityActivityRail';
import { FilterBar } from '@/components/explore/FilterBar';
import { OwnerEventCard } from '@/components/explore/OwnerEventCard';
import { PulseRail } from '@/components/explore/PulseRail';
import { PreferenceOnboardingModal } from '@/components/preferences/PreferenceOnboardingModal';
import { useSavedBusinesses } from '@/hooks/useSavedBusinesses';
import type { ActivityPulseItem, Business, ExploreLane, ExploreSortMode, OwnerEvent, User } from '@/types';
import { api } from '@/api';
import { useAuth } from '@/contexts/AuthContext';

const CACHE_VERSION = 'v5';
const CACHE_TTL_MS = 30 * 60 * 1000;
const DEFAULT_LAT = 43.6532;
const DEFAULT_LNG = -79.3832;
const DEFAULT_RADIUS = 8;
const MIN_RADIUS = 1;
const MAX_RADIUS = 50;
const DISCOVERY_LIMIT = 300;
const LANE_PREVIEW_COUNT = 16;
const INITIAL_VISIBLE_COUNT = 36;
const LOAD_MORE_COUNT = 12;
const HERO_IMAGE = 'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=2000&q=80';
const SHOW_INTERNAL_DEMO_BADGE = import.meta.env.DEV && import.meta.env.VITE_DEMO_MODE === 'true';

interface CacheEntry {
  businesses: Business[];
  lanes: ExploreLane[];
  ts: number;
}

interface UserLocation {
  latitude: number;
  longitude: number;
}

function cacheKey(lat: number, lng: number, radius: number, sortMode: ExploreSortMode) {
  return `vantage:explore:${CACHE_VERSION}:${lat.toFixed(2)}:${lng.toFixed(2)}:${radius}:${sortMode}`;
}

function getCached(key: string): CacheEntry | null {
  try {
    const raw = sessionStorage.getItem(key);
    if (!raw) return null;
    const cached = JSON.parse(raw) as Partial<CacheEntry>;
    if (!Array.isArray(cached.businesses) || !Array.isArray(cached.lanes) || typeof cached.ts !== 'number') {
      sessionStorage.removeItem(key);
      return null;
    }
    if (Date.now() - cached.ts > CACHE_TTL_MS) {
      sessionStorage.removeItem(key);
      return null;
    }
    return cached as CacheEntry;
  } catch {
    return null;
  }
}

function setCache(key: string, businesses: Business[], lanes: ExploreLane[]) {
  try {
    sessionStorage.setItem(key, JSON.stringify({ businesses, lanes, ts: Date.now() }));
  } catch {
    // ignore storage issues
  }
}

function getBusinessId(business: Business) {
  return business.id || business._id || business.name;
}

function isIndependent(business: Business) {
  return (business.business_type || '').toLowerCase() === 'independent' || (business.local_confidence ?? 0) >= 0.75;
}

function hasVerifiedSignal(business: Business) {
  return (business.checkins_today ?? 0) > 0 || !!business.last_verified_at || !!business.is_active_today;
}

function isActiveToday(business: Business) {
  return !!business.is_active_today || (business.checkins_today ?? 0) > 0;
}

function formatRelativeTimestamp(timestamp?: string) {
  if (!timestamp) return 'Updated today';
  const time = new Date(timestamp).getTime();
  if (!time) return 'Updated today';
  const diffMin = Math.max(1, Math.floor((Date.now() - time) / 60000));
  if (diffMin < 60) return `${diffMin} min ago`;
  const diffHours = Math.floor(diffMin / 60);
  if (diffHours < 24) return `${diffHours} h ago`;
  const diffDays = Math.floor(diffHours / 24);
  return diffDays === 1 ? 'Yesterday' : `${diffDays} days ago`;
}

function canonicalScore(business: Business) {
  return business.ranking_components?.final_score ?? business.canonical_rank_score ?? business.live_visibility_score ?? 0;
}

function reasonChipLabel(reasonCode: string): string | null {
  switch (reasonCode) {
    case 'VERIFIED_TODAY': return 'Verified today';
    case 'HIGH_TRUST': return 'High trust';
    case 'RECENT_MOMENTUM': return 'Recent momentum';
    case 'HIGH_ENGAGEMENT': return 'High engagement';
    case 'CLAIMED': return 'Claimed';
    case 'INDEPENDENT': return 'Independent';
    case 'HIDDEN_GEM': return 'Hidden gem';
    case 'MATCHED_CATEGORIES': return 'Matched categories';
    case 'MATCHED_VIBES': return 'Matched vibes';
    case 'INDEPENDENT_MATCH': return 'Independent match';
    case 'PRICE_MATCH': return 'Price match';
    default: return null;
  }
}

function trustReasons(business: Business): string[] {
  const trustPriority = ['VERIFIED_TODAY', 'HIGH_TRUST', 'RECENT_MOMENTUM', 'HIGH_ENGAGEMENT', 'CLAIMED', 'INDEPENDENT', 'HIDDEN_GEM', 'MATCHED_CATEGORIES', 'MATCHED_VIBES', 'INDEPENDENT_MATCH', 'PRICE_MATCH'];
  const available = new Set(business.reason_codes ?? []);
  const mapped = trustPriority
    .filter((reasonCode) => available.has(reasonCode))
    .map((reasonCode) => reasonChipLabel(reasonCode))
    .filter((reason): reason is string => !!reason);
  return mapped.slice(0, 3);
}

function matchSummary(business: Business): string | null {
  const matches = [
    ...(business.preference_match?.matched_categories ?? []),
    ...(business.preference_match?.matched_vibes ?? []),
  ].filter(Boolean);
  if (matches.length === 0) {
    return null;
  }
  return matches.slice(0, 2).join(', ');
}

function laneExplainerCodes(lane: ExploreLane): string[] {
  const lanePriority = ['VERIFIED_TODAY', 'HIGH_TRUST', 'RECENT_MOMENTUM', 'HIGH_ENGAGEMENT', 'CLAIMED', 'INDEPENDENT', 'HIDDEN_GEM', 'MATCHED_CATEGORIES', 'MATCHED_VIBES', 'INDEPENDENT_MATCH', 'PRICE_MATCH'];
  const present = new Set<string>();
  lane.items.forEach((business) => {
    (business.reason_codes ?? []).forEach((reasonCode) => present.add(reasonCode));
  });
  const prioritized = lanePriority
    .filter((reasonCode) => present.has(reasonCode))
    .slice(0, 5);
  return prioritized;
}

function flattenBusinessesFromLanes(lanes: ExploreLane[]) {
  const seen = new Set<string>();
  const flattened: Business[] = [];
  lanes.forEach((lane) => lane.items.forEach((business) => {
    const id = getBusinessId(business);
    if (seen.has(id)) return;
    seen.add(id);
    flattened.push(business);
  }));
  return flattened;
}

function laneTitleForSort(sortMode: ExploreSortMode) {
  switch (sortMode) {
    case 'distance': return { title: 'Nearby Now', subtitle: 'Sorted by distance' };
    case 'newest': return { title: 'Fresh Additions', subtitle: 'Newest listings first' };
    case 'most_reviewed': return { title: 'Most Reviewed', subtitle: 'Sorted by review volume' };
    default: return { title: 'Explore', subtitle: 'Trust-ranked for your area' };
  }
}

function buildBrowseLane(items: Business[]): ExploreLane {
  return {
    id: 'all',
    title: 'Browse All',
    subtitle: 'Canonical trust-ranked nearby',
    items,
  };
}

const CATEGORY_TAG_HINTS: Record<string, string[]> = {
  'Restaurants': ['Dining', 'Local Favorite', 'Date Night'],
  'Cafes & Coffee': ['Coffee', 'Brunch', 'Study Spot'],
  'Bars & Nightlife': ['Cocktails', 'Late Night', 'Social'],
  'Shopping': ['Boutique', 'Giftable', 'Trending'],
  'Fitness & Wellness': ['Wellness', 'Workout', 'Recovery'],
  'Beauty & Spas': ['Self Care', 'Beauty', 'Relaxing'],
  'Health & Medical': ['Trusted Care', 'Appointments', 'Local Essential'],
  'Financial Services': ['Professional', 'Advisory', 'Appointments'],
  'Automotive': ['Repair', 'Service', 'Reliable'],
  'Entertainment': ['Fun', 'Group Spot', 'Experience'],
  'Hotels & Travel': ['Stay', 'Travel', 'Convenient'],
  'Professional Services': ['Professional', 'Appointments', 'Trusted'],
  'Home Services': ['Home Care', 'Reliable', 'Trusted Service'],
  'Pets': ['Pet Friendly', 'Care', 'Local Favorite'],
  'Education': ['Learning', 'Family', 'Trusted'],
  'Grocery': ['Essentials', 'Fresh', 'Convenient'],
  'Local Services': ['Community', 'Reliable', 'Everyday'],
  'Active Life': ['Outdoor', 'Active', 'Weekend'],
  'food': ['Dining', 'Local Favorite', 'Quick Bite'],
  'retail': ['Shopping', 'Giftable', 'Trending'],
  'services': ['Professional', 'Reliable', 'Local Essential'],
  'entertainment': ['Fun', 'Experience', 'Social'],
  'health': ['Wellness', 'Care', 'Trusted'],
};

function normalizeTagLabel(value: string) {
  return value
    .replace(/[_-]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .split(' ')
    .filter(Boolean)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

function deriveBusinessTags(business: Business) {
  const tags = new Set<string>();
  (business.known_for ?? []).forEach((tag) => {
    const normalized = normalizeTagLabel(tag);
    if (normalized) tags.add(normalized);
  });
  const category = business.category || 'Other';
  const normalizedCategory = normalizeTagLabel(category);
  if (normalizedCategory && normalizedCategory !== 'Other') {
    tags.add(normalizedCategory);
  }
  (CATEGORY_TAG_HINTS[category] ?? []).forEach((tag) => tags.add(tag));
  if (isIndependent(business)) tags.add('Independent');
  if (business.is_claimed) tags.add('Claimed');
  if (hasVerifiedSignal(business)) tags.add('Verified');
  if (isActiveToday(business)) tags.add('Live Now');
  if (business.has_deals) tags.add('Deals');
  return Array.from(tags).slice(0, 8);
}

function matchesFilters(
  business: Business,
  searchQuery: string,
  selectedCategory: string,
  independentOnly: boolean,
  verifiedOnly: boolean,
  claimedOnly: boolean,
  activeTodayOnly: boolean,
  selectedTagFilters: string[],
  businessTags: string[]
) {
  if (selectedCategory !== 'All Categories' && business.category !== selectedCategory) return false;
  if (independentOnly && !isIndependent(business)) return false;
  if (verifiedOnly && !hasVerifiedSignal(business)) return false;
  if (claimedOnly && !business.is_claimed) return false;
  if (activeTodayOnly && !isActiveToday(business)) return false;
  if (selectedTagFilters.length > 0 && !selectedTagFilters.some((tag) => businessTags.includes(tag))) return false;
  const query = searchQuery.trim().toLowerCase();
  if (!query) return true;
  const haystack = [
    business.name,
    business.category,
    business.address,
    business.short_description || business.description,
    businessTags.join(' '),
  ].join(' ').toLowerCase();
  return haystack.includes(query);
}

function updateBusinessInLanes(currentLanes: ExploreLane[], updatedBusiness: Business) {
  const updatedId = getBusinessId(updatedBusiness);
  return currentLanes.map((lane) => ({
    ...lane,
    items: lane.items.map((business) => (getBusinessId(business) === updatedId ? updatedBusiness : business)),
  }));
}

export default function Businesses() {
  const { user, setUser } = useAuth();
  const { savedIds, toggleSaved } = useSavedBusinesses();
  const [viewMode, setViewMode] = useState<'grid' | 'feed'>('grid');
  const [location, setLocation] = useState<UserLocation | null>(null);
  const [radius, setRadius] = useState(DEFAULT_RADIUS);
  const [businesses, setBusinesses] = useState<Business[]>([]);
  const [lanes, setLanes] = useState<ExploreLane[]>([]);
  const [ownerEvents, setOwnerEvents] = useState<OwnerEvent[]>([]);
  const [pulseItems, setPulseItems] = useState<ActivityPulseItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [locationLoading, setLocationLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedBusiness, setSelectedBusiness] = useState<Business | null>(null);
  const [selectedLaneId, setSelectedLaneId] = useState<string | null>(null);
  const [showPreferenceOnboarding, setShowPreferenceOnboarding] = useState(false);
  const [showExplainer, setShowExplainer] = useState(true);
  const [activeExplainerLaneId, setActiveExplainerLaneId] = useState<string | null>(null);
  const [searchInput, setSearchInput] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [sortMode] = useState<ExploreSortMode>('canonical');
  const [selectedCategory, setSelectedCategory] = useState('All Categories');
  const [independentOnly, setIndependentOnly] = useState(false);
  const [verifiedOnly, setVerifiedOnly] = useState(false);
  const [claimedOnly, setClaimedOnly] = useState(false);
  const [activeTodayOnly, setActiveTodayOnly] = useState(false);
  const [showTagSidebar, setShowTagSidebar] = useState(false);
  const [selectedTagFilters, setSelectedTagFilters] = useState<string[]>([]);
  const [visibleCount, setVisibleCount] = useState(INITIAL_VISIBLE_COUNT);
  const filtersRef = useRef<HTMLElement | null>(null);
  const radiusDebounceRef = useRef<number | null>(null);
  const businessModalScrollRef = useRef(0);
  const laneOverlayScrollRef = useRef(0);
  const didAutoLocateRef = useRef(false);

  useEffect(() => {
    setShowPreferenceOnboarding(!!user && !user.preferences_completed);
  }, [user]);

  useEffect(() => {
    const debounceHandle = window.setTimeout(() => {
      setSearchQuery(searchInput);
    }, 220);

    return () => window.clearTimeout(debounceHandle);
  }, [searchInput]);

  const fetchPulse = useCallback(async (lat: number, lng: number, radiusValue: number) => {
    try {
      const nextPulse = await api.getActivityPulse(lat, lng, radiusValue, 10);
      setPulseItems(nextPulse);
    } catch {
      setPulseItems([]);
    }
  }, []);

  const fetchOwnerEvents = useCallback(async (lat: number, lng: number, radiusValue: number) => {
    try {
      const events = await api.getOwnerEvents({ lat, lng, radius: radiusValue, limit: 12 });
      setOwnerEvents(events);
    } catch {
      setOwnerEvents([]);
    }
  }, []);

  const fetchExploreData = useCallback(async (lat: number, lng: number, radiusValue: number, forceRefresh = false, requestedSortMode: ExploreSortMode = 'canonical') => {
    const key = cacheKey(lat, lng, radiusValue, requestedSortMode);
    if (forceRefresh) sessionStorage.removeItem(key);
    void fetchPulse(lat, lng, radiusValue);
    void fetchOwnerEvents(lat, lng, radiusValue);
    const cached = getCached(key);
    if (!forceRefresh && cached && (cached.businesses.length > 0 || cached.lanes.length > 0)) {
      setBusinesses(cached.businesses);
      setLanes(cached.lanes);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    const sortLane = laneTitleForSort(requestedSortMode);
    try {
      let nextBusinesses: Business[] = [];
      let nextLanes: ExploreLane[] = [];
      if (requestedSortMode === 'canonical') {
        nextBusinesses = await api.discoverBusinesses(lat, lng, radiusValue, undefined, DISCOVERY_LIMIT, forceRefresh, 'canonical');
        const canonicalLane = buildBrowseLane(nextBusinesses);
        nextLanes = [canonicalLane];

        try {
          const laneResponse = await api.getExploreLanes(lat, lng, radiusValue, DISCOVERY_LIMIT);
          const personalizedLanes = (laneResponse.lanes ?? []).filter((lane) => lane.items.length > 0);
          nextLanes = [canonicalLane, ...personalizedLanes];
        } catch {
          // Keep the canonical browse lane even if personalization fails.
        }
      } else {
        nextBusinesses = await api.discoverBusinesses(lat, lng, radiusValue, undefined, DISCOVERY_LIMIT, forceRefresh, requestedSortMode);
        nextLanes = [{ id: requestedSortMode, title: sortLane.title, subtitle: sortLane.subtitle, items: nextBusinesses }];
      }
      setBusinesses(nextBusinesses);
      setLanes(nextLanes);
      setCache(key, nextBusinesses, nextLanes);
    } catch {
      try {
        const fallback = await api.getNearbyBusinesses(lat, lng, radiusValue);
        const fallbackLanes = requestedSortMode === 'canonical'
          ? [buildBrowseLane(fallback)]
          : [{ id: requestedSortMode, title: sortLane.title, subtitle: sortLane.subtitle, items: fallback }];
        setBusinesses(fallback);
        setLanes(fallbackLanes);
        setCache(key, fallback, fallbackLanes);
      } catch (fetchError) {
        setError(fetchError instanceof Error ? fetchError.message : 'Failed to load nearby businesses');
        setBusinesses([]);
        setLanes([]);
      }
    } finally {
      setLoading(false);
    }
  }, [fetchOwnerEvents, fetchPulse]);

  useEffect(() => {
    fetchExploreData(DEFAULT_LAT, DEFAULT_LNG, DEFAULT_RADIUS, false, 'canonical');
  }, [fetchExploreData]);

  useEffect(() => {
    if (didAutoLocateRef.current || typeof window === 'undefined') {
      return;
    }
    if (!navigator.geolocation) {
      didAutoLocateRef.current = true;
      return;
    }
    didAutoLocateRef.current = true;
    setLocationLoading(true);
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const nextLocation = { latitude: position.coords.latitude, longitude: position.coords.longitude };
        setLocation(nextLocation);
        fetchExploreData(nextLocation.latitude, nextLocation.longitude, radius, true, 'canonical');
        setLocationLoading(false);
      },
      () => {
        setLocationLoading(false);
      }
    );
  }, [fetchExploreData, radius]);

  const requestLocation = () => {
    setError(null);
    if (!navigator.geolocation) {
      setError('Geolocation is not supported by this browser.');
      return;
    }
    setLocationLoading(true);
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const nextLocation = { latitude: position.coords.latitude, longitude: position.coords.longitude };
        setLocation(nextLocation);
        fetchExploreData(nextLocation.latitude, nextLocation.longitude, radius, true, sortMode);
        setLocationLoading(false);
      },
      () => {
        setLocationLoading(false);
        setError('We could not access your location. Showing businesses from the default area.');
      }
    );
  };

  const handleRadiusChange = (nextRadius: number) => {
    setRadius(nextRadius);
    if (radiusDebounceRef.current) window.clearTimeout(radiusDebounceRef.current);
    radiusDebounceRef.current = window.setTimeout(() => {
      fetchExploreData(location?.latitude ?? DEFAULT_LAT, location?.longitude ?? DEFAULT_LNG, nextRadius, true, sortMode);
    }, 220);
  };

  useEffect(() => () => {
    if (radiusDebounceRef.current) window.clearTimeout(radiusDebounceRef.current);
  }, []);

  const categoryCounts = useMemo(() => {
    const counts: Record<string, number> = { 'All Categories': businesses.length };
    businesses.forEach((business) => {
      const category = business.category || 'Other';
      counts[category] = (counts[category] || 0) + 1;
    });
    return counts;
  }, [businesses]);

  const categories = useMemo(() => Object.entries(categoryCounts)
    .map(([label, count]) => ({ label, count }))
    .sort((a, b) => {
      if (a.label === 'All Categories') return -1;
      if (b.label === 'All Categories') return 1;
      return b.count - a.count;
    })
    .slice(0, 10), [categoryCounts]);

  const businessTagMap = useMemo(() => {
    const next: Record<string, string[]> = {};
    businesses.forEach((business) => {
      next[getBusinessId(business)] = deriveBusinessTags(business);
    });
    return next;
  }, [businesses]);

  const tagFacets = useMemo(() => {
    const counts: Record<string, number> = {};
    businesses.forEach((business) => {
      const uniqueTags = new Set(businessTagMap[getBusinessId(business)] ?? []);
      uniqueTags.forEach((tag) => {
        counts[tag] = (counts[tag] || 0) + 1;
      });
    });
    return Object.entries(counts)
      .map(([label, count]) => ({ label, count }))
      .sort((a, b) => {
        if (b.count !== a.count) return b.count - a.count;
        return a.label.localeCompare(b.label);
      })
      .slice(0, 24);
  }, [businessTagMap, businesses]);

  useEffect(() => {
    setSelectedTagFilters((current) => current.filter((tag) => tagFacets.some((facet) => facet.label === tag)));
  }, [tagFacets]);

  const filteredLanes = useMemo(() => lanes
    .map((lane) => ({
      ...lane,
      items: lane.items.filter((business) => matchesFilters(
        business,
        searchQuery,
        selectedCategory,
        independentOnly,
        verifiedOnly,
        claimedOnly,
        activeTodayOnly,
        selectedTagFilters,
        businessTagMap[getBusinessId(business)] ?? []
      )),
    }))
    .filter((lane) => lane.items.length > 0), [lanes, searchQuery, selectedCategory, independentOnly, verifiedOnly, claimedOnly, activeTodayOnly, selectedTagFilters, businessTagMap]);

  const filteredBusinesses = useMemo(() => flattenBusinessesFromLanes(filteredLanes), [filteredLanes]);
  const selectedLane = useMemo(() => filteredLanes.find((lane) => lane.id === selectedLaneId) ?? null, [filteredLanes, selectedLaneId]);
  const activeExplainerLane = useMemo(
    () => filteredLanes.find((lane) => lane.id === activeExplainerLaneId) ?? filteredLanes[0] ?? null,
    [filteredLanes, activeExplainerLaneId]
  );
  const explainerCodes = useMemo(
    () => (activeExplainerLane ? laneExplainerCodes(activeExplainerLane) : []),
    [activeExplainerLane]
  );

  useEffect(() => {
    if (selectedLaneId && !selectedLane) setSelectedLaneId(null);
  }, [selectedLane, selectedLaneId]);

  useEffect(() => {
    if (!filteredLanes.length) {
      setActiveExplainerLaneId(null);
      return;
    }
    if (!activeExplainerLaneId || !filteredLanes.some((lane) => lane.id === activeExplainerLaneId)) {
      setActiveExplainerLaneId(filteredLanes[0].id);
    }
  }, [filteredLanes, activeExplainerLaneId]);

  useEffect(() => {
    setVisibleCount(INITIAL_VISIBLE_COUNT);
  }, [lanes, searchQuery, selectedCategory, independentOnly, verifiedOnly, claimedOnly, activeTodayOnly, selectedTagFilters, viewMode, sortMode, selectedLaneId]);

  const activityItems = useMemo<CommunityActivityItem[]>(() => businesses
    .filter((business) => hasVerifiedSignal(business) || isActiveToday(business))
    .sort((a, b) => {
      const aDate = a.last_activity_at ? new Date(a.last_activity_at).getTime() : 0;
      const bDate = b.last_activity_at ? new Date(b.last_activity_at).getTime() : 0;
      if (bDate !== aDate) return bDate - aDate;
      return canonicalScore(b) - canonicalScore(a);
    })
    .slice(0, 12)
    .map((business) => ({
      id: getBusinessId(business),
      name: business.name,
      category: business.category,
      timestamp: formatRelativeTimestamp(business.last_activity_at),
      summary: trustReasons(business)[0] || 'Community activity detected',
      imageUrl: business.image_url || business.image,
      secondary: `${Math.max(1, business.checkins_today ?? 0)} people verified`,
    })), [businesses]);

  const openLane = (laneId: string) => {
    laneOverlayScrollRef.current = window.scrollY;
    setSelectedLaneId(laneId);
  };

  const closeLane = () => {
    setSelectedLaneId(null);
    window.requestAnimationFrame(() => window.scrollTo({ top: laneOverlayScrollRef.current, behavior: 'auto' }));
  };

  const openBusiness = (business: Business) => {
    businessModalScrollRef.current = window.scrollY;
    setSelectedBusiness(business);
  };

  const closeBusiness = () => {
    setSelectedBusiness(null);
    window.requestAnimationFrame(() => window.scrollTo({ top: businessModalScrollRef.current, behavior: 'auto' }));
  };

  const handleBusinessUpdated = (updatedBusiness: Business) => {
    const updatedId = getBusinessId(updatedBusiness);
    setBusinesses((current) => current.map((business) => (getBusinessId(business) === updatedId ? updatedBusiness : business)));
    setLanes((current) => updateBusinessInLanes(current, updatedBusiness));
    setSelectedBusiness(updatedBusiness);
  };

  const handlePulseView = async (item: ActivityPulseItem) => {
    const existing = businesses.find((business) => getBusinessId(business) === item.business.business_id);
    if (existing) {
      openBusiness(existing);
      return;
    }
    try {
      const fetched = await api.getBusiness(item.business.business_id);
      openBusiness(fetched);
    } catch {
      // leave pulse item inert when the business can't be fetched
    }
  };

  const handleEventView = async (event: OwnerEvent) => {
    const existing = businesses.find((business) => getBusinessId(business) === event.business_id);
    if (existing) {
      openBusiness(existing);
      return;
    }
    try {
      const fetched = await api.getBusiness(event.business_id);
      openBusiness(fetched);
    } catch {
      // leave inert if fetch fails
    }
  };

  const handlePreferencesSaved = (updatedUser: User) => {
    setUser(updatedUser);
    setShowPreferenceOnboarding(false);
    fetchExploreData(location?.latitude ?? DEFAULT_LAT, location?.longitude ?? DEFAULT_LNG, radius, true, sortMode);
  };

  const renderBusinessList = (items: Business[], mode: 'grid' | 'feed', laneId?: string) => {
    const laneBusinessIds = new Set(items.map((business) => getBusinessId(business)));
    const laneEvents = ownerEvents
      .filter((event) => laneBusinessIds.has(event.business_id))
      .slice(0, mode === 'grid' ? 2 : 1);

    const content: Array<{ type: 'business'; business: Business } | { type: 'event'; event: OwnerEvent }> = [];
    items.forEach((business, index) => {
      content.push({ type: 'business', business });
      const eventIndex = Math.floor(index / 4);
      if ((index + 1) % 4 === 0 && laneEvents[eventIndex]) {
        content.push({ type: 'event', event: laneEvents[eventIndex] });
      }
    });

    if (laneEvents.length > 0 && !content.some((entry) => entry.type === 'event')) {
      content.splice(Math.min(2, content.length), 0, { type: 'event', event: laneEvents[0] });
    }

    if (mode === 'grid') {
      return (
        <div className="columns-1 gap-6 sm:columns-2 xl:columns-3 2xl:columns-4">
          {content.map((entry) => {
            if (entry.type === 'event') {
              return (
                <div key={`event-${entry.event.id}`} className="mb-4 break-inside-avoid">
                  <OwnerEventCard event={entry.event} viewMode="grid" onViewBusiness={() => handleEventView(entry.event)} />
                </div>
              );
            }

            const businessId = getBusinessId(entry.business);
            return (
              <div key={businessId} className="mb-4 break-inside-avoid">
                <BusinessCard business={entry.business} trustReasons={trustReasons(entry.business)} isFavorite={savedIds.includes(businessId)} onToggleFavorite={() => void toggleSaved(entry.business)} onViewDetails={() => openBusiness(entry.business)} viewMode="grid" matchSummary={laneId === 'for_you' ? matchSummary(entry.business) : null} />
              </div>
            );
          })}
        </div>
      );
    }

    return (
      <div className="space-y-5">
        {content.map((entry) => {
          if (entry.type === 'event') {
            return <OwnerEventCard key={`event-${entry.event.id}`} event={entry.event} viewMode="feed" onViewBusiness={() => handleEventView(entry.event)} />;
          }

          const businessId = getBusinessId(entry.business);
          return (
            <BusinessCard key={businessId} business={entry.business} trustReasons={trustReasons(entry.business)} isFavorite={savedIds.includes(businessId)} onToggleFavorite={() => void toggleSaved(entry.business)} onViewDetails={() => openBusiness(entry.business)} viewMode="feed" matchSummary={laneId === 'for_you' ? matchSummary(entry.business) : null} />
          );
        })}
      </div>
    );
  };

  const renderLoadingState = () => {
    if (sortMode === 'canonical') {
      return (
        <div className="space-y-8" aria-hidden="true">
          {Array.from({ length: 3 }).map((_, laneIndex) => (
            <section key={laneIndex} className="space-y-4">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
                <div className="space-y-2">
                  <div className="skeleton h-3 w-20 rounded-full" />
                  <div className="skeleton h-7 w-48 rounded-full" />
                  <div className="skeleton h-4 w-64 rounded-full" />
                </div>
                <div className="skeleton h-11 w-24 rounded-full" />
              </div>

              {viewMode === 'grid' ? (
                <div className="columns-1 gap-6 sm:columns-2 xl:columns-3 2xl:columns-4">
                  {Array.from({ length: 6 }).map((_, index) => (
                    <div key={`${laneIndex}-${index}`} className="mb-4 break-inside-avoid rounded-[24px] border border-[hsl(var(--border))] bg-[hsl(var(--card))] p-3">
                      <div className={`skeleton ${index % 3 === 0 ? 'aspect-[4/5]' : index % 3 === 1 ? 'aspect-[1/1]' : 'aspect-[3/4]'} rounded-[20px]`} />
                      <div className="mt-3 space-y-2">
                        <div className="skeleton h-4 w-3/4 rounded-full" />
                        <div className="skeleton h-3 w-full rounded-full" />
                        <div className="skeleton h-3 w-5/6 rounded-full" />
                        <div className="flex gap-2 pt-1">
                          <div className="skeleton h-6 w-20 rounded-full" />
                          <div className="skeleton h-6 w-16 rounded-full" />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="space-y-4">
                  {Array.from({ length: 3 }).map((_, index) => (
                    <div key={`${laneIndex}-${index}`} className="overflow-hidden rounded-[24px] border border-[hsl(var(--border))] bg-[hsl(var(--card))] p-3 sm:flex sm:gap-4">
                      <div className="skeleton aspect-[16/9] rounded-[20px] sm:w-[320px] sm:flex-shrink-0" />
                      <div className="mt-3 flex-1 space-y-2 sm:mt-0 sm:py-2">
                        <div className="skeleton h-4 w-2/3 rounded-full" />
                        <div className="skeleton h-3 w-full rounded-full" />
                        <div className="skeleton h-3 w-5/6 rounded-full" />
                        <div className="flex gap-2 pt-1">
                          <div className="skeleton h-6 w-24 rounded-full" />
                          <div className="skeleton h-6 w-20 rounded-full" />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>
          ))}
        </div>
      );
    }

    return viewMode === 'grid' ? (
      <div className="columns-1 gap-6 sm:columns-2 xl:columns-3 2xl:columns-4" aria-hidden="true">
        {Array.from({ length: 8 }).map((_, index) => (
          <div key={index} className="mb-4 break-inside-avoid rounded-[24px] border border-[hsl(var(--border))] bg-[hsl(var(--card))] p-3">
            <div className={`skeleton ${index % 3 === 0 ? 'aspect-[4/5]' : index % 3 === 1 ? 'aspect-[1/1]' : 'aspect-[3/4]'} rounded-[20px]`} />
            <div className="mt-3 space-y-2">
              <div className="skeleton h-4 w-3/4 rounded-full" />
              <div className="skeleton h-3 w-full rounded-full" />
              <div className="skeleton h-3 w-5/6 rounded-full" />
            </div>
          </div>
        ))}
      </div>
    ) : (
      <div className="space-y-4" aria-hidden="true">
        {Array.from({ length: 5 }).map((_, index) => (
          <div key={index} className="overflow-hidden rounded-[24px] border border-[hsl(var(--border))] bg-[hsl(var(--card))] p-3 sm:flex sm:gap-4">
            <div className="skeleton aspect-[16/9] rounded-[20px] sm:w-[320px] sm:flex-shrink-0" />
            <div className="mt-3 flex-1 space-y-2 sm:mt-0 sm:py-2">
              <div className="skeleton h-4 w-2/3 rounded-full" />
              <div className="skeleton h-3 w-full rounded-full" />
              <div className="skeleton h-3 w-5/6 rounded-full" />
            </div>
          </div>
        ))}
      </div>
    );
  };

  const pageSubtitle = sortMode === 'canonical'
    ? 'Browse normally first, with curated lanes layered in.'
    : `${laneTitleForSort(sortMode).title} preserves the backend order exactly.`;
  const browseAllLane = filteredLanes.find((lane) => lane.id === 'all') ?? null;
  const canonicalBrowseHasMore = sortMode === 'canonical' && !!browseAllLane && visibleCount < browseAllLane.items.length;
  const singleLaneHasMore = sortMode !== 'canonical' && filteredLanes.length > 0 && visibleCount < filteredLanes[0].items.length;
  const hasMoreInSelectedLane = !!selectedLane && visibleCount < selectedLane.items.length;
  const toggleTagFilter = (tag: string) => {
    setSelectedTagFilters((current) => (
      current.includes(tag)
        ? current.filter((value) => value !== tag)
        : [...current, tag]
    ));
  };

  return (
    <div className="explore-page min-h-screen bg-[hsl(var(--background))] px-2 py-4 sm:px-5 sm:py-6">
      <div className="mx-auto max-w-[1560px] overflow-hidden rounded-[34px] bg-[hsl(var(--background))]">
        <section className="border-b border-[hsl(var(--border))/0.7] px-6 py-8 sm:px-10 sm:py-10">
          <div className="flex flex-wrap items-center gap-2">
            <p className="text-caption font-semibold uppercase tracking-[0.14em] text-[hsl(var(--muted-foreground))]">Trust first local discovery</p>
            {SHOW_INTERNAL_DEMO_BADGE && (
              <span className="rounded-full border border-[hsl(var(--primary))/0.28] bg-[hsl(var(--primary))/0.12] px-2.5 py-1 text-caption font-semibold uppercase tracking-[0.12em] text-[hsl(var(--foreground))]">
                Demo Mode
              </span>
            )}
          </div>
          <h1 className="mt-2 font-heading text-[42px] font-bold leading-tight text-[hsl(var(--foreground))] sm:text-[52px]">Explore trusted businesses near you</h1>
          <p className="mt-2 text-body text-[hsl(var(--muted-foreground))]">Personalization shapes the lanes. Live Visibility still ranks every card inside them.</p>
          <div className="mt-5 flex flex-wrap gap-3">
            <Button onClick={requestLocation} disabled={locationLoading} className="rounded-full px-5">
              <Navigation className="h-4 w-4" />
              {locationLoading ? 'Locating...' : 'Use location'}
            </Button>
            <Button variant="outline" onClick={() => filtersRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })} className="rounded-full px-5">Browse categories</Button>
          </div>
          <p className="mt-4 text-ui text-[hsl(var(--muted-foreground))]">
            {loading ? 'Loading businesses...' : sortMode === 'canonical' ? `${filteredBusinesses.length} businesses across ${filteredLanes.length} curated lanes` : `${filteredBusinesses.length} businesses in this view`}
          </p>
          <div className="relative mt-5 h-32 overflow-hidden rounded-[26px] border border-[hsl(var(--border))/0.7] sm:h-44">
            <img src={HERO_IMAGE} alt="Explore hero" className="h-full w-full object-cover" loading="lazy" />
            <div className="absolute inset-0 bg-gradient-to-t from-[hsl(var(--card))/0.9] to-transparent dark:from-[hsl(var(--card))/0.8]" />
            <div className="absolute inset-0 bg-[hsl(var(--background))/0.18] dark:bg-[hsl(var(--background))/0.36]" />
          </div>
        </section>

        <section className="border-b border-[hsl(var(--border))/0.7] bg-[hsl(var(--card))] px-6 py-6 sm:px-10">
          <CommunityActivityRail items={activityItems} />
        </section>

        {pulseItems.length > 0 && (
          <section className="border-b border-[hsl(var(--border))/0.7] bg-[hsl(var(--card))] px-6 py-6 sm:px-10">
            <PulseRail items={pulseItems} onView={handlePulseView} />
          </section>
        )}

        <section ref={filtersRef} className="border-b border-[hsl(var(--border))/0.7] px-6 py-5 sm:px-10">
          <FilterBar
            searchQuery={searchInput}
            onSearchQueryChange={setSearchInput}
            radius={radius}
            onRadiusChange={handleRadiusChange}
            minRadius={MIN_RADIUS}
            maxRadius={MAX_RADIUS}
            locationActive={!!location}
            loadingLocation={locationLoading}
            onUseLocation={requestLocation}
            categories={categories}
            selectedCategory={selectedCategory}
            onCategoryChange={setSelectedCategory}
            independentOnly={independentOnly}
            onToggleIndependent={() => setIndependentOnly((value) => !value)}
            verifiedOnly={verifiedOnly}
            onToggleVerified={() => setVerifiedOnly((value) => !value)}
            claimedOnly={claimedOnly}
            onToggleClaimed={() => setClaimedOnly((value) => !value)}
            activeTodayOnly={activeTodayOnly}
            onToggleActiveToday={() => setActiveTodayOnly((value) => !value)}
          />
        </section>

        <section className="px-6 py-6 sm:px-10">
          {error && (
            <div className="mb-4 flex items-start gap-3 rounded-xl border border-error bg-error p-4">
              <AlertCircle className="mt-0.5 h-5 w-5 flex-shrink-0 text-error" />
              <div>
                <p className="text-ui font-semibold text-[hsl(var(--foreground))]">Notice</p>
                <p className="text-ui text-[hsl(var(--muted-foreground))]">{error}</p>
              </div>
            </div>
          )}

          <div className="mb-6 flex flex-col gap-4 rounded-[28px] border border-[hsl(var(--border))/0.8] bg-[hsl(var(--card))]/0.9 p-4">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="text-caption font-semibold uppercase tracking-[0.16em] text-[hsl(var(--muted-foreground))]">Browse Mode</p>
                <p className="text-ui text-[hsl(var(--muted-foreground))]">{pageSubtitle}</p>
              </div>
              <div className="flex flex-wrap items-center gap-3">
                {tagFacets.length > 0 && (
                  <Button type="button" variant="outline" onClick={() => setShowTagSidebar((current) => !current)} className="rounded-full px-4">
                    <SlidersHorizontal className="h-4 w-4" />
                    {showTagSidebar ? 'Hide tag filters' : 'Filter by tags'}
                  </Button>
                )}
                <div className="inline-flex rounded-full border border-[hsl(var(--border))] bg-[hsl(var(--card))] p-1">
                  <button type="button" onClick={() => setViewMode('grid')} className={`inline-flex items-center gap-2 rounded-full px-4 py-2 text-ui transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[hsl(var(--primary))/0.45] focus-visible:ring-offset-2 focus-visible:ring-offset-[hsl(var(--card))] ${viewMode === 'grid' ? 'bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))]' : 'text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))]'}`}>
                    <LayoutGrid className="h-4 w-4" />
                    Grid
                  </button>
                  <button type="button" onClick={() => setViewMode('feed')} className={`inline-flex items-center gap-2 rounded-full px-4 py-2 text-ui transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[hsl(var(--primary))/0.45] focus-visible:ring-offset-2 focus-visible:ring-offset-[hsl(var(--card))] ${viewMode === 'feed' ? 'bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))]' : 'text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))]'}`}>
                    <Rows3 className="h-4 w-4" />
                    Feed
                  </button>
                </div>
              </div>
            </div>

            {selectedTagFilters.length > 0 && (
              <div className="flex flex-wrap items-center gap-2">
                {selectedTagFilters.map((tag) => (
                  <button
                    key={tag}
                    type="button"
                    onClick={() => toggleTagFilter(tag)}
                    className="inline-flex items-center gap-2 rounded-full border border-[hsl(var(--primary))/0.3] bg-[hsl(var(--primary))/0.08] px-3 py-1.5 text-caption text-[hsl(var(--foreground))] transition-colors hover:bg-[hsl(var(--primary))/0.14]"
                  >
                    {tag}
                    <X className="h-3.5 w-3.5" />
                  </button>
                ))}
                <button
                  type="button"
                  onClick={() => setSelectedTagFilters([])}
                  className="rounded-full px-2 py-1 text-caption text-[hsl(var(--muted-foreground))] transition-colors hover:text-[hsl(var(--foreground))]"
                >
                  Clear all
                </button>
              </div>
            )}
          </div>

          <div className={`grid gap-6 ${showTagSidebar && tagFacets.length > 0 ? 'xl:grid-cols-[280px_minmax(0,1fr)]' : ''}`}>
            {showTagSidebar && tagFacets.length > 0 && (
              <aside className="h-fit rounded-[26px] border border-[hsl(var(--border))/0.8] bg-[hsl(var(--card))]/0.88 p-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-caption font-semibold uppercase tracking-[0.14em] text-[hsl(var(--muted-foreground))]">Manual filters</p>
                    <h2 className="mt-1 text-subheading font-semibold text-[hsl(var(--foreground))]">Business tags</h2>
                    <p className="mt-1 text-ui text-[hsl(var(--muted-foreground))]">Tags come from known-for labels plus business type and category.</p>
                  </div>
                  <button
                    type="button"
                    onClick={() => setShowTagSidebar(false)}
                    className="rounded-full p-2 text-[hsl(var(--muted-foreground))] transition-colors hover:text-[hsl(var(--foreground))] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[hsl(var(--primary))/0.45]"
                    aria-label="Hide tag filters"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>

                <div className="mt-4 flex flex-wrap gap-2">
                  {tagFacets.map((tag) => {
                    const active = selectedTagFilters.includes(tag.label);
                    return (
                      <button
                        key={tag.label}
                        type="button"
                        onClick={() => toggleTagFilter(tag.label)}
                        className={`inline-flex items-center gap-2 rounded-full border px-3 py-2 text-caption transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[hsl(var(--primary))/0.45] ${
                          active
                            ? 'border-[hsl(var(--primary))/0.35] bg-[hsl(var(--primary))/0.1] text-[hsl(var(--foreground))]'
                            : 'border-[hsl(var(--border))] text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))]'
                        }`}
                      >
                        <span>{tag.label}</span>
                        <span className="rounded-full bg-[hsl(var(--background))/0.7] px-1.5 py-0.5 text-[10px] font-semibold text-[hsl(var(--muted-foreground))]">
                          {tag.count}
                        </span>
                      </button>
                    );
                  })}
                </div>
              </aside>
            )}

            <div className="min-w-0">
              {!loading && activeExplainerLane && (
                <div className="mb-5 rounded-3xl border border-[hsl(var(--border))/0.8] bg-[hsl(var(--background))/0.58] p-4 backdrop-blur-sm">
                  <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                    <div>
                      <p className="text-caption font-semibold uppercase tracking-[0.16em] text-[hsl(var(--muted-foreground))]">
                        Why these businesses are surfacing
                      </p>
                      <p className="text-ui text-[hsl(var(--muted-foreground))]">
                        Explanations come directly from backend reason codes for {activeExplainerLane.title}.
                      </p>
                    </div>
                    <Button type="button" variant="outline" onClick={() => setShowExplainer((current) => !current)} className="rounded-full px-4">
                      <ChevronDown className={`h-4 w-4 transition-transform ${showExplainer ? 'rotate-180' : ''}`} />
                      {showExplainer ? 'Hide' : 'Show'}
                    </Button>
                  </div>

                  {showExplainer && (
                    <div className="mt-4 space-y-4">
                      <div className="flex flex-wrap gap-2">
                        {filteredLanes.map((lane) => (
                          <button
                            key={lane.id}
                            type="button"
                            onClick={() => setActiveExplainerLaneId(lane.id)}
                            className={`rounded-full border px-3 py-1.5 text-caption transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[hsl(var(--primary))/0.4] focus-visible:ring-offset-2 focus-visible:ring-offset-[hsl(var(--background))] ${
                              activeExplainerLane.id === lane.id
                                ? 'border-[hsl(var(--primary))] bg-[hsl(var(--primary))]/10 text-[hsl(var(--foreground))]'
                                : 'border-[hsl(var(--border))] text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))]'
                            }`}
                          >
                            {lane.title}
                          </button>
                        ))}
                      </div>

                      <div className="flex flex-wrap gap-2">
                        {explainerCodes.map((reasonCode) => (
                          <span
                            key={reasonCode}
                            className="rounded-full border border-[hsl(var(--border))/0.9] bg-[hsl(var(--card))] px-3 py-1.5 text-caption text-[hsl(var(--foreground))]"
                          >
                            {reasonChipLabel(reasonCode)}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {loading && renderLoadingState()}

              {!loading && filteredLanes.length > 0 && (
                <div className="space-y-10">
                  {filteredLanes.map((lane) => {
                    const laneLimit = sortMode === 'canonical'
                      ? lane.id === 'all'
                        ? Math.min(visibleCount, lane.items.length)
                        : Math.min(LANE_PREVIEW_COUNT, lane.items.length)
                      : Math.min(visibleCount, lane.items.length);
                    const visibleItems = lane.items.slice(0, laneLimit);
                    const hasHiddenItems = lane.items.length > visibleItems.length;
                    return (
                      <section key={lane.id} className="space-y-5 animate-fade-in-up">
                        <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
                          <div>
                            <p className="text-caption font-semibold uppercase tracking-[0.14em] text-[hsl(var(--muted-foreground))]">{lane.id === 'all' ? 'browse' : lane.id.replace(/_/g, ' ')}</p>
                            <h2 className="text-heading font-semibold text-[hsl(var(--foreground))]">{lane.title}</h2>
                            <p className="text-ui text-[hsl(var(--muted-foreground))]">{lane.subtitle}</p>
                          </div>
                          {hasHiddenItems && (
                            <Button type="button" variant="outline" onClick={() => openLane(lane.id)} className="rounded-full px-5">See all</Button>
                          )}
                        </div>
                        {renderBusinessList(visibleItems, viewMode, lane.id)}
                      </section>
                    );
                  })}

                  {canonicalBrowseHasMore && (
                    <div className="flex justify-center">
                      <Button type="button" variant="outline" onClick={() => setVisibleCount((current) => current + LOAD_MORE_COUNT)} className="rounded-full px-5">
                        <ChevronDown className="h-4 w-4" />
                        Load more from Browse All
                      </Button>
                    </div>
                  )}

                  {singleLaneHasMore && (
                    <div className="flex justify-center">
                      <Button type="button" variant="outline" onClick={() => setVisibleCount((current) => current + LOAD_MORE_COUNT)} className="rounded-full px-5">
                        <ChevronDown className="h-4 w-4" />
                        Load more
                      </Button>
                    </div>
                  )}
                </div>
              )}

              {!loading && filteredLanes.length === 0 && (
                <section className="rounded-2xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] px-6 py-12 text-center">
                  <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-[hsl(var(--secondary))]">
                    <MapPin className="h-5 w-5 text-[hsl(var(--muted-foreground))]" />
                  </div>
                  <h2 className="mt-4 text-subheading font-semibold text-[hsl(var(--foreground))]">No businesses match these filters</h2>
                  <p className="mt-2 text-ui text-[hsl(var(--muted-foreground))]">Try a broader radius or clear some filters.</p>
                </section>
              )}
            </div>
          </div>
        </section>
      </div>

      {selectedLane && (
        <div className="fixed inset-0 z-40 bg-[hsl(var(--background))/0.72] backdrop-blur-md">
          <div className="absolute inset-0" onClick={closeLane} />
          <div className="relative h-full w-full overflow-hidden bg-[hsl(var(--background))] sm:m-4 sm:h-[calc(100%-2rem)] sm:w-auto sm:rounded-[32px] sm:border sm:border-[hsl(var(--border))/0.8] sm:bg-[hsl(var(--card))]">
            <div className="flex h-full flex-col">
              <div className="flex items-start justify-between gap-4 border-b border-[hsl(var(--border))/0.8] px-5 py-5 sm:px-8">
                <div>
                  <p className="text-caption font-semibold uppercase tracking-[0.14em] text-[hsl(var(--muted-foreground))]">Lane detail</p>
                  <h2 className="text-heading font-semibold text-[hsl(var(--foreground))]">{selectedLane.title}</h2>
                  <p className="text-ui text-[hsl(var(--muted-foreground))]">{selectedLane.subtitle} • {selectedLane.items.length} businesses</p>
                </div>
                <Button type="button" variant="outline" onClick={closeLane} className="rounded-full px-4">
                  <X className="h-4 w-4" />
                  Close
                </Button>
              </div>
              <div className="flex-1 overflow-y-auto px-5 py-5 sm:px-8 sm:py-6">
                {renderBusinessList(selectedLane.items.slice(0, Math.min(visibleCount, selectedLane.items.length)), viewMode, selectedLane.id)}
                {hasMoreInSelectedLane && (
                  <div className="mt-6 flex justify-center">
                    <Button type="button" variant="outline" onClick={() => setVisibleCount((current) => current + LOAD_MORE_COUNT)} className="rounded-full px-5">
                      <ChevronDown className="h-4 w-4" />
                      Load more
                    </Button>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {selectedBusiness && <BusinessModal business={selectedBusiness} onClose={closeBusiness} onBusinessUpdated={handleBusinessUpdated} />}

      <PreferenceOnboardingModal
        open={showPreferenceOnboarding}
        user={user}
        onClose={() => setShowPreferenceOnboarding(false)}
        onSaved={handlePreferencesSaved}
      />

      {loading && businesses.length === 0 && (
        <div className="fixed bottom-5 right-5 flex items-center gap-2 rounded-full border border-[hsl(var(--border))] bg-[hsl(var(--card))] px-3 py-2 text-ui text-[hsl(var(--muted-foreground))]">
          <Loader2 className="h-4 w-4 animate-spin" />
          Loading
        </div>
      )}
    </div>
  );
}
