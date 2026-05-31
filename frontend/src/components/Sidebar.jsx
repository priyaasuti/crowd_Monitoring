import React from 'react'

export const Sidebar = ({ activeTab, setActiveTab }) => {
  const tabs = [
    { id: 'dashboard', label: 'Dashboard', icon: '📊' },
    { id: 'models', label: 'ML Models', icon: '🤖' },
    { id: 'settings', label: 'Settings', icon: '⚙️' },
  ]

  return (
    <div className="bg-gray-900 border-r border-gray-700 p-4 space-y-2">
      <h2 className="text-2xl font-bold text-white mb-8 flex items-center gap-2">
        👥 Crowd Monitor
      </h2>
      
      {tabs.map(tab => (
        <button
          key={tab.id}
          onClick={() => setActiveTab(tab.id)}
          className={`w-full text-left px-4 py-3 rounded-lg transition-colors flex items-center gap-3 ${
            activeTab === tab.id
              ? 'bg-blue-600 text-white'
              : 'text-gray-300 hover:bg-gray-800'
          }`}
        >
          <span className="text-xl">{tab.icon}</span>
          {tab.label}
        </button>
      ))}
    </div>
  )
}
