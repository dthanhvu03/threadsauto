/**
 * Global video playback manager.
 * 
 * Ensures only one video plays at a time.
 * Pauses videos when leaving viewport.
 */

import { ref, onUnmounted } from 'vue'

// Global state (shared across all components)
const playingVideoId = ref(null)
const registeredVideos = new Map()

/**
 * Video manager composable.
 * 
 * Provides methods to manage video playback:
 * - Only one video plays at a time
 * - Pause videos when leaving viewport
 * - Register/unregister video elements
 * 
 * @returns {Object} Video manager methods
 */
export function useVideoManager() {
  /**
   * Play a video and pause all others.
   * 
   * @param {string} videoId - Unique video identifier
   * @param {HTMLVideoElement} videoElement - Video element to play
   */
  const playVideo = (videoId, videoElement) => {
    if (!videoElement) {
      console.warn('[useVideoManager] playVideo: No video element provided')
      return
    }

    // Pause currently playing video
    if (playingVideoId.value && playingVideoId.value !== videoId) {
      const currentVideo = registeredVideos.get(playingVideoId.value)
      if (currentVideo && currentVideo.paused === false) {
        currentVideo.pause()
      }
    }

    // Play new video
    playingVideoId.value = videoId
    videoElement.play().catch((error) => {
      console.warn('[useVideoManager] playVideo: Failed to play video', error)
      playingVideoId.value = null
    })
  }

  /**
   * Pause all videos.
   */
  const pauseAll = () => {
    registeredVideos.forEach((videoElement) => {
      if (videoElement && !videoElement.paused) {
        videoElement.pause()
      }
    })
    playingVideoId.value = null
  }

  /**
   * Register a video element.
   * 
   * @param {string} videoId - Unique video identifier
   * @param {HTMLVideoElement} videoElement - Video element
   */
  const registerVideo = (videoId, videoElement) => {
    if (!videoElement) {
      console.warn('[useVideoManager] registerVideo: No video element provided')
      return
    }

    registeredVideos.set(videoId, videoElement)

    // Listen for pause events to update state
    const handlePause = () => {
      if (playingVideoId.value === videoId) {
        playingVideoId.value = null
      }
    }

    const handleEnded = () => {
      if (playingVideoId.value === videoId) {
        playingVideoId.value = null
      }
    }

    videoElement.addEventListener('pause', handlePause)
    videoElement.addEventListener('ended', handleEnded)

    // Store cleanup function
    videoElement._videoManagerCleanup = () => {
      videoElement.removeEventListener('pause', handlePause)
      videoElement.removeEventListener('ended', handleEnded)
    }
  }

  /**
   * Unregister a video element.
   * 
   * @param {string} videoId - Unique video identifier
   */
  const unregisterVideo = (videoId) => {
    const videoElement = registeredVideos.get(videoId)
    if (videoElement) {
      // Cleanup event listeners
      if (videoElement._videoManagerCleanup) {
        videoElement._videoManagerCleanup()
        delete videoElement._videoManagerCleanup
      }

      // Pause if currently playing
      if (playingVideoId.value === videoId) {
        videoElement.pause()
        playingVideoId.value = null
      }

      registeredVideos.delete(videoId)
    }
  }

  /**
   * Check if a video is currently playing.
   * 
   * @param {string} videoId - Video identifier
   * @returns {boolean} True if video is playing
   */
  const isPlaying = (videoId) => {
    return playingVideoId.value === videoId
  }

  /**
   * Get currently playing video ID.
   * 
   * @returns {string|null} Currently playing video ID
   */
  const getPlayingVideoId = () => {
    return playingVideoId.value
  }

  // Cleanup on unmount
  onUnmounted(() => {
    // Note: We don't cleanup all videos here because this is a global manager
    // Individual components should unregister their videos
  })

  return {
    playVideo,
    pauseAll,
    registerVideo,
    unregisterVideo,
    isPlaying,
    getPlayingVideoId
  }
}
