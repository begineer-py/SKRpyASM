import { useState } from 'react'

export function TargetAssetMapProbe() {
  const [isSelected, setIsSelected] = useState(false)

  return (
    <>
      <button type="button" onClick={() => setIsSelected(true)}>
        Select test asset
      </button>
      {isSelected ? <output role="status">Target asset selected</output> : null}
    </>
  )
}
