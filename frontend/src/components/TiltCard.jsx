import { useRef } from 'react'

// Lightweight 3D hover tilt: tracks pointer position within the card and
// rotates it in perspective space, with a synced specular highlight. No
// external tilt library — just pointer math + CSS custom properties.
export default function TiltCard({ children, className = '', style, maxTilt = 8, ...rest }) {
  const ref = useRef(null)

  const handleMove = (e) => {
    const el = ref.current
    if (!el) return
    const rect = el.getBoundingClientRect()
    const px = (e.clientX - rect.left) / rect.width
    const py = (e.clientY - rect.top) / rect.height
    const rotateY = (px - 0.5) * maxTilt * 2
    const rotateX = (0.5 - py) * maxTilt * 2
    el.style.setProperty('--tilt-x', `${rotateX}deg`)
    el.style.setProperty('--tilt-y', `${rotateY}deg`)
    el.style.setProperty('--glare-x', `${px * 100}%`)
    el.style.setProperty('--glare-y', `${py * 100}%`)
    el.style.setProperty('--glare-opacity', '1')
  }

  const handleLeave = () => {
    const el = ref.current
    if (!el) return
    el.style.setProperty('--tilt-x', '0deg')
    el.style.setProperty('--tilt-y', '0deg')
    el.style.setProperty('--glare-opacity', '0')
  }

  return (
    <div
      ref={ref}
      className={`tilt-card ${className}`}
      style={style}
      onMouseMove={handleMove}
      onMouseLeave={handleLeave}
      {...rest}
    >
      <div className="tilt-card-inner">
        {children}
        <div className="tilt-card-glare" />
      </div>
    </div>
  )
}
