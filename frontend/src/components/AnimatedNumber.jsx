import { useEffect, useRef, useState } from 'react'

// Small "living dashboard" touch: counts up from 0 to the target value once,
// on mount / when the target changes, using an eased requestAnimationFrame
// loop rather than a CSS transition (so it works on a plain text number).
export default function AnimatedNumber({ value, suffix = '', duration = 900 }) {
  const [display, setDisplay] = useState(0)
  const rafRef = useRef(null)

  useEffect(() => {
    const start = performance.now()
    const from = 0
    const to = typeof value === 'number' ? value : 0

    const tick = (now) => {
      const t = Math.min(1, (now - start) / duration)
      const eased = 1 - Math.pow(1 - t, 3)
      setDisplay(from + (to - from) * eased)
      if (t < 1) rafRef.current = requestAnimationFrame(tick)
    }
    rafRef.current = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(rafRef.current)
  }, [value, duration])

  const rounded = Number.isInteger(value) ? Math.round(display) : display.toFixed(1)
  return <>{rounded}{suffix}</>
}
