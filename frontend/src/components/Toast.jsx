import React, { useEffect } from 'react'

export const Toast = ({ message, type = 'info', onClose }) => {
  useEffect(() => {
    const timer = setTimeout(onClose, 5000)
    return () => clearTimeout(timer)
  }, [message, type, onClose])

  const bgColor = type === 'alert' ? 'bg-red-600' : 'bg-green-600'
  const icon = type === 'alert' ? '⚠️' : '✓'

  return (
    <div className={`${bgColor} text-white px-6 py-4 rounded-lg shadow-lg flex items-center gap-3 animate-pulse`}>
      <span className="text-2xl">{icon}</span>
      <span className="font-semibold">{message}</span>
    </div>
  )
}
