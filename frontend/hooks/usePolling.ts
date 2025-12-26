import { useEffect, useRef, useState } from 'react'

interface UsePollingOptions {
  enabled?: boolean
  interval?: number
  onError?: (error: Error) => void
}

export function usePolling<T>(
  fetchFn: () => Promise<T>,
  options: UsePollingOptions = {}
) {
  const { enabled = true, interval = 3000, onError } = options
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<Error | null>(null)
  const intervalRef = useRef<NodeJS.Timeout | null>(null)
  const mountedRef = useRef(true)
  const fetchFnRef = useRef(fetchFn)

  // Update fetchFn ref when it changes
  useEffect(() => {
    fetchFnRef.current = fetchFn
  }, [fetchFn])

  const fetchData = async () => {
    try {
      const result = await fetchFnRef.current()
      if (mountedRef.current) {
        setData(result)
        setError(null)
        setLoading(false)
      }
    } catch (err) {
      if (mountedRef.current) {
        const error = err instanceof Error ? err : new Error('Polling error')
        setError(error)
        setLoading(false)
        onError?.(error)
      }
    }
  }

  useEffect(() => {
    mountedRef.current = true
    
    // Initial fetch
    if (enabled) {
      fetchData()
    }

    // Set up polling
    if (enabled && interval > 0) {
      intervalRef.current = setInterval(() => {
        fetchData()
      }, interval)
    }

    // Cleanup
    return () => {
      mountedRef.current = false
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
    }
  }, [enabled, interval])

  const stopPolling = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }
  }

  const startPolling = () => {
    if (!intervalRef.current && enabled && interval > 0) {
      intervalRef.current = setInterval(() => {
        fetchData()
      }, interval)
    }
  }

  return {
    data,
    loading,
    error,
    refetch: fetchData,
    stopPolling,
    startPolling,
  }
}

