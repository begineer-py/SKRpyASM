import { BrowserRouter, Routes, Route } from "react-router-dom";


// 操！導入你的 Navbar 零件！
import Navbar from "./components/Navbar";
import UrlReconPage from "./pages/UrlReconPage/UrlReconPage";
import AICenterPage from "./pages/AICenterPage/AICenterPage";
import ExecutionMonitorPage from "./pages/ExecutionMonitorPage/ExecutionMonitorPage";
// 導入你的所有「頁面」
// 操！注意！你現在的檔案名是 TargetListPage.tsx，所以這裡也要改！
import TargetListPage from "./pages/index_page/index.tsx";
import TargetDashboard from "./pages/TargetDashboard/TargetDashboard.tsx";
import ScanResultPage from "./pages/NmapScanResultPage/ScanResultPage.tsx";
import SeedReconPage from "./pages/SeedReconPageSub/SeedReconPage.tsx";
import SubdomainDetailPage from "./pages/SubdomainDetailPage/SubdomainDetailPage.tsx";
import UrlDetailPage from "./pages/UrlDetailPage/UrlDetailPage.tsx";
import SkillLibraryPage from "./pages/SkillLibraryPage/SkillLibraryPage.tsx";
import APIKeyManagerPage from "./pages/APIKeyManagerPage/APIKeyManagerPage.tsx";
import AgentLLMConfigPage from "./pages/AgentLLMConfigPage/AgentLLMConfigPage.tsx";
import OverviewDetailPage from "./pages/OverviewDetailPage/OverviewDetailPage.tsx";
import CVEIntelligencePage from "./pages/CVEIntelligencePage/CVEIntelligencePage.tsx";
import SchedulerPage from "./pages/SchedulerPage/SchedulerPage.tsx";
import PentestConfigPage from "./pages/PentestConfigPage/PentestConfigPage.tsx";
function App() {
  return (
    <BrowserRouter>
      <Navbar />
      <main>
        <Routes>
          <Route path="/" element={<TargetListPage />} />
          <Route path="/target/:targetId" element={<TargetDashboard />} />
          <Route path="/overviews/:overviewId" element={<OverviewDetailPage />} />
          <Route path="/execution-monitor" element={<ExecutionMonitorPage />} />
          <Route path="/aicenter" element={<AICenterPage />} />
          <Route path="/target/nmap/:targetId" element={<ScanResultPage />} />
          <Route path="/target/:targetId/seed/:seedId/url_recon" element={<UrlReconPage />} />
          <Route path="/target/:targetId/seed/:seedId/subdomain" element={<SeedReconPage />} />
          <Route path="/target/:targetId/subdomain/:subdomainId" element={<SubdomainDetailPage />} />
          <Route path="/target/:targetId/url/:urlId" element={<UrlDetailPage />} />
          <Route path="/cve-intelligence" element={<CVEIntelligencePage />} />
          <Route path="/scheduler" element={<SchedulerPage />} />
          <Route path="/skills" element={<SkillLibraryPage />} />
          <Route path="/api-keys" element={<APIKeyManagerPage />} />
          <Route path="/agent-config" element={<AgentLLMConfigPage />} />
          <Route path="/pentest-config" element={<PentestConfigPage />} />
        </Routes>
      </main>
    </BrowserRouter>
  );
}

export default App;
