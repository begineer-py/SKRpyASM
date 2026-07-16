import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { TargetAssetMapProbe } from '@/spec/TargetAssetMapProbe'

describe('Target asset map test environment', () => {
  it('selects a test asset through jsdom and the Vite alias', async () => {
    // Given
    const user = userEvent.setup()
    render(<TargetAssetMapProbe />)

    // When
    await user.click(screen.getByRole('button', { name: 'Select test asset' }))

    // Then
    expect(screen.getByRole('status')).toHaveTextContent('Target asset selected')
  })
})
