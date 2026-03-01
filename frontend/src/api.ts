import type { Business, Review, Deal, ReviewCreate, User, AuthTokens, BusinessClaim, ClaimCreate, Subscription, SubscriptionCreate, TierInfo, CheckIn, CheckInCreate, UserCredibility, ActivityFeedItem, ActivityPulseItem, OwnerEvent, OwnerEventCreate, BusinessActivityStatus, ActivityComment, ActivityLikeResult, UserUpdate, UserPreferencesUpdate, ExploreSortMode, ExploreLanesResponse, DecideIntent, DecideResponse, SavedBusinessesResponse } from './types';

function resolveApiUrl(): string {
  const configured = (import.meta.env.VITE_API_URL || '').trim();

  if (!configured) {
    if (typeof window !== 'undefined' && !['localhost', '127.0.0.1'].includes(window.location.hostname)) {
      return '/api';
    }
    return 'http://localhost:8000/api';
  }

  const normalized = configured.replace(/\/$/, '');
  const apiBase = normalized.endsWith('/api') ? normalized : `${normalized}/api`;

  if (typeof window === 'undefined') {
    return apiBase;
  }

  const frontendIsLocal = ['localhost', '127.0.0.1'].includes(window.location.hostname);

  try {
    const configuredUrl = new URL(normalized, window.location.origin);
    const configuredIsLocal = ['localhost', '127.0.0.1'].includes(configuredUrl.hostname);
    if (!frontendIsLocal && configuredIsLocal) {
      return '/api';
    }
  } catch {
    
  }

  return apiBase;
}

const API_URL = resolveApiUrl();

export function buildApiUrl(path: string): string {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  if (API_URL.endsWith('/api') && normalizedPath.startsWith('/api/')) {
    return `${API_URL}${normalizedPath.slice(4)}`;
  }
  if (API_URL.endsWith('/api') && normalizedPath === '/api') {
    return API_URL;
  }
  return `${API_URL}${normalizedPath}`;
}

async function throwApiError(response: Response, fallback: string): Promise<never> {
  let message = `${fallback} (HTTP ${response.status})`;
  try {
    const data = await response.json();
    if (data?.detail && typeof data.detail === 'string') {
      message = data.detail;
    }
  } catch {
    
  }
  throw new Error(message);
}

