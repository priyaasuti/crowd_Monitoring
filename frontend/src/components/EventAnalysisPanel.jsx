import React, { useEffect, useRef, useState } from 'react'
import { AlertTriangle, Camera, Clock3, FileVideo2, MapPin, ScanFace, ShieldAlert, Siren, Upload, Waves } from 'lucide-react'

const API_BASE_URL = 'http://localhost:5000'

const emptyResult = {
  incident_type: 'No Incident',
  confidence_score: 0,
  timestamp: '--:--',
  location: 'Unknown',
  analysis_timestamp: '',
  video: null,
  models: null,
  scene_description: '',
  scene_frame: null,
}

const modelCards = [
  {
    title: 'Accident detection',
    description: 'Runs the accident LSTM head on shared MobileNetV2 features.',
    icon: AlertTriangle,
    accent: 'from-amber-400/20 to-orange-500/10',
  },
  {
    title: 'Violence detection',
    description: 'Runs the violence LSTM head on the same extracted feature stream.',
    icon: Siren,
    accent: 'from-rose-400/20 to-red-500/10',
  },
  {
    title: 'Shared features',
    description: 'Frames are sampled once, encoded once, and reused for both models.',
    icon: Waves,
    accent: 'from-cyan-400/20 to-blue-500/10',
  },
]

function formatPercent(score) {
  if (typeof score !== 'number') return '--'
  return `${Math.round(score * 100)}%`
}

