"use client"

import { useEffect, useRef } from "react"

/* ── Color palette — Periwinkle / Shadow Grey / True Cobalt ── */
type RGB = [number, number, number]
const PERIWINKLE: RGB = [212, 194, 252]
const SOFT_PERI: RGB = [153, 143, 199]
const SHADOW: RGB = [40, 38, 44]
const COBALT: RGB = [20, 36, 138]

/* ── Theme detection for dynamic contrast ── */
function isDarkMode(): boolean {
  return document.documentElement.classList.contains('dark')
}

function rgba(c: RGB, a: number) {
  return `rgba(${c[0]},${c[1]},${c[2]},${a})`
}

/* ── Types ── */
interface NetNode {
  x: number
  y: number
  ox: number
  oy: number
  r: number
  depth: number
  phase: number
  spawn: number
  alive: number
  color: RGB
  edges: number[]
}

interface FlowDot {
  from: number
  to: number
  t: number
  speed: number
}

/* ── Golden angle for organic spiral placement ── */
const GA = 2.39996323

/* ── Build the full network graph ── */
function buildNetwork(w: number, h: number): NetNode[] {
  const cx = w / 2
  const cy = h / 2
  const span = Math.min(w, h) * 0.46  // Larger spread
  const nodes: NetNode[] = []

  const add = (x: number, y: number, r: number, depth: number, spawn: number, color: RGB) => {
    nodes.push({
      x, y, ox: x, oy: y, r,
      depth: Math.max(0.3, Math.min(1, depth)),
      phase: Math.random() * 6.283,
      spawn, alive: 0, color, edges: [],
    })
  }

  // Central hub node — larger
  add(cx, cy, 14, 1, 0, PERIWINKLE)

  // More nodes per ring for density
  const rings: [number, number, number, number, number, number][] = [
    [6,  0.18, 7.0, 0.95, 0.2,  0.22],
    [8,  0.36, 5.5, 0.82, 1.0,  0.25],
    [10, 0.56, 4.0, 0.65, 2.2,  0.22],
    [12, 0.78, 3.0, 0.45, 3.8,  0.18],
    [8,  0.94, 2.2, 0.33, 5.6,  0.16],
  ]

  let idx = 1
  for (const [count, distPct, nodeR, depthBase, sStart, sGap] of rings) {
    for (let i = 0; i < count; i++) {
      const a = idx * GA + (Math.random() - 0.5) * 0.45
      const dist = distPct * span + (Math.random() - 0.5) * span * 0.06
      // Color variety
      const color: RGB =
        i % 7 === 0 ? COBALT :
        i % 5 === 0 ? SHADOW :
        i % 3 === 0 ? SOFT_PERI : PERIWINKLE
      add(
        cx + Math.cos(a) * dist,
        cy + Math.sin(a) * dist,
        nodeR,
        depthBase + (Math.random() - 0.5) * 0.08,
        sStart + i * sGap,
        color,
      )
      idx++
    }
  }

  /* ── Build FULLY connected network — every node connects to ALL nearby nodes ── */
  const connect = (a: number, b: number) => {
    if (a === b) return
    if (!nodes[a].edges.includes(b)) { nodes[a].edges.push(b); nodes[b].edges.push(a) }
  }

  // Connect every pair of nodes within a distance threshold
  const threshold = span * 0.48
  for (let i = 0; i < nodes.length; i++) {
    for (let j = i + 1; j < nodes.length; j++) {
      const d = Math.hypot(nodes[i].ox - nodes[j].ox, nodes[i].oy - nodes[j].oy)
      if (d < threshold) {
        connect(i, j)
      }
    }
  }

  // Ensure center connects to everything in first 3 rings
  const ring3End = 1 + 6 + 8 + 10 // = 25
  for (let i = 1; i < Math.min(ring3End, nodes.length); i++) {
    connect(0, i)
  }

  return nodes
}

