# apps/scanners/api.py
# Unified Scanner API Router

from ninja import Router

# Import individual scanner routers
from apps.scanners.nmap_scanner.api import router as nmap_router
from apps.scanners.subfinder.api import router as subfinder_router
from apps.scanners.nuclei_scanner.api import router as nuclei_router
from apps.scanners.get_all_url.api import router as get_all_url_router

router = Router()

# Mount them under the unified scanners namespace
router.add_router("/nmap", nmap_router, tags=["Scanners - Nmap"])
router.add_router("/subdomain", subfinder_router, tags=["Scanners - Subdomain"])
router.add_router("/vuln", nuclei_router, tags=["Scanners - Nuclei Vuln"])
router.add_router("/crawler", get_all_url_router, tags=["Scanners - Web Crawler"])
