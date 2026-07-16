import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import TargetDashboard from './TargetDashboard'

const assetMapMount = vi.fn()

vi.mock('../services/targetApi', () => ({
  gqlFetcher: vi.fn(async () => ({
    core_target_by_pk: { id: 7, core_seeds: [] },
    core_overview: [],
  })),
  GET_TARGET_DETAIL_QUERY: 'target-detail',
  GET_TARGET_SUBDOMAINS_QUERY: 'target-subdomains',
  GET_TARGET_IPS_QUERY: 'target-ips',
  GET_TARGET_OVERVIEWS_QUERY: 'target-overviews',
  GET_TARGET_URLS_QUERY: 'target-urls',
}))

vi.mock('../../../config', () => ({ GLOBAL_CONFIG: { DJANGO_API_BASE: '' } }))
vi.mock('../../../services/apiClient', () => ({ createCoreClient: () => ({ get: vi.fn() }) }))
vi.mock('../../../hooks/useApiQuery', () => ({ useApiQuery: () => ({ data: undefined, refetch: vi.fn() }) }))
vi.mock('../../../components/TechStackCVEReport', () => ({ default: () => null }))
vi.mock('../components/TargetHeader', () => ({ default: () => null }))
vi.mock('../components/SeedsTabContent', () => ({ default: () => null }))
vi.mock('../components/SubdomainsTabContent', () => ({ default: () => null }))
vi.mock('../components/IPsTabContent', () => ({ default: () => null }))
vi.mock('../components/URLsTabContent', () => ({ default: () => null }))
vi.mock('../components/AIOverviewTabContent', () => ({ default: () => null }))
vi.mock('../components/TargetExecutionsPanel', () => ({ TargetExecutionsPanel: () => null }))
vi.mock('../components/TargetFindingsPanel', () => ({ TargetFindingsPanel: () => null }))
vi.mock('../../ai/components/PlanTab', () => ({ default: () => null }))
vi.mock('../components/AssetMapTabContent', () => ({
  AssetMapTabContent: () => {
    assetMapMount()
    return <div>Asset map content</div>
  },
}))

function SearchParamsProbe() {
  const location = useLocation()
  return <output data-testid="search-params">{location.search}</output>
}

function renderDashboard(initialEntry: string) {
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <Routes>
        <Route path="/target/:targetId" element={<><TargetDashboard /><SearchParamsProbe /></>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('TargetDashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('mounts the asset map only after its nested tab is activated', async () => {
    // Given
    const user = userEvent.setup()
    renderDashboard('/target/7?source=alert')
    await screen.findByRole('tab', { name: 'Assets' })

    // When / Then
    expect(assetMapMount).not.toHaveBeenCalled()

    // When
    await user.click(screen.getByRole('tab', { name: 'Assets' }))
    expect(assetMapMount).not.toHaveBeenCalled()
    await user.click(screen.getByRole('tab', { name: 'Asset Map' }))

    // Then
    expect(await screen.findByText('Asset map content')).toBeVisible()
    expect(assetMapMount).toHaveBeenCalledTimes(1)
  })

  it('preserves unrelated search params when a primary tab changes from an invalid tab URL', async () => {
    // Given
    const user = userEvent.setup()
    renderDashboard('/target/7?tab=invalid&source=alert&filter=open')
    await screen.findByRole('tab', { name: 'Overview' })
    expect(screen.getByRole('tab', { name: 'Overview' })).toHaveAttribute('aria-selected', 'true')

    // When
    await user.click(screen.getByRole('tab', { name: 'Assets' }))

    // Then
    await waitFor(() => expect(screen.getByTestId('search-params')).toHaveTextContent('?tab=assets&source=alert&filter=open'))
  })
})
