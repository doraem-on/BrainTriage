import { useEffect, useRef } from 'react'
import * as THREE from 'three'

// Procedurally generates a stylized "neural network brain": points sampled
// inside a two-lobed, sulcus-textured ellipsoid, wired to their nearest
// neighbors. Abstract on purpose — this represents the AI reasoning over
// the diagnostic pipeline, not an anatomical rendering, no external assets.
function buildBrainPoints(count) {
  const pts = []
  for (let i = 0; i < count; i++) {
    // rejection-sample points inside a lobed ellipsoid
    let x, y, z, r
    do {
      x = (Math.random() * 2 - 1)
      y = (Math.random() * 2 - 1)
      z = (Math.random() * 2 - 1)
      const lobeSplit = 0.22 * Math.sign(x || 1)
      const dx = x - lobeSplit * 0.4
      r = (dx * dx) / 0.62 + (y * y) / 0.72 + (z * z) / 0.9
    } while (r > 1)

    // sulci/gyri texture: low-frequency noise pushes points into ridges
    const wobble = Math.sin(x * 7 + y * 5) * 0.03 + Math.cos(z * 6 - y * 4) * 0.03
    pts.push([x * 1.6 + wobble, y * 1.3 + wobble, z * 1.5 + wobble])
  }
  return pts
}

function buildEdges(points, neighborCount, maxDist) {
  const edges = []
  for (let i = 0; i < points.length; i++) {
    const dists = []
    for (let j = 0; j < points.length; j++) {
      if (i === j) continue
      const [ax, ay, az] = points[i]
      const [bx, by, bz] = points[j]
      const d = Math.hypot(ax - bx, ay - by, az - bz)
      if (d < maxDist) dists.push([d, j])
    }
    dists.sort((a, b) => a[0] - b[0])
    for (let k = 0; k < Math.min(neighborCount, dists.length); k++) {
      const j = dists[k][1]
      if (j > i) edges.push([i, j])
    }
  }
  return edges
}

export default function NeuralBrainCanvas({ nodeColor = 0x3987e5, edgeColor = 0x2c2c2a, height = 320 }) {
  const mountRef = useRef(null)

  useEffect(() => {
    const mount = mountRef.current
    if (!mount) return

    const width = mount.clientWidth
    const scene = new THREE.Scene()
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 100)
    camera.position.set(0, 0, 6.2)

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    renderer.setSize(width, height)
    mount.appendChild(renderer.domElement)

    const group = new THREE.Group()
    scene.add(group)

    const rawPoints = buildBrainPoints(260)
    const edgePairs = buildEdges(rawPoints, 3, 0.55)

    const nodeGeo = new THREE.BufferGeometry()
    const positions = new Float32Array(rawPoints.length * 3)
    rawPoints.forEach(([x, y, z], i) => {
      positions[i * 3] = x
      positions[i * 3 + 1] = y
      positions[i * 3 + 2] = z
    })
    nodeGeo.setAttribute('position', new THREE.BufferAttribute(positions, 3))
    const nodeMat = new THREE.PointsMaterial({
      color: nodeColor, size: 0.05, transparent: true, opacity: 0.9,
      blending: THREE.AdditiveBlending, depthWrite: false,
    })
    group.add(new THREE.Points(nodeGeo, nodeMat))

    const edgePositions = new Float32Array(edgePairs.length * 6)
    edgePairs.forEach(([a, b], i) => {
      edgePositions[i * 6] = rawPoints[a][0]
      edgePositions[i * 6 + 1] = rawPoints[a][1]
      edgePositions[i * 6 + 2] = rawPoints[a][2]
      edgePositions[i * 6 + 3] = rawPoints[b][0]
      edgePositions[i * 6 + 4] = rawPoints[b][1]
      edgePositions[i * 6 + 5] = rawPoints[b][2]
    })
    const edgeGeo = new THREE.BufferGeometry()
    edgeGeo.setAttribute('position', new THREE.BufferAttribute(edgePositions, 3))
    const edgeMat = new THREE.LineBasicMaterial({ color: edgeColor, transparent: true, opacity: 0.35 })
    group.add(new THREE.LineSegments(edgeGeo, edgeMat))

    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    let raf
    let t = 0
    const animate = () => {
      t += reduceMotion ? 0 : 0.0022
      group.rotation.y = t
      group.rotation.x = Math.sin(t * 0.6) * 0.12
      renderer.render(scene, camera)
      raf = requestAnimationFrame(animate)
    }
    animate()

    const handleResize = () => {
      const w = mount.clientWidth
      camera.aspect = w / height
      camera.updateProjectionMatrix()
      renderer.setSize(w, height)
    }
    window.addEventListener('resize', handleResize)

    return () => {
      cancelAnimationFrame(raf)
      window.removeEventListener('resize', handleResize)
      nodeGeo.dispose()
      nodeMat.dispose()
      edgeGeo.dispose()
      edgeMat.dispose()
      renderer.dispose()
      mount.removeChild(renderer.domElement)
    }
  }, [nodeColor, edgeColor, height])

  return <div ref={mountRef} style={{ width: '100%', height, cursor: 'grab' }} aria-hidden="true" />
}
