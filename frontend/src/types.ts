export type CategoryType = 'food' | 'retail' | 'services' | 'entertainment' | 'health';

export interface Business {
  id: string;
  _id?: string;
  name: string;
  category: CategoryType;
  description: string;
  address: string;
  phone: string;
  email: string;
  website?: string;
  image_url: string;
  rating: number;
  review_count: number;
  has_deals: boolean;
  distance?: number;
  location?: {
    type: string;
    coordinates: [number, number];
  };
}

export interface Review {
  id: string;
  _id?: string;
  business_id: string;
  user_id: string;
  user_name: string;
  rating: number;
  comment: string;
  created_at: string;
  verified: boolean;
}

export interface Deal {
  id: string;
  _id?: string;
  business_id: string;
  business_name?: string;
  title: string;
  description: string;
  discount_type: string;
  discount_value: number;
  code?: string;
  valid_until: string;
  is_active: boolean;
}

export interface ReviewCreate {
  business_id: string;
  rating: number;
  comment: string;
}

export interface Category {
  value: string;
  label: string;
  icon?: string;
}

export interface User {
  id: string;
  _id?: string;
  name: string;
  email: string;
  role: 'customer' | 'business_owner' | 'admin';
  created_at?: string;
}

export interface AuthTokens {
  access_token: string;
  token_type: string;
}
