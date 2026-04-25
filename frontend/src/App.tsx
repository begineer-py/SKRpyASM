// 檔案路徑: frontend/src/App.tsx
import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";

// 操！導入你的 Navbar 零件！
import Navbar from "./components/Navbar";
import UrlReconPage from "./pages/UrlReconPage/UrlReconPage";
import AICenterPage from "./pages/AICenterPage/AICenterPage";
// 導入你的所有「頁面」
// 操！注意！你現在的檔案名是 TargetListPage.tsx，所以這裡也要改！
import TargetListPage from "./pages/index_page/index.tsx";
import TargetDashboard from "./pages/TargetDashboard/TargetDashboard.tsx";
import ScanResultPage from "./pages/NmapScanResultPage/ScanResultPage.tsx";
import SeedReconPage from "./pages/SeedReconPageSub/SeedReconPage.tsx";
import SubdomainDetailPage from "./pages/SubdomainDetailPage/SubdomainDetailPage.tsx";
function App() {
  return (
    <BrowserRouter>
      {/* 操！看！直接用 <Navbar /> 就好了！是不是乾淨多了？！ */}
      <Navbar />

      <main style={{ padding: "20px" }}>
        {" "}
        {/* 給主要內容一個 padding */}
        <Routes>
          <Route path="/" element={<TargetListPage />} />
          <Route path="/target/:targetId" element={<TargetDashboard />} />
          <Route path="/aicenter" element={<AICenterPage />} />
          <Route path="/target/nmap/:targetId" element={<ScanResultPage />} />
          <Route
            path="/target/:targetId/seed/:seedId/url/:urlId"
            element={<UrlReconPage />}
          />
          <Route
            path="/target/:targetId/seed/:seedId/subdomain"
            element={<SeedReconPage />}
          />
          <Route
            path="/target/:targetId/subdomain/:subdomainId"
            element={<SubdomainDetailPage />}
          />
        </Routes>
      </main>
    </BrowserRouter>
  );
}

export default App;