/* ── Exported Canvas Component ── */
export function NeuralNetwork({ className = "" }: { className?: string }) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const rafRef = useRef(0)
  const stateRef = useRef<{
    nodes: NetNode[]
    dots: FlowDot[]
    t0: number
    built: boolean
  }>({ nodes: [], dots: [], t0: 0, built: false })

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext("2d")
    if (!ctx) return

    /* Handle resize */
    const resize = () => {
      const rect = canvas.getBoundingClientRect()
      if (rect.width === 0 || rect.height === 0) return
      const dpr = Math.min(window.devicePixelRatio || 1, 2)
      canvas.width = rect.width * dpr
      canvas.height = rect.height * dpr
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)

      const s = stateRef.current
      const fresh = buildNetwork(rect.width, rect.height)
      // On subsequent rebuilds, skip spawn animation
      if (s.built) fresh.forEach((n) => { n.alive = 1 })
      s.nodes = fresh
      if (!s.built) { s.t0 = performance.now(); s.built = true }
    }
    resize()
    const ro = new ResizeObserver(resize)
    ro.observe(canvas)

    const isDark = () => document.documentElement.classList.contains("dark")

    /* ── Main animation loop ── */
    const tick = (now: number) => {
      const s = stateRef.current
      if (!s.nodes.length) { rafRef.current = requestAnimationFrame(tick); return }
      const elapsed = (now - s.t0) / 1000
      const rect = canvas.getBoundingClientRect()
      const w = rect.width, h = rect.height
      if (w === 0 || h === 0) { rafRef.current = requestAnimationFrame(tick); return }
      const dark = isDark()
      ctx.clearRect(0, 0, w, h)

      /* Update nodes */
      for (const n of s.nodes) {
        if (elapsed >= n.spawn && n.alive < 1) n.alive = Math.min(1, n.alive + 0.016)
        n.phase += 0.006 + n.depth * 0.004
        n.x = n.ox + Math.sin(n.phase) * 4 * n.depth
        n.y = n.oy + Math.cos(n.phase * 0.73 + 1) * 3 * n.depth
      }

      /* Spawn flow particles */
      if (Math.random() < 0.055) {
        const alive = s.nodes.filter((n) => n.alive > 0.8)
        if (alive.length > 1) {
          const src = alive[Math.floor(Math.random() * alive.length)]
          const si = s.nodes.indexOf(src)
          const targets = src.edges.filter((e) => s.nodes[e].alive > 0.5)
          if (targets.length) {
            const ti = targets[Math.floor(Math.random() * targets.length)]
            s.dots.push({ from: si, to: ti, t: 0, speed: 0.003 + Math.random() * 0.007 })
          }
        }
      }
      if (s.dots.length > 18) s.dots.splice(0, s.dots.length - 18)
      s.dots = s.dots.filter((d) => { d.t += d.speed; return d.t < 1 })

      /* ── Draw connections ── */
      const drawn = new Set<string>()
      for (let ni = 0; ni < s.nodes.length; ni++) {
        const n = s.nodes[ni]
        if (n.alive <= 0) continue
        for (const ei of n.edges) {
          const key = ni < ei ? `${ni}-${ei}` : `${ei}-${ni}`
          if (drawn.has(key)) continue
          drawn.add(key)
          const m = s.nodes[ei]
          if (m.alive <= 0) continue
          const a = Math.min(n.alive, m.alive) * 0.14 * (n.depth + m.depth) / 2
          ctx.beginPath()
          ctx.moveTo(n.x, n.y)
          ctx.lineTo(m.x, m.y)
          ctx.strokeStyle = dark ? rgba(PERIWINKLE, a * 2.2) : rgba(COBALT, a * 2.5)
          ctx.lineWidth = ni === 0 || ei === 0 ? 1.6 : 0.6
          ctx.stroke()
        }
      }

      /* ── Draw flow particles ── */
      for (const d of s.dots) {
        const a = s.nodes[d.from], b = s.nodes[d.to]
        const x = a.x + (b.x - a.x) * d.t
        const y = a.y + (b.y - a.y) * d.t
        const fade = d.t < 0.15 ? d.t / 0.15 : d.t > 0.85 ? (1 - d.t) / 0.15 : 1

        ctx.beginPath()
        ctx.arc(x, y, 2.2, 0, 6.283)
        ctx.fillStyle = dark ? rgba(PERIWINKLE, fade * 0.7) : rgba(COBALT, fade * 0.8)
        ctx.fill()

        // Soft glow around particle
        const g = ctx.createRadialGradient(x, y, 0, x, y, 9)
        g.addColorStop(0, dark ? rgba(PERIWINKLE, fade * 0.18) : rgba(COBALT, fade * 0.22))
        g.addColorStop(1, rgba(PERIWINKLE, 0))
        ctx.fillStyle = g
        ctx.beginPath()
        ctx.arc(x, y, 9, 0, 6.283)
        ctx.fill()
      }

      /* ── Draw nodes ── */
      for (let ni = 0; ni < s.nodes.length; ni++) {
        const n = s.nodes[ni]
        if (n.alive <= 0) continue
        const pulse = 1 + Math.sin(elapsed * 1.6 + n.phase) * 0.07
        const r = n.r * pulse * n.alive
        const a = n.alive * n.depth
        const isCenter = ni === 0

        // Glow halo for larger nodes
        if (n.r >= 4) {
          const gr = r * (isCenter ? 5 : 3.5)
          const gg = ctx.createRadialGradient(n.x, n.y, r * 0.4, n.x, n.y, gr)
          gg.addColorStop(0, rgba(n.color, a * (isCenter ? 0.28 : 0.1)))
          gg.addColorStop(1, rgba(n.color, 0))
          ctx.fillStyle = gg
          ctx.beginPath()
          ctx.arc(n.x, n.y, gr, 0, 6.283)
          ctx.fill()
        }

        // Node body
        ctx.beginPath()
        ctx.arc(n.x, n.y, r, 0, 6.283)
        if (isCenter) {
          ctx.fillStyle = dark ? rgba(PERIWINKLE, a * 0.88) : rgba(PERIWINKLE, a * 0.95)
          ctx.fill()
          ctx.strokeStyle = dark ? rgba(PERIWINKLE, a * 0.45) : rgba(COBALT, a * 0.65)
          ctx.lineWidth = 2.5
          ctx.stroke()
          // Secondary glow ring
          ctx.beginPath()
          ctx.arc(n.x, n.y, r * 1.8, 0, 6.283)
          ctx.strokeStyle = dark ? rgba(PERIWINKLE, a * 0.12 * (1 + Math.sin(elapsed * 2) * 0.3)) : rgba(PERIWINKLE, a * 0.18 * (1 + Math.sin(elapsed * 2) * 0.3))
          ctx.lineWidth = 1
          ctx.stroke()
        } else {
          ctx.fillStyle = dark ? rgba(n.color, a * 0.65) : rgba(n.color, a * 0.75)
          ctx.fill()
          if (n.r >= 4) {
            ctx.strokeStyle = dark ? rgba(n.color, a * 0.22) : rgba(n.color, a * 0.35)
            ctx.lineWidth = 1
            ctx.stroke()
          }
        }
      }

      rafRef.current = requestAnimationFrame(tick)
    }

    rafRef.current = requestAnimationFrame(tick)
    return () => {
      cancelAnimationFrame(rafRef.current)
      ro.disconnect()
    }
  }, [])

  return <canvas ref={canvasRef} className={`block w-full h-full ${className}`} />
}
