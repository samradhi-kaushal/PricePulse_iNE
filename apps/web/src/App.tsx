import { useState } from "react";
import { BrowserRouter, Routes, Route, Navigate, useLocation } from "react-router-dom";
import { Sidebar } from "./components/Sidebar";
import { Header } from "./components/Header";

import { DashboardPage } from "./pages/DashboardPage";
import { ProductsPage } from "./pages/ProductsPage";
import { ProductDetailPage } from "./pages/ProductDetailPage";
import { TrackedProductsPage } from "./pages/TrackedProductsPage";
import { PriceHistoryPage } from "./pages/PriceHistoryPage";
import { ScrapeActivityPage } from "./pages/ScrapeActivityPage";
import { SettingsPage } from "./pages/SettingsPage";

import "./styles.css";

function getPageTitle(pathname: string): string {
  if (pathname.startsWith("/products/")) return "Product Detail";
  if (pathname === "/products") return "Product Catalogue";
  if (pathname.startsWith("/tracked/") && pathname.includes("/history")) return "Price History";
  if (pathname === "/tracked") return "Tracked Products";
  if (pathname === "/history") return "Price History";
  if (pathname === "/scrapes") return "Scrape Activity";
  if (pathname === "/settings") return "Settings";
  return "Dashboard";
}

function MainLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();

  const title = getPageTitle(location.pathname);

  const handleRefresh = () => {
    window.location.reload();
  };

  return (
    <div className="app-layout">
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <div className="main-wrapper">
        <Header
          title={title}
          onRefresh={handleRefresh}
          onToggleSidebar={() => setSidebarOpen((prev) => !prev)}
        />
        <main className="page-container">
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/products" element={<ProductsPage />} />
            <Route path="/products/:id" element={<ProductDetailPage />} />
            <Route path="/tracked" element={<TrackedProductsPage />} />
            <Route path="/tracked/:id/history" element={<PriceHistoryPage />} />
            <Route path="/history" element={<PriceHistoryPage />} />
            <Route path="/scrapes" element={<ScrapeActivityPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <MainLayout />
    </BrowserRouter>
  );
}
