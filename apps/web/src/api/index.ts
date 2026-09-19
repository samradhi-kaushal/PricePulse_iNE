import { listProducts, getProduct } from "./products";
import { listTrackedProducts, trackProduct, stopTracking, updateTrackedProductInterval, manualScrape } from "./tracking";
import { getDashboard } from "./dashboard";
import { getPriceHistory } from "./history";
import { getScrapeLogs } from "./scrapes";
import { listAlerts, getUnreadAlertCount, markAlertRead, markAllAlertsRead } from "./alerts";
import { listChanges, getTrackedProductChanges } from "./changes";

export {
  listProducts,
  getProduct,
  listTrackedProducts,
  trackProduct,
  stopTracking,
  updateTrackedProductInterval,
  manualScrape,
  getDashboard,
  getPriceHistory,
  getScrapeLogs,
  listAlerts,
  getUnreadAlertCount,
  markAlertRead,
  markAllAlertsRead,
  listChanges,
  getTrackedProductChanges,
};

export const api = {
  search: (query: string) => listProducts(query),
  listProducts: () => listTrackedProducts(),
  track: (productId: string) => trackProduct(productId),
  untrack: (id: string) => stopTracking(id),
  history: (id: string) => getPriceHistory(id),
  attempts: (id: string) => getScrapeLogs(id),
  manualScrape: (id: string) => manualScrape(id),
  updateInterval: (id: string, hours: number) => updateTrackedProductInterval(id, hours),
  alerts: (unreadOnly?: boolean) => listAlerts(unreadOnly),
  unreadAlertCount: () => getUnreadAlertCount(),
  markAlertRead: (id: string) => markAlertRead(id),
  markAllAlertsRead: () => markAllAlertsRead(),
  changes: () => listChanges(),
  productChanges: (id: string) => getTrackedProductChanges(id),
};

