'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import api from '@/lib/api'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

export default function NewApplicationPage() {
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [applicationId, setApplicationId] = useState<number | null>(null)

  const handleCreateApplication = async () => {
    setLoading(true)
    try {
      const response = await api.post('/api/kyc/applications')
      setApplicationId(response.data.id)
    } catch (error) {
      console.error('Failed to create application:', error)
      alert('Failed to create application')
    } finally {
      setLoading(false)
    }
  }

  if (applicationId) {
    router.push(`/dashboard/applications/${applicationId}`)
    return null
  }

  return (
    <div className="max-w-2xl mx-auto">
      <Card>
        <CardHeader>
          <CardTitle>New KYC Application</CardTitle>
          <CardDescription>Create a new KYC application to start the validation process</CardDescription>
        </CardHeader>
        <CardContent>
          <Button onClick={handleCreateApplication} disabled={loading} className="w-full">
            {loading ? 'Creating...' : 'Create Application'}
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}

