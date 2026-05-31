/**
 * Voice Alert Utility
 * Provides clear, nice voice notifications for system alerts
 */

export const playVoiceAlert = (message, options = {}) => {
  const {
    rate = 1,
    pitch = 1,
    volume = 1,
    voice = null,
  } = options

  // Check if browser supports Web Speech API
  const SpeechSynthesisUtterance = window.SpeechSynthesisUtterance
  if (!SpeechSynthesisUtterance) {
    console.warn('Speech Synthesis API not supported in this browser')
    return
  }

  // Cancel any ongoing speech
  window.speechSynthesis.cancel()

  const utterance = new SpeechSynthesisUtterance(message)

  // Set voice properties
  utterance.rate = rate
  utterance.pitch = pitch
  utterance.volume = volume

  // Select a nice, clear voice if available
  if (voice === null) {
    const voices = window.speechSynthesis.getVoices()
    // Prefer female voices as they tend to be clearer
    const preferredVoice = voices.find(
      v => v.lang.includes('en') && v.name.includes('Female')
    ) || voices.find(v => v.lang.includes('en')) || voices[0]

    if (preferredVoice) {
      utterance.voice = preferredVoice
    }
  } else {
    utterance.voice = voice
  }

  // Event handlers
  utterance.onstart = () => {
    console.log('Voice alert started:', message)
  }

  utterance.onend = () => {
    console.log('Voice alert completed')
  }

  utterance.onerror = (event) => {
    console.error('Voice alert error:', event.error)
  }

  // Speak the message
  window.speechSynthesis.speak(utterance)
}

/**
 * Play alert sound (beep pattern)
 */
export const playAlertSound = (count = 3) => {
  const audioContext = new (window.AudioContext || window.webkitAudioContext)()
  const now = audioContext.currentTime

  for (let i = 0; i < count; i++) {
    const oscillator = audioContext.createOscillator()
    const gainNode = audioContext.createGain()

    oscillator.connect(gainNode)
    gainNode.connect(audioContext.destination)

    oscillator.frequency.value = 800
    oscillator.type = 'sine'

    gainNode.gain.setValueAtTime(0.3, now + i * 0.3)
    gainNode.gain.exponentialRampToValueAtTime(0.01, now + i * 0.3 + 0.1)

    oscillator.start(now + i * 0.3)
    oscillator.stop(now + i * 0.3 + 0.1)
  }
}

/**
 * Combined alert: beep + voice
 */
export const triggerFullAlert = (message, options = {}) => {
  playAlertSound(2)
  setTimeout(() => {
    playVoiceAlert(message, options)
  }, 300)
}

export default {
  playVoiceAlert,
  playAlertSound,
  triggerFullAlert,
}
