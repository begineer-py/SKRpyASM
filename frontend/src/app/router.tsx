import { BrowserRouter, Route, Routes } from "react-router-dom";

import MainLayout from "./layouts/MainLayout";
import AICenterPage from "../features/ai/pages/AICenterPage";
import APIKeyManagerPage from "../pages/APIKeyManagerPage/APIKeyManagerPage";
import AgentLLMConfigPage from "../pages/AgentLLMConfigPage/AgentLLMConfigPage";
import CVEIntelligencePage from "../pages/CVEIntelligencePage/CVEIntelligencePage";
import ExecutionMonitorPage from "../features/ai/pages/ExecutionMonitorPage";
import OverviewDetailPage from "../features/ai/pages/OverviewDetailPage";
import PentestConfigPage from "../pages/PentestConfigPage/PentestConfigPage";
import ScanResultPage from "../pages/NmapScanResultPage/ScanResultPage";
import SchedulerPage from "../features/scheduler/pages/SchedulerPage";
import SeedReconPage from "../features/target/pages/SeedReconPage";
import SkillEditPage from "../features/skill/pages/SkillEditPage";
import SkillLibraryPage from "../features/skill/pages/SkillLibraryPage";
import SubdomainDetailPage from "../features/target/pages/SubdomainDetailPage";
import TargetDashboard from "../features/target/pages/TargetDashboard";
import TargetListPage from "../features/target/pages/TargetListPage";
import UrlDetailPage from "../features/target/pages/UrlDetailPage";
import UrlReconPage from "../features/target/pages/UrlReconPage";
import VulnerabilityEditPage from "../features/vulnerability/pages/VulnerabilityEditPage";
import VulnerabilityPage from "../features/vulnerability/pages/VulnerabilityPage";

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
