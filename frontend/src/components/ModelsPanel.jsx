import React, { useEffect, useRef, useState } from 'react'

const API_BASE_URL = 'http://localhost:5000'

export const ModelsPanel = () => {
  const fileInputRef = useRef(null)
  const [selectedImage, setSelectedImage] = useState(null)
  const [previewUrl, setPreviewUrl] = useState('')
  const [caption, setCaption] = useState('')
  const [captionError, setCaptionError] = useState('')
  const [isCaptioning, setIsCaptioning] = useState(false)
  const [modelName, setModelName] = useState('Salesforce/blip-image-captioning-large')

  const models = [
    {
      name: 'YOLOv8 Nano',
      type: 'Person Detection',
      status: 'Active',
      accuracy: '86%',
      icon: '🎯'
    },
    {
      name: 'Crowd Analyzer',
      type: 'Spike Detection',
      status: 'Active',
      accuracy: 'N/A',
      icon: '📈'
    }
  ]

  useEffect(() => {
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl)
      }
    }
  }, [previewUrl])

  const handleImageUpload = async (event) => {
    const file = event.target.files?.[0]
    if (!file) return

    setSelectedImage(file)
    setCaption('')
    setCaptionError('')
    setIsCaptioning(true)

    if (previewUrl) {
      URL.revokeObjectURL(previewUrl)
    }

    const nextPreviewUrl = URL.createObjectURL(file)
    setPreviewUrl(nextPreviewUrl)

    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('model', modelName)

      const response = await fetch(`${API_BASE_URL}/caption-image`, {
        method: 'POST',
        body: formData,
      })

      const payload = await response.json()

      if (!response.ok) {
        throw new Error(payload.error || 'Failed to generate caption')
      }

      setCaption(payload.caption || 'No caption returned')
    } catch (error) {
      setCaptionError(error.message || 'Failed to generate caption')
    } finally {
      setIsCaptioning(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white mb-2">🤖 ML Models</h2>
        <p className="text-sm text-gray-400">Upload an image and BLIP will generate a caption for it.</p>
      </div>

      <div className="rounded-2xl border border-blue-500/20 bg-gradient-to-br from-gray-900 to-gray-950 p-6 shadow-2xl shadow-black/20">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div className="space-y-2 max-w-2xl">
            <div className="inline-flex items-center rounded-full border border-blue-500/30 bg-blue-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-blue-200">
              BLIP Captioning
            </div>
            <h3 className="text-xl font-bold text-white">Image caption generator</h3>
            <p className="text-sm text-gray-300">
              Choose an image and get a caption from <span className="font-medium text-white">Salesforce/blip-image-captioning-large</span>.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              disabled={isCaptioning}
              className={`rounded-full px-4 py-2 text-sm font-semibold transition-colors ${
                isCaptioning ? 'cursor-not-allowed bg-blue-600/60 text-white/70' : 'bg-blue-600 text-white hover:bg-blue-500'
              }`}
            >
              {isCaptioning ? 'Captioning...' : 'Upload Image'}
            </button>
          </div>
        </div>

        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          className="hidden"
          onChange={handleImageUpload}
        />

        <div className="mt-6 grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="overflow-hidden rounded-2xl border border-gray-800 bg-black/40">
            <div className="flex items-center justify-between border-b border-gray-800 px-4 py-3 text-sm text-gray-400">
              <span>Selected image</span>
              <span>{selectedImage ? selectedImage.name : 'No file chosen'}</span>
            </div>
            <div className="flex min-h-[280px] items-center justify-center bg-gradient-to-br from-gray-950 to-black p-4">
              {previewUrl ? (
                <img src={previewUrl} alt="Selected for captioning" className="max-h-[420px] w-full rounded-xl object-contain" />
              ) : (
                <div className="text-center text-gray-500">
                  <p className="text-lg">Drop in an image to generate a caption</p>
                  <p className="mt-2 text-sm">PNG, JPG, WebP, BMP, or GIF</p>
                </div>
              )}
            </div>
          </div>

          <div className="space-y-4 rounded-2xl border border-gray-800 bg-gray-900 p-5">
            <label className="block space-y-2">
              <span className="text-sm font-medium text-gray-300">Model ID</span>
              <input
                type="text"
                value={modelName}
                onChange={(event) => setModelName(event.target.value)}
                className="w-full rounded-xl border border-gray-700 bg-gray-950 px-4 py-3 text-sm text-white outline-none transition-colors focus:border-blue-500"
              />
            </label>

            <div className="rounded-xl border border-gray-800 bg-gray-950 p-4">
              <p className="text-xs uppercase tracking-[0.2em] text-gray-500">Caption</p>
              <div className="mt-3 min-h-[120px] text-sm leading-6 text-gray-200">
                {caption && <p>{caption}</p>}
                {!caption && !captionError && !isCaptioning && <p className="text-gray-500">Upload an image to see the generated caption.</p>}
                {isCaptioning && <p className="text-blue-300">Generating caption...</p>}
                {captionError && <p className="text-red-300">{captionError}</p>}
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div className="grid gap-4">
        {models.map((model, idx) => (
          <div key={idx} className="bg-gray-800 border border-gray-700 rounded-lg p-6 hover:shadow-lg transition-shadow">
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-3">
                <span className="text-4xl">{model.icon}</span>
                <div>
                  <h3 className="text-xl font-bold text-white">{model.name}</h3>
                  <p className="text-gray-400 text-sm">{model.type}</p>
                </div>
              </div>
              <span className="bg-green-600 text-white px-3 py-1 rounded-full text-sm font-medium">
                {model.status}
              </span>
            </div>
            
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-gray-400">Accuracy:</span>
                <span className="text-white font-semibold">{model.accuracy}</span>
              </div>
              <div className="bg-gray-900 rounded h-2 overflow-hidden">
                <div className="bg-blue-600 h-full" style={{ width: model.accuracy === 'N/A' ? '0%' : model.accuracy }}></div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
