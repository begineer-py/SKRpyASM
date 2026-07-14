import { BrowserRouter, Route, Routes } from "react-router-dom";

import MainLayout from "./layouts/MainLayout";
import AICenterPage from "../pages/AICenterPage/AICenterPage";
import APIKeyManagerPage from "../pages/APIKeyManagerPage/APIKeyManagerPage";
import AgentLLMConfigPage from "../pages/AgentLLMConfigPage/AgentLLMConfigPage";
import CVEIntelligencePage from "../pages/CVEIntelligencePage/CVEIntelligencePage";
import ExecutionMonitorPage from "../pages/ExecutionMonitorPage/ExecutionMonitorPage";
import OverviewDetailPage from "../pages/OverviewDetailPage/OverviewDetailPage";
import PentestConfigPage from "../pages/PentestConfigPage/PentestConfigPage";
import ScanResultPage from "../pages/NmapScanResultPage/ScanResultPage";
import SchedulerPage from "../pages/SchedulerPage/SchedulerPage";
import SeedReconPage from "../pages/SeedReconPageSub/SeedReconPage";
import SkillEditPage from "../pages/SkillEditPage/SkillEditPage";
import SkillLibraryPage from "../pages/SkillLibraryPage/SkillLibraryPage";
import SubdomainDetailPage from "../pages/SubdomainDetailPage/SubdomainDetailPage";
import TargetDashboard from "../pages/TargetDashboard/TargetDashboard";
import TargetListPage from "../pages/index_page";
import UrlDetailPage from "../pages/UrlDetailPage/UrlDetailPage";
import UrlReconPage from "../pages/UrlReconPage/UrlReconPage";
import VulnerabilityEditPage from "../pages/VulnerabilityEditPage/VulnerabilityEditPage";
import VulnerabilityPage from "../pages/VulnerabilityPage/VulnerabilityPage";

export default function AppRouter() {
  return (
    <BrowserRouter>
      <MainLayout>
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
          <Route path="/skills/new" element={<SkillEditPage />} />
          <Route path="/skills/:skillId/edit" element={<SkillEditPage />} />
          <Route path="/api-keys" element={<APIKeyManagerPage />} />
          <Route path="/agent-config" element={<AgentLLMConfigPage />} />
          <Route path="/pentest-config" element={<PentestConfigPage />} />
          <Route path="/vulnerabilities" element={<VulnerabilityPage />} />
          <Route path="/vulnerabilities/:vulnId/edit" element={<VulnerabilityEditPage />} />
        </Routes>
      </MainLayout>
    </BrowserRouter>
  );
}
