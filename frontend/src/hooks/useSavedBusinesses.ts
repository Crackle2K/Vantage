import { useCallback, useEffect, useState } from 'react';
import { api } from '@/api';
import { useAuth } from '@/contexts/AuthContext';
import type { Business } from '@/types';

const LOCAL_IDS_KEY = 'vantage-favorites';
const LOCAL_ITEMS_KEY = 'vantage-saved-businesses';

function getBusinessId(business: Business) {
  return business.id || business._id || business.name;
}

function readLocalIds(): string[] {
  try {
    const raw = localStorage.getItem(LOCAL_IDS_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function readLocalItems(): Business[] {
  try {
    const raw = localStorage.getItem(LOCAL_ITEMS_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function writeLocal(savedIds: string[], savedBusinesses: Business[]) {
  localStorage.setItem(LOCAL_IDS_KEY, JSON.stringify(savedIds));
  localStorage.setItem(LOCAL_ITEMS_KEY, JSON.stringify(savedBusinesses));
}

export function useSavedBusinesses() {
  const { isAuthenticated } = useAuth();
  const [savedIds, setSavedIds] = useState<string[]>([]);
  const [savedBusinesses, setSavedBusinesses] = useState<Business[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    if (!isAuthenticated) {
      const nextIds = readLocalIds();
      setSavedIds(nextIds);
      setSavedBusinesses(readLocalItems());
      setLoading(false);
      return;
    }

    try {
      const response = await api.getSavedBusinesses();
      const items = response.items ?? [];
      setSavedBusinesses(items);
      setSavedIds(items.map((item) => getBusinessId(item)));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load saved businesses');
      setSavedIds([]);
      setSavedBusinesses([]);
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const toggleSaved = useCallback(async (business: Business) => {
    const businessId = getBusinessId(business);
    const wasSaved = savedIds.includes(businessId);

    const nextIds = wasSaved
      ? savedIds.filter((id) => id !== businessId)
      : [businessId, ...savedIds];
    const nextBusinesses = wasSaved
      ? savedBusinesses.filter((item) => getBusinessId(item) !== businessId)
      : [business, ...savedBusinesses.filter((item) => getBusinessId(item) !== businessId)];

    setSavedIds(nextIds);
    setSavedBusinesses(nextBusinesses);
    setError(null);

    if (!isAuthenticated) {
      writeLocal(nextIds, nextBusinesses);
      return;
    }

    try {
      if (wasSaved) {
        await api.unsaveBusiness(businessId);
      } else {
        await api.saveBusiness(businessId);
      }
    } catch (err) {
      setSavedIds(savedIds);
      setSavedBusinesses(savedBusinesses);
      setError(err instanceof Error ? err.message : 'Failed to update saved businesses');
    }
  }, [isAuthenticated, savedBusinesses, savedIds]);

  return {
    savedIds,
    savedBusinesses,
    loading,
    error,
    refresh,
    toggleSaved,
  };
}
