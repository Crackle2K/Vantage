import type { Business, Review, Deal, ReviewCreate, Category, User, AuthTokens } from './types';

const API_URL = 'http://localhost:8000/api';

function getAuthHeaders(): HeadersInit {
  const token = localStorage.getItem('localboost_token');
  const headers: HeadersInit = { 'Content-Type': 'application/json' };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

export const api = {
  // ─── Auth ────────────────────────────────────
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

  async register(name: string, email: string, password: string, role: string): Promise<AuthTokens> {
    const response = await fetch(`${API_URL}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, email, password, role }),
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

  // ─── Businesses ──────────────────────────────
  async getBusinesses(category?: string, sortBy?: string, search?: string): Promise<Business[]> {
    const params = new URLSearchParams();
    if (category) params.append('category', category);
    if (sortBy) params.append('sort_by', sortBy);
    if (search) params.append('search', search);
    const response = await fetch(`${API_URL}/businesses?${params}`);
    if (!response.ok) throw new Error('Failed to fetch businesses');
    return response.json();
  },

  async getBusinessFeed(page: number = 1, pageSize: number = 10, category?: string, search?: string, sortBy?: string): Promise<{
    businesses: Business[];
    total: number;
    page: number;
    page_size: number;
    has_more: boolean;
  }> {
    const params = new URLSearchParams();
    params.append('page', page.toString());
    params.append('page_size', pageSize.toString());
    if (category) params.append('category', category);
    if (search) params.append('search', search);
    if (sortBy) params.append('sort_by', sortBy);
    const response = await fetch(`${API_URL}/businesses/feed?${params}`);
    if (!response.ok) throw new Error('Failed to fetch business feed');
    return response.json();
  },

  async getNearbyBusinesses(lat: number, lng: number, radius: number): Promise<Business[]> {
    const response = await fetch(
      `${API_URL}/businesses/nearby?lat=${lat}&lng=${lng}&radius=${radius}`
    );
    if (!response.ok) throw new Error('Failed to fetch nearby businesses');
    return response.json();
  },

  async getBusiness(id: string): Promise<Business> {
    const response = await fetch(`${API_URL}/businesses/${id}`);
    if (!response.ok) throw new Error('Failed to fetch business');
    return response.json();
  },

  // ─── Reviews ─────────────────────────────────
  async getBusinessReviews(businessId: string): Promise<Review[]> {
    const response = await fetch(`${API_URL}/reviews/business/${businessId}`);
    if (!response.ok) throw new Error('Failed to fetch reviews');
    return response.json();
  },

  async createReview(review: ReviewCreate): Promise<Review> {
    const response = await fetch(`${API_URL}/reviews`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(review),
    });
    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      throw new Error(data.detail || 'Failed to create review');
    }
    return response.json();
  },

  // ─── Deals ───────────────────────────────────
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

  // ─── Categories ──────────────────────────────
  getCategories(): Category[] {
    return [
      { value: 'food', label: 'Food & Dining', icon: 'utensils' },
      { value: 'retail', label: 'Retail & Shopping', icon: 'shopping-bag' },
      { value: 'services', label: 'Services', icon: 'wrench' },
      { value: 'entertainment', label: 'Entertainment', icon: 'music' },
      { value: 'health', label: 'Health & Wellness', icon: 'heart-pulse' },
    ];
  },
};