function getAuthHeaders(includeJson: boolean = false): HeadersInit {
  const token = localStorage.getItem('vantage_token');
  const headers: HeadersInit = {};
  if (includeJson) {
    headers['Content-Type'] = 'application/json';
  }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

export const api = {
  
  async login(email: string, password: string): Promise<AuthTokens> {
    const response = await fetch(`${API_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      throw new Error(data.detail || 'Login failed');
    }
    return response.json();
  },

  async register(
    name: string,
    email: string,
    password: string,
    role: string,
    recaptchaToken: string,
    recaptchaAction: string
  ): Promise<AuthTokens> {
    const response = await fetch(`${API_URL}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name,
        email,
        password,
        role,
        recaptcha_token: recaptchaToken,
        recaptcha_action: recaptchaAction,
      }),
    });
    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      throw new Error(data.detail || 'Registration failed');
    }
    return response.json();
  },

  async getMe(): Promise<User> {
    const response = await fetch(`${API_URL}/auth/me`, {
      headers: getAuthHeaders(),
    });
    if (!response.ok) throw new Error('Not authenticated');
    return response.json();
  },

  async googleAuth(credential: string): Promise<AuthTokens> {
    const response = await fetch(`${API_URL}/auth/google`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ credential }),
    });
    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      throw new Error(data.detail || 'Google authentication failed');
    }
    return response.json();
  },

  async getUserProfile(userId: string): Promise<User> {
    const response = await fetch(`${API_URL}/users/${userId}`);
    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      throw new Error(data.detail || 'Failed to fetch user profile');
    }
    return response.json();
  },

  async updateMyProfile(updates: UserUpdate): Promise<User> {
    const response = await fetch(`${API_URL}/users/me`, {
      method: 'PUT',
      headers: getAuthHeaders(true),
      body: JSON.stringify(updates),
    });
    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      throw new Error(data.detail || 'Failed to update profile');
    }
    return response.json();
  },

  async getBusinesses(category?: string, sortBy?: string, search?: string): Promise<Business[]> {
    const params = new URLSearchParams();
    if (category) params.append('category', category);
    if (sortBy) params.append('sort_by', sortBy);
    if (search) params.append('search', search);
    const response = await fetch(`${API_URL}/businesses?${params}`);
    if (!response.ok) await throwApiError(response, 'Failed to fetch businesses');
    return response.json();
  },

  async getNearbyBusinesses(lat: number, lng: number, radius: number): Promise<Business[]> {
    const response = await fetch(
      `${API_URL}/businesses/nearby?lat=${lat}&lng=${lng}&radius=${radius}`
    );
    if (!response.ok) await throwApiError(response, 'Failed to fetch nearby businesses');
    return response.json();
  },

  async getBusiness(id: string): Promise<Business> {
    const response = await fetch(`${API_URL}/businesses/${id}`);
    if (!response.ok) await throwApiError(response, 'Failed to fetch business');
    return response.json();
  },

  async updateMyPreferences(preferences: UserPreferencesUpdate): Promise<User> {
    const response = await fetch(`${API_URL}/users/preferences`, {
      method: 'PUT',
      headers: getAuthHeaders(true),
      body: JSON.stringify(preferences),
    });
    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      throw new Error(data.detail || 'Failed to update preferences');
    }
    return response.json();
  },

  async updateBusinessProfile(
    businessId: string,
    updates: { short_description?: string; known_for?: string[] }
  ): Promise<Business> {
    const response = await fetch(`${API_URL}/businesses/${businessId}/profile`, {
      method: 'PUT',
      headers: getAuthHeaders(true),
      body: JSON.stringify(updates),
    });
    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      throw new Error(data.detail || 'Failed to update business profile');
    }
    return response.json();
  },

  async getBusinessReviews(businessId: string): Promise<Review[]> {
    const response = await fetch(`${API_URL}/reviews/business/${businessId}`);
    if (!response.ok) throw new Error('Failed to fetch reviews');
    return response.json();
  },

  async createReview(review: ReviewCreate): Promise<Review> {
    const response = await fetch(`${API_URL}/reviews`, {
      method: 'POST',
      headers: getAuthHeaders(true),
      body: JSON.stringify(review),
    });
    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      throw new Error(data.detail || 'Failed to create review');
    }
    return response.json();
  },

  async getDeals(): Promise<Deal[]> {
    const response = await fetch(`${API_URL}/deals`);
    if (!response.ok) throw new Error('Failed to fetch deals');
    return response.json();
  },

  async getBusinessDeals(businessId: string): Promise<Deal[]> {
    const response = await fetch(`${API_URL}/deals/business/${businessId}`);
    if (!response.ok) throw new Error('Failed to fetch deals');
    return response.json();
  },

  async submitClaim(claim: ClaimCreate): Promise<BusinessClaim> {
    const response = await fetch(`${API_URL}/claims`, {
      method: 'POST',
      headers: getAuthHeaders(true),
      body: JSON.stringify(claim),
    });
    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      throw new Error(data.detail || 'Failed to submit claim');
    }
    return response.json();
  },

  async getMyClaims(): Promise<BusinessClaim[]> {
    const response = await fetch(`${API_URL}/claims/my`, {
      headers: getAuthHeaders(),
    });
    if (!response.ok) throw new Error('Failed to fetch claims');
    return response.json();
  },

  async getSubscriptionTiers(): Promise<TierInfo[]> {
    const response = await fetch(`${API_URL}/subscriptions/tiers`);
    if (!response.ok) throw new Error('Failed to fetch tiers');
    return response.json();
  },

  async createSubscription(sub: SubscriptionCreate): Promise<Subscription> {
    const response = await fetch(`${API_URL}/subscriptions`, {
      method: 'POST',
      headers: getAuthHeaders(true),
      body: JSON.stringify(sub),
    });
    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      throw new Error(data.detail || 'Failed to create subscription');
    }
    return response.json();
  },

  async getMySubscriptions(): Promise<Subscription[]> {
    const response = await fetch(`${API_URL}/subscriptions/my`, {
      headers: getAuthHeaders(),
    });
    if (!response.ok) throw new Error('Failed to fetch subscriptions');
    return response.json();
  },

  async getBusinessSubscription(businessId: string): Promise<Subscription | null> {
    const response = await fetch(`${API_URL}/subscriptions/business/${businessId}`, {
      headers: getAuthHeaders(),
    });
    if (!response.ok) return null;
    return response.json();
  },

  async checkIn(data: CheckInCreate): Promise<CheckIn> {
    const response = await fetch(`${API_URL}/checkins`, {
      method: 'POST',
      headers: getAuthHeaders(true),
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.detail || 'Failed to check in');
    }
    return response.json();
  },

  async getActivityFeed(page: number = 1, pageSize: number = 20): Promise<{ items: ActivityFeedItem[]; has_more: boolean }> {
    const params = new URLSearchParams();
    params.append('page', page.toString());
    params.append('page_size', pageSize.toString());
    const response = await fetch(`${API_URL}/feed?${params}`);
    if (!response.ok) throw new Error('Failed to fetch activity feed');
    const data = await response.json();
    
    if (data && Array.isArray(data.items)) {
      return { items: data.items, has_more: !!data.has_more };
    }
    
    if (Array.isArray(data)) {
      return { items: data, has_more: data.length >= pageSize };
    }
    return { items: [], has_more: false };
  },

  async getActivityPulse(
    lat: number,
    lng: number,
    radius: number = 5,
    limit: number = 10
  ): Promise<ActivityPulseItem[]> {
    const params = new URLSearchParams();
    params.append('lat', lat.toString());
    params.append('lng', lng.toString());
    params.append('radius', radius.toString());
    params.append('limit', limit.toString());
    const response = await fetch(`${API_URL}/activity/pulse?${params}`);
    if (!response.ok) throw new Error('Failed to fetch pulse');
    const data = await response.json();
    return Array.isArray(data?.items) ? data.items : [];
  },

  async getOwnerEvents(options: {
    businessId?: string;
    lat?: number;
    lng?: number;
    radius?: number;
    includePast?: boolean;
    limit?: number;
  }): Promise<OwnerEvent[]> {
    const params = new URLSearchParams();
    if (options.businessId) {
      params.append('business_id', options.businessId);
    } else {
      if (typeof options.lat === 'number') params.append('lat', options.lat.toString());
      if (typeof options.lng === 'number') params.append('lng', options.lng.toString());
      params.append('radius', String(options.radius ?? 5));
    }
    if (options.includePast) params.append('include_past', 'true');
    if (typeof options.limit === 'number') params.append('limit', options.limit.toString());
    const response = await fetch(`${API_URL}/events?${params}`);
    if (!response.ok) throw new Error('Failed to fetch events');
    return response.json();
  },

  async createOwnerEvent(payload: OwnerEventCreate): Promise<OwnerEvent> {
    const response = await fetch(`${API_URL}/events`, {
      method: 'POST',
      headers: getAuthHeaders(true),
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      throw new Error(data.detail || 'Failed to create event');
    }
    return response.json();
  },

  async getBusinessActivity(businessId: string): Promise<BusinessActivityStatus> {
    const response = await fetch(`${API_URL}/businesses/${businessId}/activity`);
    if (!response.ok) throw new Error('Failed to fetch business activity');
    return response.json();
  },

  async getMyCredibility(): Promise<UserCredibility> {
    const response = await fetch(`${API_URL}/credibility/me`, {
      headers: getAuthHeaders(),
    });
    if (!response.ok) throw new Error('Failed to fetch credibility');
    return response.json();
  },

  async toggleActivityLike(activityId: string): Promise<ActivityLikeResult> {
    const response = await fetch(`${API_URL}/feed/${activityId}/like`, {
      method: 'POST',
      headers: getAuthHeaders(true),
    });
    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      throw new Error(data.detail || 'Failed to like activity');
    }
    return response.json();
  },

  async getActivityComments(activityId: string): Promise<ActivityComment[]> {
    const response = await fetch(`${API_URL}/feed/${activityId}/comments`);
    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      throw new Error(data.detail || 'Failed to fetch comments');
    }
    return response.json();
  },

  async addActivityComment(activityId: string, content: string): Promise<{ comment: ActivityComment; comments: number }> {
    const response = await fetch(`${API_URL}/feed/${activityId}/comments`, {
      method: 'POST',
      headers: getAuthHeaders(true),
      body: JSON.stringify({ content }),
    });
    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      throw new Error(data.detail || 'Failed to add comment');
    }
    return response.json();
  },

  async discoverBusinesses(
    lat: number,
    lng: number,
    radius: number = 5,
    category?: string,
    limit: number = 200,
    refresh: boolean = false,
    sortMode: ExploreSortMode = 'canonical'
  ): Promise<Business[]> {
    const params = new URLSearchParams();
    params.append('lat', lat.toString());
    params.append('lng', lng.toString());
    params.append('radius', radius.toString());
    params.append('limit', limit.toString());
    if (refresh) params.append('refresh', 'true');
    params.append('sort_mode', sortMode);
    if (category) params.append('category', category);
    const response = await fetch(`${API_URL}/discover?${params}`);
    if (!response.ok) await throwApiError(response, 'Failed to discover businesses');
    return response.json();
  },

  async getExploreLanes(
    lat: number,
    lng: number,
    radius: number = 5,
    limit: number = 120
  ): Promise<ExploreLanesResponse> {
    const params = new URLSearchParams();
    params.append('lat', lat.toString());
    params.append('lng', lng.toString());
    params.append('radius', radius.toString());
    params.append('limit', limit.toString());
    let response: Response;
    try {
      response = await fetch(`${API_URL}/explore/lanes?${params}`, {
        headers: getAuthHeaders(),
      });
    } catch {

      response = await fetch(`${API_URL}/explore/lanes?${params}`);
      if (!response.ok) await throwApiError(response, 'Failed to fetch explore lanes');
      return response.json();
    }
    if (!response.ok) await throwApiError(response, 'Failed to fetch explore lanes');
    return response.json();
  },

  async decideForMe(
    lat: number,
    lng: number,
    radiusKm: number,
    intent: DecideIntent,
    options?: {
      category?: string;
      limit?: number;
      constraints?: DecideIntent[];
    }
  ): Promise<DecideResponse> {
    const params = new URLSearchParams();
    params.append('lat', lat.toString());
    params.append('lng', lng.toString());
    params.append('radius_km', radiusKm.toString());
    params.append('intent', intent);
    params.append('limit', String(options?.limit ?? 3));
    if (options?.category) params.append('category', options.category);
    if (options?.constraints?.length) params.append('constraints', options.constraints.join(','));
    const response = await fetch(`${API_URL}/decide?${params}`);
    if (!response.ok) await throwApiError(response, 'Failed to get decide picks');
    return response.json();
  },

  async getSavedBusinesses(): Promise<SavedBusinessesResponse> {
    const response = await fetch(`${API_URL}/saved`, {
      headers: getAuthHeaders(),
    });
    if (!response.ok) await throwApiError(response, 'Failed to fetch saved businesses');
    return response.json();
  },

  async saveBusiness(businessId: string): Promise<{ business_id: string; saved: boolean }> {
    const response = await fetch(`${API_URL}/saved/${businessId}`, {
      method: 'POST',
      headers: getAuthHeaders(),
    });
    if (!response.ok) await throwApiError(response, 'Failed to save business');
    return response.json();
  },

  async unsaveBusiness(businessId: string): Promise<{ business_id: string; saved: boolean }> {
    const response = await fetch(`${API_URL}/saved/${businessId}`, {
      method: 'DELETE',
      headers: getAuthHeaders(),
    });
    if (!response.ok) await throwApiError(response, 'Failed to remove saved business');
    return response.json();
  },

  async purgeChains(): Promise<{ deleted: number; confidence_updated: number; total_scanned: number }> {
    const response = await fetch(`${API_URL}/purge-chains`, {
      method: 'DELETE',
      headers: getAuthHeaders(),
    });
    if (!response.ok) throw new Error('Failed to purge chain businesses');
    return response.json();
  },

};
