import React, { useEffect, useMemo, useRef, useState } from 'react'
import { Activity, ArrowRight, ShieldAlert, Sparkles, Users, ScanSearch, ChevronLeft, Circle, ShieldCheck, TrendingUp, AlertTriangle } from 'lucide-react'
import { VideoPanel } from './components/VideoPanel'
import { MetricCard } from './components/MetricCard'
import { CrowdChart } from './components/CrowdChart'
import { Toast } from './components/Toast'
import { EventAnalysisPanel } from './components/EventAnalysisPanel'

const API_BASE_URL = 'http://localhost:5000'

export default function App() {
  const [activeModule, setActiveModule] = useState(null)
  const [data, setData] = useState(null)
  const [frameData, setFrameData] = useState(null)
  const [events, setEvents] = useState([])
  const [isLoading, setIsLoading] = useState(true)
  const [apiError, setApiError] = useState('')
  const [showToast, setShowToast] = useState(false)
  const [toastMessage, setToastMessage] = useState('')
  const [toastType, setToastType] = useState('info')

  const lastStatusRef = useRef(null)
  const alertLatchedRef = useRef(false)
  const normalStreakRef = useRef(0)

  const safeData = data || {
    count: 0,
    average: 0,
    spike: 0,
    status: 'NORMAL',
    history: [],
    density_index: 0,
    occupancy_ratio: 0,
    concentration_ratio: 0,
    recent_growth: 0,
    sudden_crowd_formation: false,
    overcrowded: false,
    stampede_risk: false,
    stampede_risk_score: 0,
    unusual_gathering: false,
    risk_level: 'LOW',
  }

  const moduleTabs = useMemo(
    () => [
      {
        id: 'crowd',
        label: 'Crowd Monitoring Module',
        shortLabel: 'Crowd Monitoring',
        icon: Users,
        accent: 'from-cyan-400 to-blue-500',
        description:
          'Live YOLO-based crowd intelligence with density, sudden formation, overcrowding, and stampede risk signals.',
      },
      {
        id: 'events',
        label: 'Event Analysis Module',
        shortLabel: 'Event Analysis',
        icon: ShieldAlert,
        accent: 'from-amber-400 to-rose-500',
        description:
          'Upload a video to run accident, violence, and weapon analysis with timestamped results.',
      },
    ],
    [],
  )

  const crowdHighlights = [
    'YOLO person detection',
    'Crowd density estimation',
    'Sudden crowd formation',
    'Overcrowding detection',
    'Stampede risk scoring',
  ]

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/data`)
        if (!response.ok) throw new Error('Failed to fetch data')

        const newData = await response.json()
        setData(newData)
        setApiError('')

        const alertMessage = newData.sudden_crowd_formation
          ? 'Sudden crowd detected.'
          : 'Crowd risk has escalated.'

        if (newData.status === 'ALERT') {
          normalStreakRef.current = 0
          if (!alertLatchedRef.current) {
            showAlertToast(alertMessage)
            alertLatchedRef.current = true
          }
        } else {
          normalStreakRef.current += 1
          if (normalStreakRef.current >= 3) {
            alertLatchedRef.current = false
          }
        }

        if (lastStatusRef.current && lastStatusRef.current !== newData.status && newData.status === 'ALERT' && !alertLatchedRef.current) {
          showAlertToast(alertMessage)
        }

        lastStatusRef.current = newData.status
        setIsLoading(false)
      } catch (error) {
        console.error('Error fetching data:', error)
        setApiError('Backend is not responding on port 5000')
        setIsLoading(false)
      }
    }

    fetchData()
    const interval = setInterval(fetchData, 1000)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    const fetchFrame = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/frame`)
        if (!response.ok) throw new Error('Failed to fetch frame')
        const frameResponse = await response.json()
        setFrameData(frameResponse.frame)
      } catch (error) {
        console.error('Error fetching frame:', error)
      }
    }

    fetchFrame()
    const interval = setInterval(fetchFrame, 500)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    const fetchEvents = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/events`)
        if (!response.ok) throw new Error('Failed to fetch events')
        const eventsResponse = await response.json()
        setEvents(eventsResponse.events)
      } catch (error) {
        console.error('Error fetching events:', error)
      }
    }

    fetchEvents()
    const interval = setInterval(fetchEvents, 2000)
    return () => clearInterval(interval)
  }, [])

  const showAlertToast = (message) => {
    setToastMessage(message)
    setToastType('alert')
    setShowToast(true)
  }

  const crowdMetricCards = [
    {
      title: 'People Count',
      value: safeData.count,
      icon: Circle,
      color: 'blue',
    },
    {
      title: 'Average',
      value: safeData.average,
      icon: TrendingUp,
      color: 'green',
    },
    {
      title: 'Density',
      value: safeData.density_index,
      icon: ShieldCheck,
      color: safeData.overcrowded ? 'red' : 'yellow',
    },
    {
      title: 'Risk Level',
      value: safeData.risk_level,
      icon: safeData.stampede_risk ? AlertTriangle : ShieldCheck,
      color: safeData.stampede_risk ? 'red' : 'green',
    },
  ]

  const showTopAlert = safeData.sudden_crowd_formation || safeData.stampede_risk || safeData.status === 'ALERT'

  const renderCrowdModule = () => (
    <div className="space-y-6">
      {apiError && (
        <div className="rounded-2xl border border-yellow-500/20 bg-yellow-500/10 px-4 py-3 text-sm text-yellow-100">
          {apiError}. The live camera panel still loads, but crowd metrics need the Flask API.
        </div>
      )}

      {showTopAlert && (
        <div className="rounded-[2rem] border border-red-500/40 bg-red-500/15 px-5 py-4 shadow-2xl shadow-red-500/20">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-[11px] uppercase tracking-[0.35em] text-red-200">Crowd alert</p>
              <h2 className="mt-2 text-2xl font-black tracking-tight text-red-100 sm:text-3xl">
                Sudden crowd detected
              </h2>
              <p className="mt-2 text-sm text-red-100/80">
                Live crowd risk is high. The feed is still running and the alert is being tracked in real time.
              </p>
            </div>
            <div className="flex h-12 w-12 items-center justify-center rounded-full border border-red-300/40 bg-red-500/20 text-red-100 text-2xl font-bold">
              !
            </div>
          </div>
        </div>
      )}

      <div className="grid gap-6 xl:grid-cols-[1.35fr_0.65fr]">
        <div className="rounded-[2rem] border border-white/10 bg-slate-950/60 p-3 shadow-2xl shadow-black/20 sm:p-4">
          <VideoPanel frameData={frameData} isLoading={isLoading} liveData={data} />
        </div>

        <div className="space-y-6 rounded-[2rem] border border-white/10 bg-slate-950/70 p-5 shadow-2xl shadow-black/20">
          <div>
            <p className="text-[11px] uppercase tracking-[0.28em] text-slate-400">Key metrics</p>
            <h3 className="mt-1 text-base font-semibold text-white">Crowd numbers at a glance</h3>
          </div>

          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-1 2xl:grid-cols-2">
            {crowdMetricCards.map((metric) => (
              <MetricCard
                key={metric.title}
                title={metric.title}
                value={metric.value}
                icon={metric.icon}
                color={metric.color}
              />
            ))}
          </div>

          <div className="rounded-2xl border border-white/10 bg-slate-950/60 p-3 shadow-inner shadow-black/20">
            <CrowdChart history={safeData.history || []} />
          </div>

        </div>
      </div>
    </div>
  )

  const renderLanding = () => (
    <section className="relative overflow-hidden rounded-[2.25rem] border border-white/10 bg-white/5 p-6 shadow-2xl shadow-black/30 backdrop-blur-2xl sm:p-8">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(34,211,238,0.14),transparent_34%),radial-gradient(circle_at_bottom_right,rgba(59,130,246,0.12),transparent_30%)]" />
      <div className="relative">
        <div className="flex flex-wrap items-center gap-3">
          <span className="inline-flex items-center gap-2 rounded-full border border-cyan-400/20 bg-cyan-400/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.24em] text-cyan-100">
            <Activity className="h-4 w-4" />
            AI Video Intelligence Platform
          </span>
          <span className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-medium text-slate-300">
            <ScanSearch className="h-4 w-4" />
            Crowd + event analysis workspace
          </span>
        </div>

        <div className="mt-8 max-w-3xl space-y-5">
          <p className="text-sm font-medium uppercase tracking-[0.4em] text-cyan-200/70">Welcome</p>
          <h1 className="text-4xl font-black tracking-tight text-white sm:text-5xl lg:text-6xl">
            AI System for Crowd Detection and Event Description in Public Spaces
          </h1>
          <p className="text-base leading-7 text-slate-300 sm:text-lg">
            Monitor people flow with live YOLO detections, crowd density estimation, sudden formation alerts,
            overcrowding warnings, and stampede risk scoring.
          </p>

          <div className="grid gap-4 pt-2 sm:grid-cols-2">
            <button
              type="button"
              onClick={() => setActiveModule('crowd')}
              className="group rounded-[1.5rem] border border-cyan-400/20 bg-cyan-400/10 p-5 text-left transition-all hover:border-cyan-300/40 hover:bg-cyan-400/15"
            >
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-xs uppercase tracking-[0.3em] text-cyan-100/70">Module 1</p>
                  <h2 className="mt-2 text-lg font-semibold text-white">Crowd Monitoring Module</h2>
                  <p className="mt-2 text-sm leading-6 text-slate-300">
                    Live video, counts, density, overcrowding, and stampede risk.
                  </p>
                </div>
                <ArrowRight className="mt-1 h-5 w-5 text-cyan-100 transition-transform group-hover:translate-x-1" />
              </div>
            </button>

            <button
              type="button"
              onClick={() => setActiveModule('events')}
              className="group rounded-[1.5rem] border border-amber-400/20 bg-amber-400/10 p-5 text-left transition-all hover:border-amber-300/40 hover:bg-amber-400/15"
            >
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-xs uppercase tracking-[0.3em] text-amber-100/70">Module 2</p>
                  <h2 className="mt-2 text-lg font-semibold text-white">Event Analysis Module</h2>
                  <p className="mt-2 text-sm leading-6 text-slate-300">
                    Upload a video, run accident, violence, and weapon models, then review incident type, confidence, timestamp, and location.
                  </p>
                </div>
                <ArrowRight className="mt-1 h-5 w-5 text-amber-100 transition-transform group-hover:translate-x-1" />
              </div>
            </button>
          </div>
        </div>
      </div>
    </section>
  )

  const activeModuleTab = moduleTabs.find((module) => module.id === activeModule)

  return (
    <div className="min-h-screen overflow-hidden bg-[#050816] text-white">
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute left-[-8rem] top-[-10rem] h-96 w-96 rounded-full bg-cyan-500/20 blur-3xl" />
        <div className="absolute right-[-7rem] top-24 h-[28rem] w-[28rem] rounded-full bg-fuchsia-500/10 blur-3xl" />
        <div className="absolute bottom-[-9rem] left-1/2 h-72 w-72 -translate-x-1/2 rounded-full bg-blue-500/10 blur-3xl" />
      </div>

      <main className="relative mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8 lg:py-8 overflow-y-auto">
        {activeModule === null ? (
          renderLanding()
        ) : (
          <>
            <section className="mb-4 flex items-center justify-between gap-3 rounded-[1.5rem] border border-white/10 bg-white/5 px-4 py-3 shadow-2xl shadow-black/20 backdrop-blur-2xl">
              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={() => setActiveModule(null)}
                  className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-white/10 bg-white/5 text-slate-200 hover:bg-white/10"
                  aria-label="Back to landing"
                >
                  <ChevronLeft className="h-4 w-4" />
                </button>
                <div>
                  <p className="text-[11px] uppercase tracking-[0.28em] text-slate-400">Workspace</p>
                  <h2 className="text-lg font-semibold text-white">{activeModuleTab?.label}</h2>
                </div>
              </div>

              <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[11px] font-medium text-slate-300">
                {activeModule === 'crowd' ? 'Crowd monitoring active' : 'Event analysis active'}
              </div>
            </section>

            {activeModule === 'crowd' ? renderCrowdModule() : <EventAnalysisPanel />}
          </>
        )}
      </main>

      {showToast && (
        <div className="fixed bottom-6 right-6 z-50">
          <Toast message={toastMessage} type={toastType} onClose={() => setShowToast(false)} />
        </div>
      )}
    </div>
  )
}
