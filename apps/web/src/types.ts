export type SearchProduct = {
  id: string | number;
  external_id?: string;
  name: string;
  brand?: string;
  category?: string;
  sku?: string;
  product_url?: string;
};

export type PricePoint = {
  id: string;
  price: number;
  currency: string;
  stock?: number | null;
  in_stock?: boolean;
  recorded_at?: string;
  observed_at?: string;
};

export type Attempt = {
  id: string;
  attempt_number: number;
  product_name?: string;
  product_external_id?: string;
  attempted_at?: string;
  started_at?: string;
  finished_at?: string | null;
  status: string;
  error_code?: string | null;
  error_message?: string | null;
  duration_ms?: number | null;
};

export type ProductChange = {
  id: string;
  tracked_product_id: string;
  product_name: string;
  change_type: "PRICE_INCREASE" | "PRICE_DECREASE" | "STOCK_INCREASE" | "STOCK_DECREASE";
  previous_value: string;
  current_value: string;
  detected_at: string;
};

export type AlertItem = {
  id: string;
  tracked_product_id: string;
  product_name: string;
  alert_type: "PRICE_INCREASE" | "PRICE_DECREASE" | "STOCK_INCREASE" | "STOCK_DECREASE";
  title: string;
  message: string;
  is_read: boolean;
  created_at: string;
};

export type Product = {
  id: string;
  external_id: string;
  name: string;
  slug: string;
  brand: string;
  category: string;
  sku: string;
  product_url: string;
  is_tracked: boolean;
};

export type TrackedProduct = {
  id: string;
  product?: Product;
  source_product_id?: string;
  name?: string;
  is_active?: boolean;
  active?: boolean;
  scrape_interval_hours?: number;
  next_scrape_at: string;
  created_at?: string;
  updated_at?: string;
  latest_price?: PricePoint | null;
  latest_scrape?: Attempt | null;
  latestPrice?: PricePoint | null;
  latestAttempt?: Attempt | null;
};

export type DashboardData = {
  tracked_product_count: number;
  successful_scrape_count: number;
  retry_count: number;
  failed_scrape_count: number;
  unread_alert_count: number;
  recent_tracked_products: TrackedProduct[];
  recent_scrape_activity: Attempt[];
  recent_changes?: ProductChange[];
  recent_alerts?: AlertItem[];
};