export const EventAnalysisPanel = () => {
  const fileInputRef = useRef(null)
  const [selectedFile, setSelectedFile] = useState(null)
  const [previewUrl, setPreviewUrl] = useState('')
  const [result, setResult] = useState(emptyResult)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [sceneStatus, setSceneStatus] = useState('idle')
  const [sceneJobId, setSceneJobId] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl)
      }
    }
  }, [previewUrl])

  useEffect(() => {
    if (!sceneJobId || sceneStatus !== 'pending') return undefined

    let cancelled = false

    const pollSceneDescription = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/analysis-jobs/${sceneJobId}`)
        const payload = await response.json()

        if (cancelled) return

        if (response.ok) {
          if (payload.scene_description) {
            setResult((previous) => ({
              ...previous,
              scene_description: payload.scene_description,
            }))
          }

          if (payload.scene_status === 'ready') {
            setSceneStatus('ready')
            return
          }

          if (payload.scene_status === 'error') {
            setSceneStatus('error')
            setError(payload.error || 'Failed to generate the scene description')
            return
          }
        }
      } catch (pollError) {
        if (!cancelled) {
          setSceneStatus('error')
          setError(pollError.message || 'Failed to fetch the scene description')
        }
      }
    }

    const intervalId = setInterval(pollSceneDescription, 2500)
    pollSceneDescription()

    return () => {
      cancelled = true
      clearInterval(intervalId)
    }
  }, [sceneJobId, sceneStatus])

  const handleUpload = async (event) => {
    const file = event.target.files?.[0]
    if (!file) return

    setSelectedFile(file)
    setIsAnalyzing(true)
    setSceneStatus('idle')
    setSceneJobId('')
    setError('')
    setResult(emptyResult)

    if (previewUrl) {
      URL.revokeObjectURL(previewUrl)
    }
    setPreviewUrl(URL.createObjectURL(file))

    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('system_location', 'Local monitoring workstation')

      const response = await fetch(`${API_BASE_URL}/analyze-event-video`, {
        method: 'POST',
        body: formData,
      })

      const payload = await response.json()
      if (!response.ok) {
        throw new Error(payload.error || 'Failed to analyze the uploaded video')
      }

      setResult(payload)
      setSceneJobId(payload.analysis_job_id || '')
      setSceneStatus(payload.scene_status || (payload.scene_description ? 'ready' : 'idle'))
    } catch (uploadError) {
      setError(uploadError.message || 'Failed to analyze the uploaded video')
    } finally {
      setIsAnalyzing(false)
    }
  }

  const video = result.video || {}
  const violence = result.models?.violence || {}
  const accident = result.models?.accident || {}

  return (
    <div className="space-y-6">
      <div className="rounded-[2rem] border border-amber-500/15 bg-gradient-to-br from-slate-950 via-slate-950 to-amber-950/30 p-6 shadow-2xl shadow-black/20 sm:p-8">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <span className="inline-flex items-center gap-2 rounded-full border border-amber-400/20 bg-amber-400/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.24em] text-amber-100">
              <ScanFace className="h-4 w-4" />
              Event Analysis
            </span>
            <h3 className="mt-3 text-2xl font-semibold tracking-tight text-white">
              Upload video and detect incidents
            </h3>
          </div>

          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={isAnalyzing}
            className={`inline-flex items-center gap-2 rounded-full px-5 py-2 text-sm font-medium transition-colors ${
              isAnalyzing ? 'cursor-not-allowed bg-amber-500/40 text-white/70' : 'bg-amber-400 text-slate-950 hover:bg-amber-300'
            }`}
          >
            <Upload className="h-4 w-4" />
            {isAnalyzing ? 'AI is analyzing...' : 'Upload video'}
          </button>

          <input ref={fileInputRef} type="file" accept="video/*" className="hidden" onChange={handleUpload} />
        </div>
      </div>

      <div className="grid gap-6 xl:grid-cols-[0.92fr_1.08fr]">
        <div className="rounded-[1.75rem] border border-white/10 bg-slate-950/70 p-5 shadow-2xl shadow-black/20">
          <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Upload status</p>
          <div className="mt-4 rounded-2xl border border-white/10 bg-white/5 p-4">
            <p className="text-sm text-slate-300">Selected file</p>
            <p className="mt-1 text-base font-medium text-white">{selectedFile ? selectedFile.name : 'No file selected'}</p>
          </div>

          <div className="mt-4 overflow-hidden rounded-2xl border border-white/10 bg-black/40">
            <div className="border-b border-white/10 px-4 py-3 text-xs uppercase tracking-[0.2em] text-slate-400">
              Preview
            </div>
            <div className="flex min-h-[220px] items-center justify-center bg-black">
              {previewUrl ? (
                <video src={previewUrl} controls className="h-full w-full object-contain" />
              ) : (
                <p className="px-6 text-center text-sm text-slate-400">
                  Upload a video to preview
                </p>
              )}
            </div>
          </div>

          {error && (
            <div className="mt-4 rounded-2xl border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-100">
              {error}
            </div>
          )}
        </div>

        <div className="rounded-[1.75rem] border border-white/10 bg-slate-950/70 p-5 shadow-2xl shadow-black/20">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-xs uppercase tracking-[0.3em] text-slate-400">Analysis result</p>
              <h3 className="mt-1 text-xl font-semibold text-white">Incident summary</h3>
            </div>
            <div className="inline-flex items-center gap-2 rounded-full border border-amber-400/20 bg-amber-400/10 px-3 py-1 text-xs font-medium text-amber-100">
              <ShieldAlert className="h-3.5 w-3.5" />
              {sceneStatus === 'pending'
                ? 'Detection complete, generating scene description'
                : sceneStatus === 'error'
                  ? 'Scene description failed'
                  : 'Ready'}
            </div>
          </div>

          {sceneStatus === 'pending' && (
            <div className="mt-4 rounded-2xl border border-amber-500/20 bg-amber-500/10 p-4 text-sm text-amber-50">
              Detection results are ready. Scene description is being generated in the background, and it will appear below as soon as it completes.
            </div>
          )}

          {sceneStatus === 'ready' && result.scene_description && (
            <div className="mt-4 rounded-2xl border border-emerald-500/20 bg-emerald-500/10 p-4 text-sm text-emerald-50">
              Scene description is ready.
            </div>
          )}

          <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
            <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
              <p className="text-[11px] uppercase tracking-[0.18em] text-slate-400">Incident type</p>
              <p className="mt-2 text-lg font-semibold text-white">{result.incident_type}</p>
            </div>
            <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
              <p className="text-[11px] uppercase tracking-[0.18em] text-slate-400">Confidence score</p>
              <p className="mt-2 text-lg font-semibold text-white">{formatPercent(result.confidence_score)}</p>
            </div>
            <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
              <p className="text-[11px] uppercase tracking-[0.18em] text-slate-400">Timestamp</p>
              <p className="mt-2 text-lg font-semibold text-white">{result.timestamp}</p>
            </div>
          </div>

          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
              <div className="flex items-center gap-2 text-slate-300">
                <MapPin className="h-4 w-4 text-cyan-200" />
                <p className="text-[11px] uppercase tracking-[0.18em]">System location</p>
              </div>
              <p className="mt-2 text-sm text-white">{result.location || video.system_location || 'Unknown'}</p>
            </div>
            <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
              <div className="flex items-center gap-2 text-slate-300">
                <Clock3 className="h-4 w-4 text-amber-200" />
                <p className="text-[11px] uppercase tracking-[0.18em]">Analysis time</p>
              </div>
              <p className="mt-2 text-sm text-white">{result.analysis_timestamp || '--'}</p>
            </div>
          </div>

          <div className="mt-4 rounded-2xl border border-cyan-500/20 bg-cyan-500/8 p-4 text-sm text-cyan-50/90">
            {video.camera_captured ? 'Camera source confirmed' : 'Uploaded video processed'}
          </div>

          <div className="mt-4 grid gap-3 lg:grid-cols-2">
            <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
              <p className="text-[11px] uppercase tracking-[0.18em] text-slate-400">Violence model</p>
              <p className="mt-2 text-lg font-semibold text-white">{violence.detected ? 'Violence detected' : 'No violence detected'}</p>
              <p className="mt-1 text-sm text-slate-300">Confidence: {formatPercent(violence.confidence)}</p>
              <p className="mt-1 text-sm text-slate-300">Timestamp: {violence.timestamp || '--:--'}</p>
            </div>
            <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
              <p className="text-[11px] uppercase tracking-[0.18em] text-slate-400">Accident model</p>
              <p className="mt-2 text-lg font-semibold text-white">{accident.detected ? 'Accident detected' : 'No accident detected'}</p>
              <p className="mt-1 text-sm text-slate-300">Confidence: {formatPercent(accident.confidence)}</p>
              <p className="mt-1 text-sm text-slate-300">Timestamp: {accident.timestamp || '--:--'}</p>
            </div>
          </div>

          {result.scene_description && (
            <div className="mt-6 rounded-2xl border border-cyan-500/20 bg-cyan-500/8 p-4 text-sm text-cyan-100">
              <p className="text-[11px] uppercase tracking-[0.18em] text-cyan-200">Scene description</p>
              <p className="mt-3 whitespace-pre-line text-sm leading-6 text-slate-100">{result.scene_description}</p>
            </div>
          )}

          {result.scene_frame && (
            <div className="mt-6 rounded-2xl border border-white/10 bg-slate-950/80 p-4">
              <p className="text-[11px] uppercase tracking-[0.18em] text-slate-400">Captured frame</p>
              <img
                src={`data:image/jpeg;base64,${result.scene_frame}`}
                alt="Scene frame"
                className="mt-3 h-auto w-full rounded-2xl object-contain"
              />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
